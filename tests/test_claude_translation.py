import contextlib
import io
import json
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from cryptography.fernet import Fernet

from backend.integrations.base import (
    ConnectionTestResult,
    IntegrationProvider,
    ProviderDescriptor,
    TranslationRequest,
    TranslationResult,
)
from backend.integrations.credentials import CredentialVault
from backend.integrations.providers.claude import ClaudeProvider
from backend.integrations.registry import ProviderRegistry
from backend.storage import Storage
from backend.translations.llm_prompt import glossary_terms_in_text, select_glossary_entries
from backend.translations.service import TranslationService, TranslationServiceError


class FakeDeepLProvider(IntegrationProvider):
    def __init__(self):
        self.requests = []

    @property
    def descriptor(self):
        return ProviderDescriptor("deepl", "DeepL", "", ())

    def validate_credentials(self, credentials):
        return dict(credentials)

    def test_connection(self, credentials):
        return ConnectionTestResult("connected", "ok", "ok")

    def translate(self, credentials, request: TranslationRequest):
        self.requests.append(request)
        root = ET.fromstring(request.text)
        for element in root.findall(".//p"):
            element.text = "DeepL переклад"
        return TranslationResult(ET.tostring(root, encoding="unicode"), "EN")


def chunk_from_user_message(message: str) -> ET.Element:
    match = re.search(r"<chunk>.*</chunk>|<chunk />", message, re.S)
    return ET.fromstring(match.group(0))


def translate_everything(message: str) -> str:
    """A model that follows the glossary: the paragraph naming Harry gets "Гаррі"."""
    root = chunk_from_user_message(message)
    for element in root.findall(".//p"):
        source = "".join(element.itertext())
        for child in list(element):
            element.remove(child)
        element.text = f"Переклад {element.attrib['id']}" + (" Гаррі" if "Harry" in source else "")
    return "```xml\n" + ET.tostring(root, encoding="unicode") + "\n```"


def message_payload(text, stop_reason="end_turn", **extra):
    return {
        "id": "msg_test",
        "model": "claude-sonnet-5-5",
        "stop_reason": stop_reason,
        "content": [{"type": "thinking", "thinking": ""}, {"type": "text", "text": text}],
        "usage": {
            "input_tokens": 120,
            "output_tokens": 80,
            "cache_creation_input_tokens": 900,
            "cache_read_input_tokens": 0,
        },
        **extra,
    }


class ScriptedClaudeTransport:
    """Mock HTTP transport: each call is answered by `responder(request_body) -> (status, payload)`."""

    def __init__(self, responder=None):
        self.responder = responder or (lambda body: (200, message_payload(translate_everything(body["messages"][0]["content"]))))
        self.calls = []

    def post(self, url, headers, body, timeout):
        payload = json.loads(body)
        self.calls.append({"url": url, "headers": headers, "body": payload, "timeout": timeout})
        status, response = self.responder(payload)
        return status, json.dumps(response, ensure_ascii=False).encode("utf-8")

    def user_message(self, index=0):
        return self.calls[index]["body"]["messages"][0]["content"]

    def system_prompt(self, index=0):
        return self.calls[index]["body"]["system"][0]["text"]


class ClaudeTranslationServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")
        self.vault = CredentialVault(Fernet(Fernet.generate_key()))
        self.deepl = FakeDeepLProvider()
        self.transport = ScriptedClaudeTransport()
        self.service = TranslationService(
            self.storage, self.vault, ProviderRegistry([self.deepl, ClaudeProvider(self.transport)])
        )

        self.deepl_connection = self._connection("deepl", "deepl-key")
        self.claude_connection = self._connection("claude", "claude-key")

        harry = self.storage.create_glossary_entry({
            "source": "Harry", "target": "Гаррі", "characterGender": "masc",
            "speechRegister": "постійна лайка", "indeclinable": True,
        })
        mira = self.storage.create_glossary_entry({"source": "Mira", "target": "Міра", "characterGender": "femn"})
        wand = self.storage.create_glossary_entry({"source": "wand", "target": "чарівна паличка", "note": "не «жезл»"})
        rule = self.storage.create_rule({"text": "Звертання до старших — на «ви»."})

        self.project = self.storage.create_project({
            "title": "Claude book",
            "status": "translation",
            "narratorGender": "masc",
            "translationRules": "Не перекладай назви вулиць.",
            "projectGlossaryEntryIds": [harry["glossaryEntryId"], mira["glossaryEntryId"], wand["glossaryEntryId"]],
            "projectRuleIds": [rule["ruleId"]],
        })
        self.project_id = self.project["projectId"]
        long_text = "Long sentence about the rain over the river. " * 35  # > batch budget: one paragraph per batch
        self.storage.save_book_structure(
            self.project_id,
            "book.epub",
            "application/epub+zip",
            b"book",
            {"chapters": [
                {"title": "One", "elements": [
                    {"type": "paragraph", "text": "Earlier one."},
                    {"type": "paragraph", "text": "Earlier two."},
                    {"type": "paragraph", "text": "Earlier three."},
                    {"type": "paragraph", "text": "Earlier four."},
                ]},
                {"title": "Two", "elements": [
                    {"type": "paragraph", "text": '"Go," Harry said. "Now."'},
                    {"type": "paragraph", "text": long_text},
                    {"type": "paragraph", "text": long_text},
                ]},
            ]},
        )
        structure = self.storage.get_book_structure(self.project_id)
        self.chapter_one_ids = [element["paragraphId"] for element in structure["chapters"][0]["elements"]]
        self.chapter_id = structure["chapters"][1]["chapterId"]
        self.paragraph_ids = [element["paragraphId"] for element in structure["chapters"][1]["elements"]]

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _connection(self, provider_id, api_key, status="connected"):
        connection = self.storage.create_integration_connection(provider_id, provider_id, self.vault.encrypt({"apiKey": api_key}))
        self.storage.update_integration_connection_status(connection["connectionId"], status, "ok", "ok", {})
        return connection

    def _use_claude(self, **extra):
        self.storage.update_project(self.project_id, {
            "aiConfiguration": {"translationConnectionId": self.claude_connection["connectionId"], **extra},
        })

    def _translate_batch(self, batch_index):
        with contextlib.redirect_stdout(io.StringIO()):
            return self.service.translate_chapter(self.project_id, self.chapter_id, {"batchIndex": batch_index})

    def test_projects_without_a_claude_choice_keep_translating_with_deepl(self):
        result = self.service.translate_chapter(self.project_id, self.chapter_id, {})

        self.assertEqual("deepl", result["providerId"])
        self.assertEqual(3, result["translatedParagraphCount"])
        self.assertNotIn("totalBatches", result)
        self.assertEqual([], self.transport.calls)

    def test_a_deepl_connection_chosen_for_the_project_keeps_the_deepl_path(self):
        self.storage.update_project(self.project_id, {
            "aiConfiguration": {"translationConnectionId": self.deepl_connection["connectionId"]},
        })

        result = self.service.translate_chapter(self.project_id, self.chapter_id, {})

        self.assertEqual("deepl", result["providerId"])
        self.assertEqual([], self.transport.calls)

    def test_claude_translates_one_batch_per_request_and_saves_it(self):
        self._use_claude()

        first = self._translate_batch(0)

        self.assertEqual("claude", first["providerId"])
        self.assertEqual(0, first["batchIndex"])
        self.assertEqual(3, first["totalBatches"])
        self.assertEqual([self.paragraph_ids[0]], first["sourceParagraphIds"])
        self.assertEqual(f"Переклад {self.paragraph_ids[0]} Гаррі", self.storage.get_paragraph(self.paragraph_ids[0])["translationText"])
        self.assertIsNone(self.storage.get_paragraph(self.paragraph_ids[1])["translationText"])
        self.assertEqual([], self.deepl.requests)

        for batch_index in (1, 2):
            self._translate_batch(batch_index)
        self.assertEqual(3, len(self.transport.calls))
        self.assertEqual(f"Переклад {self.paragraph_ids[2]}", self.storage.get_paragraph(self.paragraph_ids[2])["translationText"])

        with self.assertRaises(TranslationServiceError) as context:
            self._translate_batch(3)
        self.assertEqual("translation_invalid", context.exception.code)

    def test_batches_stay_well_under_the_cloudflare_timeout_budget(self):
        self._use_claude()
        self._translate_batch(0)

        call = self.transport.calls[0]
        self.assertLess(call["timeout"], 100)
        chunk = chunk_from_user_message(self.transport.user_message())
        self.assertLessEqual(len(chunk.findall("p")), TranslationService._LLM_BATCH_MAX_PARAGRAPHS)

    def test_system_prompt_carries_glossary_characters_rules_and_dialogue_convention(self):
        self._use_claude()
        self._translate_batch(0)

        system = self.transport.system_prompt()
        self.assertIn("Harry → Гаррі", system)
        self.assertIn("рід: чоловічий рід", system)
        self.assertIn("мовний регістр: постійна лайка", system)
        self.assertIn("не відмінюється", system)
        self.assertIn("Mira → Міра; рід: жіночий рід", system)
        self.assertIn("wand → чарівна паличка — не «жезл»", system)
        self.assertIn("Звертання до старших — на «ви».", system)
        self.assertIn("Не перекладай назви вулиць.", system)
        self.assertIn("тире (—), без лапок", system)
        self.assertIn("— Іди, — сказав він.", system)

    def test_system_prompt_is_cached_and_identical_for_every_batch(self):
        self._use_claude()
        self._translate_batch(0)
        self._translate_batch(1)

        first, second = (call["body"]["system"] for call in self.transport.calls)
        self.assertEqual(first, second)
        self.assertEqual({"type": "ephemeral"}, first[0]["cache_control"])
        self.assertNotIn(self.paragraph_ids[0], first[0]["text"])

    def test_user_message_has_source_and_translated_context_before_the_batch(self):
        self.storage.update_paragraph(self.chapter_one_ids[2], "Раніше три.", False)
        self.storage.update_paragraph(self.chapter_one_ids[3], "Раніше чотири.", False)
        self._use_claude()

        self._translate_batch(0)

        message = self.transport.user_message()
        source = re.search(r"<context_source>(.*)</context_source>", message, re.S).group(1)
        self.assertNotIn("Earlier one.", source)
        self.assertIn("Earlier two.", source)
        self.assertIn("Earlier four.", source)
        translated = re.search(r"<context_translation>(.*)</context_translation>", message, re.S).group(1)
        self.assertIn("Раніше три.", translated)
        self.assertIn("Раніше чотири.", translated)
        # The batch itself is never part of the context.
        self.assertNotIn("Harry said", source)

    def test_later_batches_see_earlier_batches_translations_as_context(self):
        self._use_claude()
        self._translate_batch(0)
        self._translate_batch(1)

        translated = re.search(r"<context_translation>(.*)</context_translation>", self.transport.user_message(1), re.S).group(1)
        self.assertIn(f"Переклад {self.paragraph_ids[0]}", translated)

    def test_narrator_change_is_inherited_by_following_batches(self):
        self.storage.set_paragraph_narrator_change(self.paragraph_ids[1], "femn")
        self._use_claude()

        self._translate_batch(0)
        self._translate_batch(2)

        self.assertIn(f"[{self.paragraph_ids[0]}]: оповідач — чоловік", self.transport.user_message(0))
        self.assertIn(f"[{self.paragraph_ids[2]}]: оповідач — жінка", self.transport.user_message(1))

    def test_model_comes_from_the_project_setting_with_sonnet_as_default(self):
        self._use_claude()
        self._translate_batch(0)
        self.assertEqual("claude-sonnet-5-5", self.transport.calls[0]["body"]["model"])

        self._use_claude(translationModel="claude-opus-5-5")
        self._translate_batch(0)
        self.assertEqual("claude-opus-5-5", self.transport.calls[1]["body"]["model"])

    # --- glossary: catalog + translation (DeepL) glossary -------------------------

    def _add_translation_glossary(self, entries, source_language="EN", target_language="UK"):
        glossary = self.storage.get_or_create_project_translation_glossary(self.project_id, source_language, target_language)
        item_ids = self.storage.resolve_glossary_item_ids(entries)
        self.storage.commit_translation_glossary_version(glossary["glossaryRuleId"], item_ids)

    def _prompt_log(self, batch_index=0):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.service.translate_chapter(self.project_id, self.chapter_id, {"batchIndex": batch_index})
        lines = [line for line in output.getvalue().splitlines() if line.startswith("[CLAUDE PROMPT]")]
        self.assertEqual(1, len(lines))
        return lines[0], json.loads(lines[0].removeprefix("[CLAUDE PROMPT] "))

    def test_terms_only_in_the_translation_glossary_reach_the_claude_prompt(self):
        # Saved through the DeepL glossary editor: linked to the version, not to project_glossary.
        self._add_translation_glossary([
            {"source": "Court of Justice", "target": "Двір Правосуддя"},
            {"source": "wand", "target": "чарівна паличка", "context": "не «жезл»"},  # same row as the catalog entry
            {"source": "Harry", "target": "Гаррі", "context": "з DeepL-глосарію"},  # different row, same term
        ])
        self.assertNotIn(
            "Court of Justice",
            [entry["source"] for entry in self.storage.list_glossary() if entry["glossaryEntryId"] in self.storage.get_project(self.project_id)["projectGlossaryEntryIds"]],
        )
        self._use_claude()

        _, logged = self._prompt_log()

        system = self.transport.system_prompt()
        self.assertIn("- Court of Justice → Двір Правосуддя", system)
        self.assertEqual(1, system.count("wand → чарівна паличка"))
        self.assertEqual(1, system.count("Harry → Гаррі"))
        # On a duplicate the catalog entry (with gender and register) wins.
        self.assertIn("Harry → Гаррі; рід: чоловічий рід; мовний регістр: постійна лайка", system)
        self.assertNotIn("з DeepL-глосарію", system)
        self.assertEqual(["Court of Justice", "Harry", "Mira", "wand"], logged["glossarySources"])
        self.assertEqual(4, logged["glossaryTermCount"])

    def test_translation_glossaries_for_other_language_pairs_are_ignored(self):
        self._add_translation_glossary([{"source": "Court of Justice", "target": "Gerichtshof"}], "EN", "DE")
        self._use_claude()

        self._prompt_log()

        self.assertNotIn("Gerichtshof", self.transport.system_prompt())

    def test_prompt_log_line_summarises_the_prompt_without_book_text(self):
        self._use_claude()

        line, logged = self._prompt_log()

        self.assertEqual(3, logged["glossaryTermCount"])
        self.assertEqual(["Harry", "Mira", "wand"], logged["glossarySources"])
        self.assertEqual(2, logged["characterCount"])
        self.assertEqual(2, logged["ruleCount"])  # one catalog rule + the project's translationRules
        self.assertEqual(["Harry"], logged["batchGlossaryHits"])
        self.assertNotIn("Go,", line)
        self.assertNotIn("rain over the river", line)

    def test_prompt_makes_glossary_forms_mandatory_with_the_possessive_example(self):
        self._use_claude()
        self._prompt_log()

        system = self.transport.system_prompt()
        self.assertIn("ГЛОСАРІЙ — ОБОВ'ЯЗКОВО", system)
        self.assertIn("лише граматичну форму відповідника: відмінок, число", system)
        self.assertIn("Заборонено: синоніми", system)
        self.assertIn("\"the Court of Justice's ruling\" → «рішення Двору Правосуддя»", system)
        self.assertIn("НЕПРАВИЛЬНО: «рішення Двору Справедливості»", system)

    def test_terms_present_in_the_batch_are_repeated_next_to_the_text(self):
        self._use_claude()
        self._prompt_log(0)
        self._prompt_log(1)

        first, second = self.transport.user_message(0), self.transport.user_message(1)
        self.assertIn("ТЕРМІНИ ГЛОСАРІЮ В ЦЬОМУ ФРАГМЕНТІ", first)
        self.assertIn("- Harry → Гаррі", first)
        self.assertNotIn("ТЕРМІНИ ГЛОСАРІЮ В ЦЬОМУ ФРАГМЕНТІ", second)
        # The reminder sits in the per-batch message, so the cached system prompt is unchanged.
        self.assertEqual(self.transport.calls[0]["body"]["system"], self.transport.calls[1]["body"]["system"])

    def test_usage_of_every_call_is_logged(self):
        self._use_claude()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = self.service.translate_chapter(self.project_id, self.chapter_id, {"batchIndex": 0})

        lines = [line for line in output.getvalue().splitlines() if line.startswith("[CLAUDE USAGE]")]
        self.assertEqual(1, len(lines))
        logged = json.loads(lines[0].removeprefix("[CLAUDE USAGE] "))
        self.assertEqual(
            {"inputTokens": 120, "outputTokens": 80, "cacheWriteTokens": 900, "cacheReadTokens": 0},
            {key: logged[key] for key in ("inputTokens", "outputTokens", "cacheWriteTokens", "cacheReadTokens")},
        )
        self.assertEqual("claude-sonnet-5-5", logged["model"])
        self.assertEqual(120, result["usage"]["input_tokens"])

    def test_mismatched_paragraph_ids_fail_the_batch_without_saving(self):
        def wrong_ids(body):
            root = chunk_from_user_message(body["messages"][0]["content"])
            for element in root.findall("p"):
                element.attrib["id"] = "invented"
                element.text = "Переклад"
            return 200, message_payload(ET.tostring(root, encoding="unicode"))

        self.transport.responder = wrong_ids
        self._use_claude()

        with self.assertRaises(TranslationServiceError) as context:
            self._translate_batch(0)

        self.assertEqual("chunk_mapping_failed", context.exception.code)
        self.assertEqual(2, len(self.transport.calls))  # one retry, then the strict check wins
        self.assertIsNone(self.storage.get_paragraph(self.paragraph_ids[0])["translationText"])

    def test_reply_without_valid_xml_fails_the_batch_without_saving(self):
        self.transport.responder = lambda body: (200, message_payload("Ось переклад: Іди, сказав він."))
        self._use_claude()

        with self.assertRaises(TranslationServiceError) as context:
            self._translate_batch(0)

        self.assertEqual("chunk_mapping_failed", context.exception.code)
        self.assertIsNone(self.storage.get_paragraph(self.paragraph_ids[0])["translationText"])

    def test_refusal_fails_the_batch_without_saving_or_retrying(self):
        self.transport.responder = lambda body: (200, {
            **message_payload(""),
            "stop_reason": "refusal",
            "stop_details": {"type": "refusal", "category": "general_harms"},
        })
        self._use_claude()

        with self.assertRaises(TranslationServiceError) as context:
            self._translate_batch(0)

        self.assertEqual("provider_error", context.exception.code)
        self.assertIn("general_harms", str(context.exception))
        self.assertEqual(1, len(self.transport.calls))
        self.assertIsNone(self.storage.get_paragraph(self.paragraph_ids[0])["translationText"])

    def _mark_reviewed(self, *paragraph_ids):
        for paragraph_id in paragraph_ids:
            self.storage.update_paragraph(paragraph_id, f"Вичитано {paragraph_id}", True)

    def _assert_untouched_reviewed(self, paragraph_id):
        paragraph = self.storage.get_paragraph(paragraph_id)
        self.assertEqual(f"Вичитано {paragraph_id}", paragraph["translationText"])
        self.assertTrue(paragraph["reviewed"])

    def test_deepl_chapter_translation_skips_reviewed_paragraphs(self):
        self._mark_reviewed(self.paragraph_ids[1])

        result = self.service.translate_chapter(self.project_id, self.chapter_id, {})

        self.assertEqual([self.paragraph_ids[0], self.paragraph_ids[2]], result["sourceParagraphIds"])
        self.assertEqual([self.paragraph_ids[1]], result["skippedReviewedParagraphIds"])
        self.assertEqual(2, result["translatedParagraphCount"])
        sent_ids = [element.attrib["id"] for request in self.deepl.requests for element in ET.fromstring(request.text).findall("p")]
        self.assertNotIn(self.paragraph_ids[1], sent_ids)
        self._assert_untouched_reviewed(self.paragraph_ids[1])
        self.assertEqual("DeepL переклад", self.storage.get_paragraph(self.paragraph_ids[2])["translationText"])

    def test_claude_chapter_translation_skips_reviewed_paragraphs(self):
        self._mark_reviewed(self.paragraph_ids[1])
        self._use_claude()

        first = self._translate_batch(0)
        second = self._translate_batch(1)

        self.assertEqual(2, first["totalBatches"])
        self.assertEqual([self.paragraph_ids[0]], first["sourceParagraphIds"])
        self.assertEqual([self.paragraph_ids[2]], second["sourceParagraphIds"])
        self.assertEqual([self.paragraph_ids[1]], second["skippedReviewedParagraphIds"])
        for index in range(len(self.transport.calls)):
            chunk_ids = [element.attrib["id"] for element in chunk_from_user_message(self.transport.user_message(index)).findall("p")]
            self.assertNotIn(self.paragraph_ids[1], chunk_ids)
        self._assert_untouched_reviewed(self.paragraph_ids[1])
        self.assertEqual(f"Переклад {self.paragraph_ids[2]}", self.storage.get_paragraph(self.paragraph_ids[2])["translationText"])
        # The proofread text still feeds the context for the paragraphs after it.
        self.assertIn(f"Вичитано {self.paragraph_ids[1]}", self.transport.user_message(1))

    def test_fully_reviewed_chapter_calls_no_provider(self):
        self._mark_reviewed(*self.paragraph_ids)

        deepl_result = self.service.translate_chapter(self.project_id, self.chapter_id, {})
        self.assertEqual(0, deepl_result["translatedParagraphCount"])
        self.assertEqual(self.paragraph_ids, deepl_result["skippedReviewedParagraphIds"])
        self.assertEqual([], self.deepl.requests)

        self._use_claude()
        claude_result = self._translate_batch(0)
        self.assertEqual(0, claude_result["totalBatches"])
        self.assertEqual(0, claude_result["translatedParagraphCount"])
        self.assertEqual(self.paragraph_ids, claude_result["skippedReviewedParagraphIds"])
        self.assertEqual([], self.transport.calls)
        for paragraph_id in self.paragraph_ids:
            self._assert_untouched_reviewed(paragraph_id)

    def test_paragraph_button_adds_a_version_to_a_reviewed_paragraph_on_both_providers_and_keeps_its_text(self):
        paragraph_id = self.paragraph_ids[0]
        self._mark_reviewed(paragraph_id)
        deepl_result = self.service.translate_paragraph(paragraph_id, {})
        self.assertEqual("deepl", deepl_result["providerId"])
        self.assertEqual(f"Вичитано {paragraph_id}", deepl_result["translationText"])
        self.assertTrue(deepl_result["reviewed"])
        self.assertEqual(["DeepL переклад"], [item["text"] for item in deepl_result["translationVariants"] if item["engine"] == "deepl"])

        self._use_claude()
        with contextlib.redirect_stdout(io.StringIO()):
            claude_result = self.service.translate_paragraph(paragraph_id, {})
        self.assertEqual("claude", claude_result["providerId"])
        self.assertEqual(f"Вичитано {paragraph_id}", claude_result["translationText"])
        self.assertTrue(claude_result["reviewed"])
        self.assertEqual(
            [f"Переклад {paragraph_id} Гаррі"], [item["text"] for item in claude_result["translationVariants"] if item["engine"] == "claude"]
        )

    def test_single_paragraph_translation_follows_the_project_choice(self):
        self._use_claude()

        with contextlib.redirect_stdout(io.StringIO()):
            result = self.service.translate_paragraph(
                self.paragraph_ids[2], {"connectionId": self.deepl_connection["connectionId"]}
            )

        self.assertEqual("claude", result["providerId"])
        self.assertEqual(f"Переклад {self.paragraph_ids[2]}", result["translationText"])
        self.assertIn(f"[{self.paragraph_ids[2]}]: оповідач — чоловік", self.transport.user_message())
        self.assertEqual([], self.deepl.requests)

    def test_claude_connection_that_is_not_ready_is_reported_not_silently_replaced(self):
        broken = self._connection("claude", "other-key", status="error")
        self.storage.update_project(self.project_id, {"aiConfiguration": {"translationConnectionId": broken["connectionId"]}})

        with self.assertRaises(TranslationServiceError) as context:
            self.service.translate_chapter(self.project_id, self.chapter_id, {})

        self.assertEqual("translation_connection_not_ready", context.exception.code)
        self.assertEqual([], self.deepl.requests)



