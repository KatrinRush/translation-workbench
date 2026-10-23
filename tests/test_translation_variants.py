import contextlib
import io
import json
import re
import sqlite3
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from cryptography.fernet import Fernet

from backend.integrations.base import ConnectionTestResult, IntegrationProvider, ProviderDescriptor, TranslationResult
from backend.integrations.credentials import CredentialVault
from backend.integrations.providers.claude import ClaudeProvider
from backend.integrations.providers.gemini import GeminiProvider
from backend.integrations.providers.openai import OpenAIProvider
from backend.integrations.registry import ProviderRegistry
from backend.integrations.service import IntegrationService, IntegrationServiceError
from backend.server import validate_project_ai_configuration
from backend.storage import Storage
from backend.translations.service import TranslationService

MARK = ""


def chunk_ids_and_text(message, label):
    root = ET.fromstring(re.search(r"<chunk>.*</chunk>|<chunk />", message, re.S).group(0))
    for element in root.findall("p"):
        for child in list(element):
            element.remove(child)
        element.text = f"{label} {element.attrib['id']}"
    return ET.tostring(root, encoding="unicode")


class FakeDeepL(IntegrationProvider):
    @property
    def descriptor(self):
        return ProviderDescriptor("deepl", "DeepL", "", ())

    def validate_credentials(self, credentials):
        return dict(credentials)

    def test_connection(self, credentials):
        return ConnectionTestResult("connected", "ok", "ok")

    def translate(self, credentials, request):
        root = ET.fromstring(request.text)
        for element in root.findall(".//p"):
            element.text = f"DeepL {element.attrib['id']}"
        return TranslationResult(ET.tostring(root, encoding="unicode"), "EN")


class EngineTransport:
    """Mock HTTP for Claude, OpenAI and Gemini: answers each in its own wire format."""

    def __init__(self):
        self.calls = []

    def post(self, url, headers, body, timeout):
        payload = json.loads(body)
        self.calls.append({"url": url, "body": payload})
        if "anthropic" in url:
            text = chunk_ids_and_text(payload["messages"][0]["content"], "Claude")
            reply = {"model": payload["model"], "stop_reason": "end_turn", "content": [{"type": "text", "text": text}],
                     "usage": {"input_tokens": 10, "output_tokens": 5}}
        elif "openai" in url:
            text = chunk_ids_and_text(payload["input"], "GPT")
            reply = {"model": payload["model"], "status": "completed",
                     "output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}],
                     "usage": {"input_tokens": 12, "output_tokens": 6}}
        else:
            text = chunk_ids_and_text(payload["contents"][0]["parts"][0]["text"], "Gemini")
            reply = {"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": "STOP"}],
                     "usageMetadata": {"promptTokenCount": 9, "candidatesTokenCount": 4}}
        return 200, json.dumps(reply, ensure_ascii=False).encode("utf-8")


