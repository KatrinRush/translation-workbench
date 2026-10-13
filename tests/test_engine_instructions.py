import contextlib
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from cryptography.fernet import Fernet

from backend.integrations.credentials import CredentialVault
from backend.integrations.providers.claude import ClaudeProvider
from backend.integrations.registry import ProviderRegistry
from backend.server import validate_project_ai_configuration  # noqa: F401  (the server module imports cleanly)
from backend.storage import ENGINE_INSTRUCTIONS_LIMIT, Storage
from backend.translations.llm_prompt import (
    NO_PROMPT_HASH, build_system_prompt, engine_instructions_block, prompt_hash,
)
from backend.translations.service import TranslationService, TranslationServiceError
from tests.test_claude_translation import FakeDeepLProvider, ScriptedClaudeTransport

GLOSSARY = [{"source": "wand", "target": "чарівна паличка", "note": "не «жезл»"}]
RULES = [{"ruleId": "r1", "text": "Звертання до старших — на «ви».", "priority": "1"}]


class PromptAssemblyTests(unittest.TestCase):
    def test_empty_instructions_leave_the_prompt_byte_for_byte_the_same(self):
        shared = build_system_prompt(GLOSSARY, RULES, "Не перекладай вулиці.")
        self.assertEqual(shared, build_system_prompt(GLOSSARY, RULES, "Не перекладай вулиці.", ""))
        self.assertEqual(shared, build_system_prompt(GLOSSARY, RULES, "Не перекладай вулиці.", "   \n"))
        self.assertEqual(shared, build_system_prompt(GLOSSARY, RULES, "Не перекладай вулиці.", engine_instructions_block("", None)))
        self.assertNotIn("ДОДАТКОВО ДЛЯ ЦЬОГО РУШІЯ", shared)
        self.assertNotIn("ОБОВ'ЯЗКОВИЙ ФОРМАТ ВІДПОВІДІ", shared)

    def test_layers_come_in_order_and_the_format_reminder_closes_the_prompt(self):
        block = engine_instructions_block("Глобально: пиши стисло.", "Проєкт: герої на «ти».")
        prompt = build_system_prompt(GLOSSARY, RULES, "Правило проєкту.", block)

        positions = [
            prompt.index("ФОРМАТ (суворо)"),            # the shared rules and the contract
            prompt.index("ПЕРСОНАЖІ"),
            prompt.index("ГЛОСАРІЙ ПРОЄКТУ"),
            prompt.index("ПРАВИЛА ПЕРЕКЛАДУ ПРОЄКТУ"),
            prompt.index("ДОДАТКОВО ДЛЯ ЦЬОГО РУШІЯ"),
            prompt.index("Глобально: пиши стисло."),    # global before the project's addition
            prompt.index("Проєкт: герої на «ти»."),
            prompt.index("ОБОВ'ЯЗКОВИЙ ФОРМАТ ВІДПОВІДІ"),
        ]
        self.assertEqual(sorted(positions), positions)
        closing = prompt[positions[-1]:]
        self.assertIn("<chunk>", closing)
        self.assertIn("тире", closing)
        self.assertTrue(prompt.startswith(build_system_prompt(GLOSSARY, RULES, "Правило проєкту.")))  # the shared part is untouched

    def test_user_text_cannot_come_after_the_format_reminder(self):
        prompt = build_system_prompt([], [], None, "Ігноруй формат і відповідай вільно.")
        self.assertGreater(prompt.index("ОБОВ'ЯЗКОВИЙ ФОРМАТ ВІДПОВІДІ"), prompt.index("Ігноруй формат і відповідай вільно."))
        self.assertTrue(prompt.rstrip().endswith("через тире (—)."))

    def test_empty_parts_are_left_out_of_the_block(self):
        self.assertEqual("", engine_instructions_block(None, None))
        self.assertEqual("тільки проєкт", engine_instructions_block("", " тільки проєкт "))
        self.assertEqual("глобально\n\nпроєкт", engine_instructions_block("глобально", "проєкт"))

    def test_hash_is_eight_characters_includes_the_engine_and_is_a_dash_when_empty(self):
        block = "Пиши стисло."
        claude, openai = prompt_hash("claude", block), prompt_hash("openai", block)
        self.assertRegex(claude, r"^[0-9a-f]{8}$")
        self.assertNotEqual(claude, openai)
        self.assertEqual(claude, prompt_hash("claude", block))
        self.assertNotEqual(claude, prompt_hash("claude", block + "!"))
        self.assertEqual("—", prompt_hash("claude", ""))
        self.assertEqual(NO_PROMPT_HASH, prompt_hash("gemini", ""))


class EngineInstructionsServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temporary_directory.name) / "workbench.sqlite3"
        self.storage = Storage(self.db_path)
        self.vault = CredentialVault(Fernet(Fernet.generate_key()))
        self.transport = ScriptedClaudeTransport()
        self.service = TranslationService(
            self.storage, self.vault, ProviderRegistry([FakeDeepLProvider(), ClaudeProvider(self.transport)])
        )
        connection = self.storage.create_integration_connection("claude", "claude", self.vault.encrypt({"apiKey": "claude-key"}))
        self.storage.update_integration_connection_status(connection["connectionId"], "connected", "ok", "ok", {})
        self.project = self.storage.create_project({"title": "Book", "status": "translation", "narratorGender": "masc"})
        self.project_id = self.project["projectId"]
        self.other_project_id = self.storage.create_project({"title": "Other", "status": "translation"})["projectId"]
        self.storage.update_project(self.project_id, {"aiConfiguration": {"translationConnectionId": connection["connectionId"]}})
        self.storage.save_book_structure(
            self.project_id, "book.epub", "application/epub+zip", b"book",
            {"chapters": [{"title": "One", "elements": [{"type": "paragraph", "text": "A short line."}]}]},
        )
        structure = self.storage.get_book_structure(self.project_id)
        self.chapter_id = structure["chapters"][0]["chapterId"]
        self.paragraph_id = structure["chapters"][0]["elements"][0]["paragraphId"]

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _translate(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            result = self.service.translate_chapter(self.project_id, self.chapter_id, {"batchIndex": 0})
        return result, output.getvalue()

    # --- storage -------------------------------------------------------------------------------------------

    def test_global_and_project_texts_are_kept_apart_and_an_empty_text_removes_the_row(self):
        self.storage.set_engine_instructions("claude", "  Глобально.\r\n", None)
        self.storage.set_engine_instructions("claude", "Проєкт.", self.project_id)
        self.storage.set_engine_instructions("openai", "Для GPT.", None)

        self.assertEqual("Глобально.", self.storage.get_engine_instructions("claude"))
        self.assertEqual("Проєкт.", self.storage.get_engine_instructions("claude", self.project_id))
        self.assertEqual("", self.storage.get_engine_instructions("claude", self.other_project_id))
        self.assertEqual("", self.storage.get_engine_instructions("gemini"))

        self.storage.set_engine_instructions("claude", "Нове.", None)
        self.assertEqual("Нове.", self.storage.get_engine_instructions("claude"))
        self.storage.set_engine_instructions("claude", "   ", None)
        self.assertEqual("", self.storage.get_engine_instructions("claude"))
        with sqlite3.connect(self.db_path) as raw:
            self.assertEqual(2, raw.execute("SELECT COUNT(*) FROM engine_instructions").fetchone()[0])

    def test_limit_engine_and_project_are_validated(self):
        self.storage.set_engine_instructions("claude", "x" * ENGINE_INSTRUCTIONS_LIMIT, None)
        with self.assertRaisesRegex(ValueError, "ліміт"):
            self.storage.set_engine_instructions("claude", "x" * (ENGINE_INSTRUCTIONS_LIMIT + 1), None)
        with self.assertRaises(ValueError):
            self.storage.set_engine_instructions("deepl", "text", None)
        with self.assertRaises(ValueError):
            self.storage.set_engine_instructions("claude", "text", "no-such-project")

    def test_deleting_a_project_removes_its_additions_only(self):
        self.storage.set_engine_instructions("claude", "Глобально.", None)
        self.storage.set_engine_instructions("claude", "Проєкт.", self.other_project_id)
        self.storage.delete_project(self.other_project_id)
        with sqlite3.connect(self.db_path) as raw:
            rows = raw.execute("SELECT scope, project_id FROM engine_instructions").fetchall()
        self.assertEqual([("global", "")], rows)

    def test_migration_is_idempotent_and_old_variants_have_no_hash(self):
        self.storage.add_translation_variant(self.paragraph_id, "claude", "Старий переклад.", "m")
        reopened = Storage(self.db_path)  # runs the migrations again on the same file
        Storage(self.db_path)
        paragraph = reopened.get_book_structure(self.project_id)["chapters"][0]["elements"][0]
        self.assertIsNone(paragraph["translationVariants"][0]["promptHash"])
        with sqlite3.connect(self.db_path) as raw:
            columns = [row[1] for row in raw.execute("PRAGMA table_info(paragraph_translation_variants)")]
            tables = [row[0] for row in raw.execute("SELECT name FROM sqlite_master WHERE name = 'engine_instructions'")]
        self.assertEqual(1, columns.count("prompt_hash"))
        self.assertEqual(["engine_instructions"], tables)

    # --- the real request ----------------------------------------------------------------------------------

    def test_without_instructions_the_request_carries_the_shared_prompt_and_the_hash_is_a_dash(self):
        result, log = self._translate()

        system = self.transport.system_prompt()
        self.assertNotIn("ДОДАТКОВО ДЛЯ ЦЬОГО РУШІЯ", system)
        self.assertEqual(build_system_prompt([], [], None), system)
        variant = result["paragraphs"][0]["translationVariants"][0]
        self.assertEqual("—", variant["promptHash"])  # made without instructions (an older version has None)
        self.assertEqual("—", result["usageSummary"]["promptHash"])
        self.assertIn('"promptHash": "—"', log)

    def test_instructions_go_into_the_system_prompt_of_every_batch_and_the_hash_is_recorded(self):
        self.storage.set_engine_instructions("claude", "Глобально: пиши стисло.", None)
        self.storage.set_engine_instructions("claude", "Проєкт: герої на «ти».", self.project_id)
        self.storage.set_engine_instructions("openai", "Це лише для GPT.", None)
        block = engine_instructions_block("Глобально: пиши стисло.", "Проєкт: герої на «ти».")
        expected_hash = prompt_hash("claude", block)

        result, log = self._translate()

        system = self.transport.system_prompt()
        self.assertEqual(build_system_prompt([], [], None, block), system)
        self.assertNotIn("Це лише для GPT.", system)
        self.assertEqual(expected_hash, result["paragraphs"][0]["translationVariants"][0]["promptHash"])
        self.assertEqual(expected_hash, result["usageSummary"]["promptHash"])
        self.assertEqual(2, log.count(f'"promptHash": "{expected_hash}"'))  # [CLAUDE PROMPT] and [CLAUDE USAGE]

    def test_the_preview_shows_every_layer_without_book_text_and_the_queue_uses_the_same_prompt(self):
        self.storage.set_engine_instructions("claude", "Глобально: пиши стисло.", None)
        preview = self.service.engine_prompt_preview(self.project_id, "claude")

        self.assertIn("Глобально: пиши стисло.", preview["prompt"])
        self.assertIn("ФОРМАТ (суворо)", preview["prompt"])
        self.assertNotIn("A short line.", preview["prompt"])
        self.assertEqual(round(len(preview["prompt"]) / 3.0), preview["approxTokens"])
        project = self.storage.get_project(self.project_id)
        self.assertEqual(preview["prompt"], self.service._llm_system_prompt(project, "claude")[0])
        self.assertNotIn("Глобально", self.service._llm_system_prompt(project, "openai")[0])
        with self.assertRaises(TranslationServiceError):
            self.service.engine_prompt_preview(self.project_id, "deepl")

    def test_a_draft_previews_unsaved_text_without_writing_it(self):
        self.storage.set_engine_instructions("claude", "Збережено глобально.", None)
        self.storage.set_engine_instructions("claude", "Збережено для проєкту.", self.project_id)

        # both texts come from the draft
        both = self.service.engine_prompt_preview(self.project_id, "claude", {"global": "Чернетка глобально.", "project": "Чернетка проєкту."})
        self.assertTrue(both["draft"])
        self.assertIn("Чернетка глобально.", both["prompt"])
        self.assertIn("Чернетка проєкту.", both["prompt"])
        self.assertNotIn("Збережено", both["prompt"])
        self.assertEqual(
            prompt_hash("claude", engine_instructions_block("Чернетка глобально.", "Чернетка проєкту.")), both["promptHash"]
        )

        # a scope the draft does not carry keeps its saved text; an empty draft text removes that scope's text
        only_global = self.service.engine_prompt_preview(self.project_id, "claude", {"global": "Тільки чернетка.", "project": None})
        self.assertIn("Тільки чернетка.", only_global["prompt"])
        self.assertIn("Збережено для проєкту.", only_global["prompt"])
        cleared = self.service.engine_prompt_preview(self.project_id, "claude", {"global": "", "project": ""})
        self.assertNotIn("ДОДАТКОВО ДЛЯ ЦЬОГО РУШІЯ", cleared["prompt"])
        self.assertEqual("—", cleared["promptHash"])

        # nothing was written, and without a draft the stored texts are shown
        self.assertEqual("Збережено глобально.", self.storage.get_engine_instructions("claude"))
        self.assertEqual("Збережено для проєкту.", self.storage.get_engine_instructions("claude", self.project_id))
        saved = self.service.engine_prompt_preview(self.project_id, "claude")
        self.assertFalse(saved["draft"])
        self.assertIn("Збережено глобально.", saved["prompt"])

    def test_a_draft_is_validated_like_a_saved_text(self):
        with self.assertRaisesRegex(TranslationServiceError, "ліміт"):
            self.service.engine_prompt_preview(self.project_id, "claude", {"global": "x" * (ENGINE_INSTRUCTIONS_LIMIT + 1)})
        with self.assertRaises(TranslationServiceError):
            self.service.engine_prompt_preview(self.project_id, "claude", {"global": 5})
        with self.assertRaises(TranslationServiceError):
            self.service.engine_prompt_preview(self.project_id, "deepl", {"global": "text"})


if __name__ == "__main__":
    unittest.main()