class GlossaryPromptHelperTests(unittest.TestCase):
    def test_possessive_and_case_variants_match_whole_words_only(self):
        entries = [{"source": "Court of Justice", "target": "Двір Правосуддя"}, {"source": "Court", "target": "Двір"}]

        hits = glossary_terms_in_text(entries, '<chunk><p id="p">The <i>court of justice\'s</i> ruling</p></chunk>')
        # The longest match wins: "Court" inside "court of justice" is not reported...
        self.assertEqual(["Court of Justice"], [entry["source"] for entry in hits])
        # ...but a separate occurrence of it is.
        hits = glossary_terms_in_text(entries, "<p>The court of justice met; the court rose.</p>")
        self.assertEqual(["Court of Justice", "Court"], [entry["source"] for entry in hits])
        self.assertEqual([], glossary_terms_in_text(entries, "<p>A quiet courtyard.</p>"))

    def test_duplicates_collapse_on_source_and_the_first_entry_wins(self):
        selected = select_glossary_entries([
            {"source": "Court of Justice", "target": "Двір Правосуддя", "note": "catalog"},
            {"source": "court of justice ", "target": "Суд", "note": "translation glossary"},
            {"source": "Inactive", "target": "x", "active": False},
            {"source": "", "target": "empty"},
        ])

        self.assertEqual([("Court of Justice", "catalog")], [(entry["source"], entry["note"]) for entry in selected])


if __name__ == "__main__":
    unittest.main()