class VariantFixture(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "workbench.sqlite3"
        self.storage = Storage(self.database_path)
        self.vault = CredentialVault(Fernet(Fernet.generate_key()))
        self.transport = EngineTransport()
        self.service = TranslationService(self.storage, self.vault, ProviderRegistry([
            FakeDeepL(), ClaudeProvider(self.transport), OpenAIProvider(self.transport), GeminiProvider(self.transport),
        ]))
        self.connections = {provider: self._connection(provider) for provider in ("deepl", "claude", "openai", "gemini")}
        self.project_id = self.storage.create_project({"title": "Engines", "status": "translation"})["projectId"]
        self.storage.save_book_structure(
            self.project_id, "book.epub", "application/epub+zip", b"book",
            {"chapters": [{"title": "One", "elements": [
                {"type": "paragraph", "text": "First."},
                {"type": "paragraph", "text": "Second."},
            ]}]},
        )
        chapter = self.storage.get_book_structure(self.project_id)["chapters"][0]
        self.chapter_id = chapter["chapterId"]
        self.ids = [element["paragraphId"] for element in chapter["elements"]]

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _connection(self, provider_id):
        connection = self.storage.create_integration_connection(provider_id, provider_id, self.vault.encrypt({"apiKey": f"{provider_id}-key"}))
        self.storage.update_integration_connection_status(connection["connectionId"], "connected", "ok", "ok", {})
        return connection

    def use_engine(self, provider_id, **models):
        configuration = {"translationConnectionId": self.connections[provider_id]["connectionId"]}
        if models:
            configuration["translationModels"] = models
        self.storage.update_project(self.project_id, {"aiConfiguration": configuration})

    def translate_chapter(self):
        """All batches of the chapter (LLM engines answer one batch per call)."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = self.service.translate_chapter(self.project_id, self.chapter_id, {"batchIndex": 0})
            for batch_index in range(1, result.get("totalBatches") or 1):
                self.service.translate_chapter(self.project_id, self.chapter_id, {"batchIndex": batch_index})
        return output.getvalue()

    def variants(self, paragraph_id, engine=None):
        items = self.storage.get_paragraph(paragraph_id)["translationVariants"]
        return [item for item in items if engine is None or item["engine"] == engine]

    def add_footnote(self, paragraph_id, footnote_id="fn1"):
        with self.storage.connection() as connection:
            connection.execute(
                "INSERT INTO paragraph_footnotes(footnote_id, paragraph_id, note_text, created_at) VALUES (?, ?, ?, ?)",
                (footnote_id, paragraph_id, "Примітка", "2026-01-01"),
            )

    def footnote_ids(self, paragraph_id):
        with self.storage.connection() as connection:
            return [row["footnote_id"] for row in connection.execute(
                "SELECT footnote_id FROM paragraph_footnotes WHERE paragraph_id = ?", (paragraph_id,)
            ).fetchall()]


class MigrationTests(VariantFixture):
    def test_existing_translation_becomes_the_chosen_current_variant_once(self):
        self.storage.update_paragraph(self.ids[0], "Старий переклад", True)
        # Simulate a database created before variants existed.
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("DROP TABLE paragraph_translation_variants")
            connection.execute("ALTER TABLE book_paragraphs DROP COLUMN selected_variant_id")

        storage = Storage(self.database_path)
        Storage(self.database_path)  # a second start must not duplicate anything

        paragraph = storage.get_paragraph(self.ids[0])
        self.assertEqual(1, len(paragraph["translationVariants"]))
        current = paragraph["translationVariants"][0]
        self.assertEqual(("current", "Старий переклад"), (current["engine"], current["text"]))
        self.assertEqual(current["variantId"], paragraph["selectedVariantId"])
        self.assertEqual("Старий переклад", paragraph["translationText"])
        self.assertTrue(paragraph["reviewed"])
        self.assertEqual([], storage.get_paragraph(self.ids[1])["translationVariants"])

    def test_structure_exposes_variants_and_selection(self):
        self.storage.add_translation_variant(self.ids[0], "claude", "Claude текст", "claude-x")

        element = self.storage.get_book_structure(self.project_id)["chapters"][0]["elements"][0]

        self.assertEqual("Claude текст", element["translationText"])
        self.assertEqual(element["translationVariants"][0]["variantId"], element["selectedVariantId"])
        self.assertEqual("claude-x", element["translationVariants"][0]["model"])


class EngineRunTests(VariantFixture):
    def test_first_variant_is_chosen_and_later_engines_never_overwrite_the_chosen_text(self):
        self.use_engine("deepl")
        self.translate_chapter()
        self.assertEqual(f"DeepL {self.ids[0]}", self.storage.get_paragraph(self.ids[0])["translationText"])

        for engine, label in (("claude", "Claude"), ("openai", "GPT"), ("gemini", "Gemini")):
            self.use_engine(engine)
            self.translate_chapter()
            paragraph = self.storage.get_paragraph(self.ids[0])
            self.assertEqual(f"DeepL {self.ids[0]}", paragraph["translationText"])
            self.assertEqual([f"{label} {self.ids[0]}"], [item["text"] for item in self.variants(self.ids[0], engine)])

        engines = sorted(item["engine"] for item in self.variants(self.ids[0]))
        self.assertEqual(["claude", "deepl", "gemini", "openai"], engines)

    def test_chosen_manual_edit_survives_an_engine_run(self):
        self.storage.save_paragraph_edit(self.ids[0], "Моя редакція", False)
        self.use_engine("openai")
        self.translate_chapter()
        self.assertEqual("Моя редакція", self.storage.get_paragraph(self.ids[0])["translationText"])
        self.assertEqual(1, len(self.variants(self.ids[0], "openai")))

    def test_text_without_a_chosen_variant_keeps_its_text_and_marks_when_an_engine_adds_a_version(self):
        # A text can stand with no chosen variant (a plain write that did not match the chosen one).
        # An engine run only adds a version there; the text, «Перевірено» and «Вичитано» stay.
        self.storage.update_paragraph(self.ids[0], "Моя редакція", True, proofread=True)
        self.assertIsNone(self.storage.get_paragraph(self.ids[0])["selectedVariantId"])
        self.use_engine("claude")

        with contextlib.redirect_stdout(io.StringIO()):
            result = self.service.translate_paragraph(self.ids[0], {})

        self.assertEqual("Моя редакція", result["translationText"])
        self.assertTrue(result["reviewed"])
        self.assertTrue(result["proofread"])
        self.assertIsNone(result["selectedVariantId"])
        self.assertEqual([f"Claude {self.ids[0]}"], [item["text"] for item in self.variants(self.ids[0], "claude")])

    def test_chapter_run_keeps_every_text_and_mark_and_only_fills_untranslated_paragraphs(self):
        self.storage.update_paragraph(self.ids[0], "Моя редакція", False)  # a text, nothing chosen, not marked
        self.use_engine("claude")

        self.translate_chapter()

        first, second = (self.storage.get_paragraph(item) for item in self.ids)
        self.assertEqual("Моя редакція", first["translationText"])
        self.assertEqual(1, len(self.variants(self.ids[0], "claude")))
        self.assertEqual(f"Claude {self.ids[1]}", second["translationText"])  # no translation yet: the engine's becomes the chosen one
        self.assertEqual(second["translationVariants"][0]["variantId"], second["selectedVariantId"])

    def test_queue_batch_over_a_translated_paragraph_adds_a_version_and_changes_nothing_else(self):
        self.storage.update_paragraph(self.ids[0], "Моя редакція", True, proofread=True)
        queue = self.storage.create_translation_queue(
            self.project_id, "claude", self.connections["claude"]["connectionId"], None, None, {}, None, None,
            [{"chapterId": self.chapter_id, "chapterIndex": 1, "title": "One", "plan": self.ids[:1],
              "batchesTotal": 1, "chars": 6}],
        )
        item = self.storage.get_translation_queue(queue["queueId"])["items"][0]

        summary = self.storage.save_queue_batch(
            queue["queueId"], item["itemId"], "claude", [{"paragraphId": self.ids[0], "text": "Від Claude"}]
        )

        paragraph = self.storage.get_paragraph(self.ids[0])
        self.assertEqual({"created": 1, "autoSelected": 0}, summary)
        self.assertEqual(("Моя редакція", True, True), (paragraph["translationText"], paragraph["reviewed"], paragraph["proofread"]))
        self.assertEqual(["Від Claude"], [variant["text"] for variant in self.variants(self.ids[0], "claude")])

    def test_reviewed_paragraphs_are_skipped_for_chapters_but_not_for_the_paragraph_button(self):
        self.storage.save_paragraph_edit(self.ids[0], "Вичитано", True)
        self.use_engine("gemini")

        self.translate_chapter()
        self.assertEqual([], self.variants(self.ids[0], "gemini"))
        self.assertEqual(1, len(self.variants(self.ids[1], "gemini")))

        with contextlib.redirect_stdout(io.StringIO()):
            result = self.service.translate_paragraph(self.ids[0], {})
        self.assertEqual(1, len(self.variants(self.ids[0], "gemini")))
        self.assertEqual("Вичитано", result["translationText"])
        self.assertTrue(result["reviewed"])  # chosen text unchanged, so the review stands

    def test_model_comes_from_translation_models_and_is_stored_on_the_variant(self):
        self.use_engine("gemini", gemini="gemini-project-model")
        self.translate_chapter()
        self.assertIn("/models/gemini-project-model:generateContent", self.transport.calls[0]["url"])

        self.use_engine("openai", openai="gpt-project-model")
        self.translate_chapter()
        openai_call = next(call for call in self.transport.calls if "openai" in call["url"])
        self.assertEqual("gpt-project-model", openai_call["body"]["model"])
        self.assertEqual("gpt-project-model", self.variants(self.ids[0], "openai")[0]["model"])

    def test_usage_and_prompt_lines_carry_the_provider_name(self):
        self.use_engine("openai")
        log = self.translate_chapter()
        self.assertIn("[OPENAI USAGE]", log)
        self.assertIn("[OPENAI PROMPT]", log)
        usage = json.loads(next(line for line in log.splitlines() if line.startswith("[OPENAI USAGE]")).removeprefix("[OPENAI USAGE] "))
        self.assertEqual((12, 6, "openai"), (usage["inputTokens"], usage["outputTokens"], usage["providerId"]))

        self.use_engine("gemini")
        self.assertIn("[GEMINI USAGE]", self.translate_chapter())

    def test_rerun_with_identical_text_adds_no_version(self):
        self.use_engine("claude")
        for _ in range(3):
            self.translate_chapter()
        # the fake engine answers the same text each time: still a single version
        self.assertEqual(1, len(self.variants(self.ids[0], "claude")))


class VersionTests(VariantFixture):
    def add(self, engine, text, paragraph_id=None):
        return self.storage.add_translation_variant(paragraph_id or self.ids[0], engine, text, f"{engine}-model")["translationVariants"]

    def texts(self, engine, paragraph_id=None):
        return [item["text"] for item in self.variants(paragraph_id or self.ids[0], engine)]

    def test_several_translations_of_one_engine_make_several_versions_oldest_first(self):
        for number in range(1, 4):
            self.add("claude", f"Claude {number}")
        self.assertEqual(["Claude 1", "Claude 2", "Claude 3"], self.texts("claude"))
        self.assertTrue(all(item["model"] == "claude-model" for item in self.variants(self.ids[0], "claude")))
        self.assertEqual([], self.texts("claude", self.ids[1]))  # other paragraphs and engines are separate

    def test_identical_text_to_the_newest_version_is_not_duplicated_but_an_older_text_is(self):
        self.add("claude", "A")
        self.add("claude", "B")
        payload = self.storage.add_translation_variant(self.ids[0], "claude", "B", "other-model")
        self.assertEqual(["A", "B"], self.texts("claude"))
        self.assertEqual(self.ids[0], payload["paragraphId"])
        self.add("claude", "A")  # equal to an older version only: a new version
        self.assertEqual(["A", "B", "A"], self.texts("claude"))

    def test_identical_text_is_deduplicated_per_engine(self):
        self.add("claude", "Same")
        self.add("openai", "Same")
        self.assertEqual(["Same"], self.texts("claude"))
        self.assertEqual(["Same"], self.texts("openai"))

    def test_only_the_newest_n_versions_are_kept(self):
        from backend import storage as storage_module
        self.assertEqual(10, storage_module.VARIANT_VERSIONS_KEPT)
        total = storage_module.VARIANT_VERSIONS_KEPT + 3
        self.add("deepl", "DeepL")  # the first variant is the chosen one and is exempt from the limit
        for number in range(1, total + 1):
            self.add("openai", f"GPT {number}")
        kept = self.texts("openai")
        self.assertEqual([f"GPT {number}" for number in range(4, total + 1)], kept)
        self.assertEqual(storage_module.VARIANT_VERSIONS_KEPT, len(kept))

    def test_the_selected_version_survives_beyond_n_and_the_limit_is_per_engine(self):
        from unittest.mock import patch
        from backend import storage as storage_module
        with patch.object(storage_module, "VARIANT_VERSIONS_KEPT", 3):
            first = self.add("claude", "Claude 1")[-1]  # the first variant becomes the chosen one
            self.assertEqual(first["variantId"], self.storage.get_paragraph(self.ids[0])["selectedVariantId"])
            for number in range(2, 8):
                self.add("claude", f"Claude {number}")
            self.add("gemini", "Gemini 1")
        self.assertEqual(["Claude 1", "Claude 5", "Claude 6", "Claude 7"], self.texts("claude"))
        self.assertEqual(["Gemini 1"], self.texts("gemini"))
        self.assertEqual("Claude 1", self.storage.get_paragraph(self.ids[0])["translationText"])

    def test_choosing_another_version_lets_the_old_selection_be_pruned_only_beyond_n(self):
        from unittest.mock import patch
        from backend import storage as storage_module
        with patch.object(storage_module, "VARIANT_VERSIONS_KEPT", 2):
            for number in range(1, 5):
                versions = self.add("claude", f"Claude {number}")
            self.assertEqual(["Claude 1", "Claude 3", "Claude 4"], [v["text"] for v in versions if v["engine"] == "claude"])
            newest = versions[-1]
            selected = self.storage.select_translation_variant(self.ids[0], newest["variantId"])
        self.assertEqual(["Claude 3", "Claude 4"], [v["text"] for v in selected["translationVariants"] if v["engine"] == "claude"])

    def test_undo_recreates_the_selected_version_that_was_pruned_after_the_choice(self):
        from unittest.mock import patch
        from backend import storage as storage_module
        with patch.object(storage_module, "VARIANT_VERSIONS_KEPT", 1):
            first = self.add("claude", "Claude 1")[-1]
            second = self.add("claude", "Claude 2")[-1]
            selected = self.storage.select_translation_variant(self.ids[0], second["variantId"])
            self.assertNotIn(first["variantId"], [item["variantId"] for item in selected["translationVariants"]])
            restored = self.storage.restore_translation_selection(self.ids[0], selected["previous"])
        self.assertEqual(first["variantId"], restored["selectedVariantId"])
        self.assertEqual("Claude 1", restored["translationText"])

    def test_manual_and_current_stay_a_single_row(self):
        self.storage.update_paragraph(self.ids[0], "Старий", False)
        self.storage = type(self.storage)(self.database_path)  # start-up migration makes «Поточний»
        for text in ("Правка 1", "Правка 2", "Правка 3"):
            self.storage.save_paragraph_edit(self.ids[0], text, False)
        self.assertEqual(["Правка 3"], self.texts("manual"))
        self.assertEqual(["Старий"], self.texts("current"))

    def test_warnings_belong_to_their_version(self):
        warning = [{"type": "glossary_missing", "source": "Lark", "target": "Ларк"}]
        self.storage.add_translation_variant(self.ids[0], "claude", "Версія 1", "m", warning)
        self.storage.add_translation_variant(self.ids[0], "claude", "Версія 2", "m", None)
        first, second = self.variants(self.ids[0], "claude")
        self.assertEqual(warning, first["warnings"])
        self.assertEqual([], second["warnings"])

    def test_reviewed_and_footnotes_rules_hold_for_a_chosen_older_version(self):
        self.add_footnote(self.ids[0])
        self.storage.update_paragraph(self.ids[0], f"Старий{MARK}fn1{MARK}", True)
        old = self.add("claude", "Claude 1")[-1]
        self.add("claude", "Claude 2")
        chosen = self.storage.select_translation_variant(self.ids[0], old["variantId"])
        self.assertEqual("Claude 1", chosen["translationText"].replace(MARK, "").replace("fn1", ""))
        self.assertFalse(chosen["reviewed"])
        self.assertEqual(["fn1"], self.footnote_ids(self.ids[0]))


class SelectionTests(VariantFixture):
    def test_selecting_copies_the_variant_and_clears_reviewed_only_when_text_changes(self):
        deepl = self.storage.add_translation_variant(self.ids[0], "deepl", "DeepL текст")["translationVariants"][0]
        claude = self.storage.add_translation_variant(self.ids[0], "claude", "Claude текст")["translationVariants"][1]
        self.storage.save_paragraph_edit(self.ids[0], "DeepL текст", True)  # proofread, same text

        same = self.storage.select_translation_variant(self.ids[0], deepl["variantId"])
        self.assertTrue(same["reviewed"])

        changed = self.storage.select_translation_variant(self.ids[0], claude["variantId"])
        self.assertEqual("Claude текст", changed["translationText"])
        self.assertEqual(claude["variantId"], changed["selectedVariantId"])
        self.assertFalse(changed["reviewed"])
        self.assertEqual(deepl["variantId"], changed["previous"]["selectedVariantId"])
        self.assertTrue(changed["previous"]["reviewed"])

    def test_footnote_markers_are_carried_to_the_end_and_no_footnote_is_deleted(self):
        self.storage.save_paragraph_edit(self.ids[0], f"Текст{MARK}fn1{MARK} далі", False)
        self.add_footnote(self.ids[0])
        variant = self.storage.add_translation_variant(self.ids[0], "claude", "Новий текст")["translationVariants"][-1]

        result = self.storage.select_translation_variant(self.ids[0], variant["variantId"])

        self.assertEqual(f"Новий текст{MARK}fn1{MARK}", result["translationText"])
        self.assertEqual(["fn1"], result["movedFootnoteIds"])
        self.assertEqual(["fn1"], self.footnote_ids(self.ids[0]))

    def test_undo_restores_selection_text_reviewed_and_footnotes_without_a_manual_variant(self):
        self.storage.save_paragraph_edit(self.ids[0], f"Ручний{MARK}fn1{MARK}", True)
        self.add_footnote(self.ids[0])
        variant = self.storage.add_translation_variant(self.ids[0], "gemini", "Gemini текст")["translationVariants"][-1]
        before = self.storage.get_paragraph(self.ids[0])

        selected = self.storage.select_translation_variant(self.ids[0], variant["variantId"])
        restored = self.storage.restore_translation_selection(self.ids[0], selected["previous"])

        self.assertEqual(before["selectedVariantId"], restored["selectedVariantId"])
        self.assertEqual(before["translationText"], restored["translationText"])
        self.assertTrue(restored["reviewed"])
        self.assertEqual(["fn1"], self.footnote_ids(self.ids[0]))
        self.assertEqual(1, len([item for item in restored["translationVariants"] if item["engine"] == "manual"]))
        self.assertEqual(f"Ручний{MARK}fn1{MARK}", self.variants(self.ids[0], "manual")[0]["text"])

    def test_only_a_real_text_change_is_recorded_as_manual(self):
        self.storage.add_translation_variant(self.ids[0], "deepl", "DeepL текст")

        unchanged = self.storage.save_paragraph_edit(self.ids[0], "DeepL текст", True)
        self.assertEqual([], [item for item in unchanged["translationVariants"] if item["engine"] == "manual"])

        edited = self.storage.save_paragraph_edit(self.ids[0], "Виправлено", False)
        manual = [item for item in edited["translationVariants"] if item["engine"] == "manual"]
        self.assertEqual(["Виправлено"], [item["text"] for item in manual])
        self.assertEqual(manual[0]["variantId"], edited["selectedVariantId"])

        again = self.storage.save_paragraph_edit(self.ids[0], "Виправлено ще", False)
        self.assertEqual(["Виправлено ще"], [item["text"] for item in again["translationVariants"] if item["engine"] == "manual"])

        cleared = self.storage.save_paragraph_edit(self.ids[0], None, False)
        self.assertIsNone(cleared["translationText"])

    def test_unknown_variant_is_rejected(self):
        with self.assertRaises(ValueError):
            self.storage.select_translation_variant(self.ids[0], "variant-missing")


class ModelListServiceTests(unittest.TestCase):
    class Provider(IntegrationProvider):
        def __init__(self, provider_id="claude", fail=False):
            self.provider_id = provider_id
            self.fail = fail
            self.calls = []

        @property
        def descriptor(self):
            return ProviderDescriptor(self.provider_id, self.provider_id, "", ())

        def validate_credentials(self, credentials):
            return dict(credentials)

        def test_connection(self, credentials):
            return ConnectionTestResult("connected", "ok", "ok")

        def translate(self, credentials, request):
            raise NotImplementedError

        def list_models(self, credentials):
            self.calls.append(credentials["apiKey"])
            if self.fail:
                raise ValueError("Claude відхилив API key.")
            return [{"id": "model-alpha", "displayName": "Alpha"}, {"id": "model-beta", "displayName": "Beta"}]

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")
        self.vault = CredentialVault(Fernet(Fernet.generate_key()))
        self.now = [1000.0]
        self.provider = self.Provider()
        self.service = IntegrationService(self.storage, self.vault, ProviderRegistry([self.provider, FakeDeepL()]), clock=lambda: self.now[0])
        self.connection = self.storage.create_integration_connection("claude", "Claude", self.vault.encrypt({"apiKey": "secret-key"}))

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_models_are_cached_briefly_and_filterable(self):
        first = self.service.list_models(self.connection["connectionId"])
        second = self.service.list_models(self.connection["connectionId"], "beta")

        self.assertEqual(["model-alpha", "model-beta"], [item["id"] for item in first["models"]])
        self.assertFalse(first["cached"])
        self.assertTrue(second["cached"])
        self.assertEqual(["model-beta"], [item["id"] for item in second["models"]])
        self.assertEqual(1, len(self.provider.calls))
        self.assertNotIn("secret-key", json.dumps(first))

        self.now[0] += IntegrationService.MODEL_LIST_TTL_SECONDS + 1
        self.service.list_models(self.connection["connectionId"])
        self.service.list_models(self.connection["connectionId"], refresh=True)
        self.assertEqual(3, len(self.provider.calls))

    def test_updating_the_connection_drops_the_cache(self):
        self.service.list_models(self.connection["connectionId"])
        self.service.update_connection(self.connection["connectionId"], {"credentials": {"apiKey": "new-key"}})
        self.service.list_models(self.connection["connectionId"])
        self.assertEqual(["secret-key", "new-key"], self.provider.calls)

    def test_errors_are_readable(self):
        self.provider.fail = True
        with self.assertRaises(IntegrationServiceError) as context:
            self.service.list_models(self.connection["connectionId"])
        self.assertEqual((502, "models_unavailable"), (context.exception.http_status, context.exception.code))
        self.assertIn("API key", str(context.exception))

        with self.assertRaises(IntegrationServiceError) as missing:
            self.service.list_models("connection-missing")
        self.assertEqual(404, missing.exception.http_status)

        deepl = self.storage.create_integration_connection("deepl", "DeepL", self.vault.encrypt({"apiKey": "k"}))
        with self.assertRaises(IntegrationServiceError) as unsupported:
            self.service.list_models(deepl["connectionId"])
        self.assertEqual("models_unsupported", unsupported.exception.code)

    def test_provider_list_names_default_translation_models(self):
        registry = ProviderRegistry([ClaudeProvider(), OpenAIProvider(), GeminiProvider(), FakeDeepL()])
        providers = {item["providerId"]: item for item in IntegrationService(self.storage, self.vault, registry).list_providers()["providers"]}
        self.assertEqual(OpenAIProvider.VERIFICATION_MODEL, providers["openai"]["defaultTranslationModel"])
        self.assertEqual(GeminiProvider.VERIFICATION_MODEL, providers["gemini"]["defaultTranslationModel"])
        self.assertIsNone(providers["deepl"]["defaultTranslationModel"])


class ProjectSettingsValidationTests(unittest.TestCase):
    def test_translation_models_are_validated(self):
        self.assertIsNone(validate_project_ai_configuration(
            {"aiConfiguration": {"translationModels": {"claude": None, "openai": "gpt-x", "gemini": "gemini-x"}}}, []
        ))
        self.assertIsNotNone(validate_project_ai_configuration({"aiConfiguration": {"translationModels": {"grok": "x"}}}, []))
        self.assertIsNotNone(validate_project_ai_configuration({"aiConfiguration": {"translationModels": {"openai": 5}}}, []))
        self.assertIsNotNone(validate_project_ai_configuration({"aiConfiguration": {"translationModels": "gpt-x"}}, []))


if __name__ == "__main__":
    unittest.main()
