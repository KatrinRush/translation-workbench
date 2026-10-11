import contextlib
import io
import json
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from cryptography.fernet import Fernet

from backend.integrations.credentials import CredentialVault
from backend.integrations.providers.claude import ClaudeProvider
from backend.integrations.registry import ProviderRegistry
from backend.storage import Storage
from backend.translations.glossary_check import find_glossary_hits, missing_terms
from backend.translations.service import TranslationService

JUSTICE_COURT = {"source": "Justice's Court", "target": "Двір Правосуддя"}
COURT = {"source": "court", "target": "суд"}
JUSTICE = {"source": "Justice", "target": "Правосуддя"}
RAZAK = {"source": "Razak", "target": "Разак"}


def sources(entries):
    return [entry["source"] for entry in entries]


class FindGlossaryHitsTests(unittest.TestCase):
    def test_typographic_apostrophe_in_text_matches_straight_one_in_glossary(self):
        self.assertEqual(["Justice's Court"], sources(find_glossary_hits([JUSTICE_COURT], "Razak fled Justice’s court.")))

    def test_typographic_apostrophe_in_glossary_matches_straight_one_in_text(self):
        entry = {"source": "Justice’s Court", "target": "Двір Правосуддя"}
        self.assertEqual(["Justice’s Court"], sources(find_glossary_hits([entry], "Razak fled Justice's court.")))
        self.assertEqual(["Justice’s Court"], sources(find_glossary_hits([entry], "Razak fled Justiceʼs Court.")))

    def test_case_is_ignored_both_ways(self):
        self.assertEqual(["court"], sources(find_glossary_hits([COURT], "The Court rose.")))
        self.assertEqual(["Justice"], sources(find_glossary_hits([JUSTICE], "blind justice")))

    def test_longest_match_wins_and_short_terms_inside_it_are_not_reported(self):
        entries = [COURT, JUSTICE, JUSTICE_COURT, RAZAK]
        hits = find_glossary_hits(entries, '<p id="p-1">Razak fled <i>Justice’s court</i> at dawn.</p>')
        self.assertEqual(["Justice's Court", "Razak"], sources(hits))

    def test_a_short_term_outside_the_long_match_still_counts(self):
        entries = [COURT, JUSTICE, JUSTICE_COURT]
        hits = find_glossary_hits(entries, "He fled Justice’s court; the court never forgot.")
        self.assertEqual(["court", "Justice's Court"], sources(hits))

    def test_whole_words_only(self):
        self.assertEqual([], find_glossary_hits([COURT], "A quiet courtyard."))


class MissingTermsTests(unittest.TestCase):
    def test_any_case_or_number_of_the_equivalent_counts(self):
        self.assertEqual([], missing_terms([JUSTICE_COURT, RAZAK], "Разак утік із Двору Правосуддя."))
        self.assertEqual([], missing_terms([JUSTICE_COURT], "У дворі <b>правосуддя</b> було тихо."))

    def test_a_synonym_is_reported(self):
        self.assertEqual(["Justice's Court"], sources(missing_terms([JUSTICE_COURT, RAZAK], "Разак утік із Двору Справедливості.")))


def chunk_of(message):
    return ET.fromstring(re.search(r"<chunk>.*</chunk>", message, re.S).group(0))


class ScriptedTransport:
    """Mock Claude HTTP: each call takes the next reply builder (message -> chunk XML or raw text)."""

    def __init__(self, *builders):
        self.builders = list(builders)
        self.calls = []

    def post(self, url, headers, body, timeout):
        payload = json.loads(body)
        message = payload["messages"][0]["content"]
        self.calls.append(message)
        builder = self.builders.pop(0) if len(self.builders) > 1 else self.builders[0]
        reply = {"model": payload["model"], "stop_reason": "end_turn", "content": [{"type": "text", "text": builder(message)}],
                 "usage": {"input_tokens": 1, "output_tokens": 1}}
        return 200, json.dumps(reply, ensure_ascii=False).encode("utf-8")


def answer(text):
    def build(message):
        root = chunk_of(message)
        for element in root.findall("p"):
            for child in list(element):
                element.remove(child)
            element.text = text
        return ET.tostring(root, encoding="unicode")
    return build


SYNONYM = answer("Разак утік із Двору Справедливості.")
COMPLIANT = answer("Разак утік із Двору Правосуддя.")


class GlossaryCheckServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")
        self.vault = CredentialVault(Fernet(Fernet.generate_key()))
        entry_ids = [self.storage.create_glossary_entry(entry)["glossaryEntryId"] for entry in (COURT, JUSTICE, JUSTICE_COURT, RAZAK)]
        connection = self.storage.create_integration_connection("claude", "Claude", self.vault.encrypt({"apiKey": "k"}))
        self.storage.update_integration_connection_status(connection["connectionId"], "connected", "ok", "ok", {})
        self.project_id = self.storage.create_project({
            "title": "Fool me twice", "status": "translation", "projectGlossaryEntryIds": entry_ids,
            "aiConfiguration": {"translationConnectionId": connection["connectionId"]},
        })["projectId"]
        self.storage.save_book_structure(
            self.project_id, "book.epub", "application/epub+zip", b"book",
            {"chapters": [{"title": "CHAPTER 38", "elements": [{"type": "paragraph", "text": "Razak fled Justice’s court."}]}]},
        )
        chapter = self.storage.get_book_structure(self.project_id)["chapters"][0]
        self.chapter_id = chapter["chapterId"]
        self.paragraph_id = chapter["elements"][0]["paragraphId"]

    def tearDown(self):
        self.temporary_directory.cleanup()

    def translate(self, transport):
        service = TranslationService(self.storage, self.vault, ProviderRegistry([ClaudeProvider(transport)]))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            service.translate_chapter(self.project_id, self.chapter_id, {"batchIndex": 0})
        return output.getvalue()

    def claude_variant(self):
        return next(item for item in self.storage.get_paragraph(self.paragraph_id)["translationVariants"] if item["engine"] == "claude")

    def test_hits_and_reminder_use_the_longest_term_with_its_translation(self):
        transport = ScriptedTransport(COMPLIANT)
        log = self.translate(transport)

        prompt = json.loads(next(line for line in log.splitlines() if line.startswith("[CLAUDE PROMPT]")).removeprefix("[CLAUDE PROMPT] "))
        self.assertEqual(["Justice's Court", "Razak"], prompt["batchGlossaryHits"])
        reminder = transport.calls[0].split("ТЕРМІНИ ГЛОСАРІЮ В ЦЬОМУ ФРАГМЕНТІ", 1)[1].split("Переклади цей фрагмент", 1)[0]
        self.assertIn("- Justice's Court → Двір Правосуддя", reminder)
        self.assertIn("- Razak → Разак", reminder)
        self.assertNotIn("- court →", reminder)
        self.assertNotIn("- Justice →", reminder)

    def test_compliant_translation_needs_no_retry(self):
        transport = ScriptedTransport(COMPLIANT)
        log = self.translate(transport)
        self.assertEqual(1, len(transport.calls))
        self.assertNotIn("GLOSSARY CHECK", log)
        self.assertEqual([], self.claude_variant()["warnings"])

    def test_missing_equivalent_triggers_one_retry_that_names_it(self):
        transport = ScriptedTransport(SYNONYM, COMPLIANT)
        self.translate(transport)

        self.assertEqual(2, len(transport.calls))
        self.assertIn("НЕ ВИКОРИСТАНО ОБОВ'ЯЗКОВІ ВІДПОВІДНИКИ", transport.calls[1])
        self.assertIn(f"- [{self.paragraph_id}] Justice's Court → Двір Правосуддя", transport.calls[1])
        self.assertEqual("Разак утік із Двору Правосуддя.", self.storage.get_paragraph(self.paragraph_id)["translationText"])
        self.assertEqual([], self.claude_variant()["warnings"])

    def test_still_missing_after_the_retry_becomes_a_warning_on_the_variant(self):
        transport = ScriptedTransport(SYNONYM, SYNONYM)
        log = self.translate(transport)

        self.assertEqual(2, len(transport.calls))  # exactly one retry
        self.assertEqual(
            [{"type": "glossary_missing", "source": "Justice's Court", "target": "Двір Правосуддя"}],
            self.claude_variant()["warnings"],
        )
        check = json.loads(next(line for line in log.splitlines() if line.startswith("[CLAUDE GLOSSARY CHECK]")).removeprefix("[CLAUDE GLOSSARY CHECK] "))
        self.assertEqual({self.paragraph_id: ["Justice's Court"]}, check["stillMissing"])
        element = self.storage.get_book_structure(self.project_id)["chapters"][0]["elements"][0]
        self.assertEqual("glossary_missing", element["translationVariants"][0]["warnings"][0]["type"])

    def test_retry_with_broken_xml_keeps_the_first_translation_and_warns(self):
        transport = ScriptedTransport(SYNONYM, lambda message: "not xml at all")
        self.translate(transport)

        self.assertEqual(2, len(transport.calls))
        self.assertEqual("Разак утік із Двору Справедливості.", self.storage.get_paragraph(self.paragraph_id)["translationText"])
        self.assertEqual("Justice's Court", self.claude_variant()["warnings"][0]["source"])


if __name__ == "__main__":
    unittest.main()
