"""Dictionary in the original column: sentence splitting, glossary shortcut, cache, strict JSON with one retry,
usage kind 'dictionary', apostrophes and hyphens, missing connection. Mock transport only."""
import json
import logging
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet

from backend import server
from backend.dictionary_service import DictionaryError, DictionaryService, plain_text, split_sentences
from backend.integrations.credentials import CredentialVault
from backend.integrations.providers.claude import ClaudeProvider
from backend.integrations.registry import ProviderRegistry
from backend.storage import Storage
from backend.usage import project_report

USAGE = {"input_tokens": 400, "output_tokens": 120, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}
PRICED = "claude-sonnet-5-5"

ANSWER = {
    "term": "bucket", "lemma": "bucket", "pos": "іменник", "termType": "word", "expandedPhrase": None,
    "meaningInContext": "відро", "translations": [{"text": "відро", "register": None}, {"text": "цебро", "register": "застаріле"}],
    "registerNote": None, "inThisTranslation": "відро", "examples": [{"en": "A bucket of water.", "uk": "Відро води."}],
}

PARAGRAPH = 'He said, "Dr. Smith kicked the bucket." She did not care. The well-known man didn’t stay till 5 o\'clock, Mr. Brown noted etc. Then he left.'


class Transport:
    def __init__(self):
        self.replies = []
        self.calls = []

    def post(self, url, headers, body, timeout):
        payload = json.loads(body)
        self.calls.append({"payload": payload, "timeout": timeout})
        reply = self.replies.pop(0) if self.replies else ANSWER
        text = reply if isinstance(reply, str) else json.dumps(reply, ensure_ascii=False)
        return 200, json.dumps({"model": payload["model"], "stop_reason": "end_turn", "content": [{"type": "text", "text": text}], "usage": USAGE}).encode()

    def prompt(self, index=-1):
        return self.calls[index]["payload"]["messages"][0]["content"]


class DictionaryFixture(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.directory.name) / "w.sqlite3"
        self.storage = Storage(self.database_path)
        self.vault = CredentialVault(Fernet(Fernet.generate_key()))
        self.connection = self.storage.create_integration_connection("claude", "Claude", self.vault.encrypt({"apiKey": "k"}))
        self.storage.update_integration_connection_status(self.connection["connectionId"], "connected", "ok", "ok", {})
        self.project_id = self.storage.create_project({"title": "Dict", "status": "translation"})["projectId"]
        self.storage.save_book_structure(self.project_id, "b.epub", "application/epub+zip", b"b", {"chapters": [
            {"title": "One", "elements": [{"type": "paragraph", "text": PARAGRAPH}, {"type": "paragraph", "text": "Plain <i>italic</i> words &amp; more."}]}]})
        chapter = self.storage.get_book_structure(self.project_id)["chapters"][0]
        self.chapter_id = chapter["chapterId"]
        self.paragraph_id, self.second_id = [e["paragraphId"] for e in chapter["elements"]]
        self.storage.update_paragraph(self.paragraph_id, "Він сказав: «Доктор Сміт віддав Богу душу».", False)
        self.transport = Transport()
        self.models = [{"id": PRICED, "displayName": "Sonnet"}]
        self.service = self.make_service()

    def make_service(self):
        registry = ProviderRegistry([ClaudeProvider(self.transport)])
        return DictionaryService(self.storage, self.vault, registry, lambda connection_id: {"models": self.models},
                                 lambda project: self.glossary_entries())

    def glossary_entries(self):
        return self.storage.list_glossary() if getattr(self, "use_glossary", False) else []

    def tearDown(self):
        self.directory.cleanup()

    def lookup(self, needle, mode="word", paragraph=None, nth=0, **extra):
        paragraph_id = paragraph or self.paragraph_id
        text = plain_text(self.storage.paragraph_lookup_context(paragraph_id)["originalText"])
        start = -1
        for _ in range(nth + 1):
            start = text.index(needle, start + 1)
        data = {"projectId": self.project_id, "paragraphId": paragraph_id, "text": needle, "offsetStart": start,
                "offsetEnd": start + len(needle), "mode": mode, **extra}
        return self.service.lookup(data)

    def usage_rows(self):
        return self.storage.list_translation_usage(self.project_id)


class SentenceTests(unittest.TestCase):
    def sentences(self, text):
        return [text[a:b] for a, b in split_sentences(text)]

    def test_abbreviations_and_initials_do_not_end_a_sentence(self):
        self.assertEqual(["Mr. Brown met Dr. Smith at St. Paul's, etc. and J. R. Smith left."],
                         self.sentences("Mr. Brown met Dr. Smith at St. Paul's, etc. and J. R. Smith left."))
        self.assertEqual(["That is, i.e. a test.", "Next one."], self.sentences("That is, i.e. a test. Next one."))

    def test_quotes_after_the_stop_close_the_sentence(self):
        self.assertEqual(['He said: "Go."', "She left."], self.sentences('He said: "Go." She left.'))
        self.assertEqual(['"Is it you?"', "Anna asked.", '"Yes."', "He nodded."], self.sentences('"Is it you?" Anna asked. "Yes." He nodded.'))

    def test_a_dialogue_tag_in_lower_case_stays_in_the_sentence(self):
        self.assertEqual(['"Stop!" she cried.', "Then it ended."], self.sentences('"Stop!" she cried. Then it ended.'))

    def test_ellipsis_and_plain_text(self):
        self.assertEqual(2, len(self.sentences("Well... Maybe. Not now.")) - 1)
        self.assertEqual(["no stops here"], self.sentences("no stops here"))
        self.assertEqual([(0, 0)], split_sentences(""))

    def test_numbers_and_the_pronoun_I(self):
        self.assertEqual(2, len(self.sentences("See No. 5 for details. He did.")))
        self.assertEqual(2, len(self.sentences("So did I. He left.")))


class LookupTests(DictionaryFixture):
    def test_a_word_is_looked_up_with_its_sentence_the_paragraph_and_the_translation(self):
        result = self.lookup("bucket")
        self.assertEqual(("model", "word", False, PRICED), (result["source"], result["mode"], result["cached"], result["model"]))
        self.assertEqual("відро", result["result"]["meaningInContext"])
        self.assertEqual(["відро", "цебро"], [t["text"] for t in result["result"]["translations"]])
        self.assertEqual(3, result["moreRemaining"])
        self.assertIsNone(result["priceWarning"])
        prompt = self.transport.prompt()
        self.assertIn('Dr. Smith kicked the ⟦bucket⟧."', prompt)  # the sentence, the term marked
        self.assertIn("Увесь абзац", prompt)  # the paragraph is sent as context
        self.assertIn("Доктор Сміт віддав Богу душу", prompt)  # the chosen translation
        self.assertNotIn("She did not care", prompt.split("Увесь абзац")[0])  # the sentence is only its own part
        payload = self.transport.calls[0]["payload"]
        self.assertLessEqual(payload["max_tokens"], 1500)
        self.assertLessEqual(self.transport.calls[0]["timeout"], 60)
        self.assertIn("JSON", payload["system"][0]["text"])

    def test_every_call_is_recorded_as_kind_dictionary_and_shows_in_the_cost_report(self):
        self.lookup("bucket")
        rows = self.usage_rows()
        self.assertEqual([("dictionary", "claude", PRICED, self.chapter_id, 400, 120)],
                         [(r["kind"], r["engine"], r["model"], r["chapterId"], r["inputTokens"], r["outputTokens"]) for r in rows])
        report = project_report(rows, self.storage.list_model_prices(), {})
        self.assertEqual(["dictionary"], [item["kind"] for item in report["byKind"]])
        self.assertGreater(report["total"]["costUsd"], 0)

    def test_a_phrase_is_looked_up_as_a_phrase(self):
        self.transport.replies.append({**ANSWER, "term": "kicked the bucket", "termType": "idiom", "meaningInContext": "померти"})
        result = self.lookup("kicked the bucket", mode="phrase")
        self.assertEqual(("phrase", "idiom"), (result["mode"], result["result"]["termType"]))
        self.assertIn("Що це: фраза", self.transport.prompt())

    def test_a_word_inside_an_idiom_reports_where_the_wider_phrase_stands(self):
        self.transport.replies.append({**ANSWER, "termType": "idiom", "expandedPhrase": "kicked the bucket", "meaningInContext": "померти"})
        result = self.lookup("bucket")
        text = plain_text(PARAGRAPH)
        expanded = result["expanded"]
        self.assertEqual("kicked the bucket", expanded["text"])
        self.assertEqual("kicked the bucket", text[expanded["start"]:expanded["end"]])
        self.transport.replies.append({**ANSWER, "termType": "phrasal_verb", "expandedPhrase": "an invented phrase"})
        self.assertIsNone(self.lookup("care")["expanded"])  # not found around the word: no range

    def test_the_second_identical_lookup_is_free(self):
        first = self.lookup("bucket")
        second = self.lookup("bucket")
        self.assertEqual(("cache", True), (second["source"], second["cached"]))
        self.assertEqual(first["result"], second["result"])
        self.assertEqual((1, 1), (len(self.transport.calls), len(self.usage_rows())))
        self.lookup("care")  # another word: a new call
        self.assertEqual(2, len(self.transport.calls))

    def test_the_cache_is_per_sentence_and_per_model(self):
        self.lookup("Then")
        self.storage.update_paragraph(self.second_id, "x", False)
        self.lookup("words", paragraph=self.second_id)
        self.assertEqual(2, len(self.transport.calls))
        self.storage.update_project(self.project_id, {"aiConfiguration": {"dictionary": {"model": "other-model"}}})
        again = self.lookup("Then")
        self.assertEqual(("model", "other-model"), (again["source"], again["model"]))
        self.assertEqual(3, len(self.transport.calls))

    def test_the_cache_key_has_no_book_text(self):
        self.lookup("bucket")
        with sqlite3.connect(self.database_path) as connection:
            keys = connection.execute("SELECT term_key, sentence_hash, model, mode FROM dictionary_cache").fetchall()
        self.assertEqual([("bucket", keys[0][1], PRICED, "word")], keys)
        self.assertNotIn("Smith", keys[0][1])
        self.assertEqual(32, len(keys[0][1]))


class SentenceFieldsTests(DictionaryFixture):
    def check(self, result, term):
        sentence = result["sentence"]
        self.assertEqual(term, sentence[result["termStart"]:result["termEnd"]])

    def test_the_answer_carries_the_sentence_and_where_the_term_stands(self):
        result = self.lookup("bucket")
        self.assertEqual('He said, "Dr. Smith kicked the bucket."', result["sentence"])
        self.check(result, "bucket")
        self.assertEqual((result["sentence"].index("bucket"), result["sentence"].index("bucket") + 6), (result["termStart"], result["termEnd"]))

    def test_a_sentence_in_the_middle_of_the_paragraph_and_a_phrase(self):
        result = self.lookup("didn’t stay", mode="phrase")
        self.assertTrue(result["sentence"].startswith("The well-known man"))
        self.assertTrue(result["sentence"].endswith("Then he left."))  # etc. is an abbreviation: it does not end the sentence
        self.check(result, "didn’t stay")

    def test_the_sentence_is_the_whole_paragraph_when_the_term_crosses_a_boundary(self):
        text = plain_text(PARAGRAPH)
        a, b = text.index("bucket"), text.index("She did") + 3
        result = self.service.lookup({"projectId": self.project_id, "paragraphId": self.paragraph_id, "text": text[a:b],
                                      "offsetStart": a, "offsetEnd": b, "mode": "phrase"})
        self.assertEqual(text, result["sentence"])
        self.check(result, text[a:b])

    def test_a_one_sentence_paragraph(self):
        result = self.lookup("words", paragraph=self.second_id)
        self.assertEqual("Plain italic words & more.", result["sentence"])
        self.check(result, "words")

    def test_cached_and_glossary_answers_have_them_too_and_nothing_is_stored_or_logged(self):
        self.lookup("bucket")
        cached = self.lookup("bucket")
        self.assertEqual("cache", cached["source"])
        self.check(cached, "bucket")
        with sqlite3.connect(self.database_path) as connection:
            stored = " ".join(row[0] for row in connection.execute("SELECT response FROM dictionary_cache"))
        self.assertNotIn("sentence", stored)
        self.assertNotIn("termStart", stored)
        self.assertNotIn("Smith", stored)
        self.use_glossary = True
        self.storage.create_glossary_entry({"source": "care", "target": "турбота"})
        glossary = self.lookup("care")
        self.assertEqual("glossary", glossary["source"])
        self.check(glossary, "care")
        with self.assertLogs(level=logging.INFO) as logs:
            self.lookup("bucket")
        self.assertNotIn("Smith", "\n".join(logs.output))
        self.assertNotIn("termStart", "\n".join(logs.output))


class ValidationTests(DictionaryFixture):
    def test_invalid_json_is_repeated_once_and_both_calls_are_billed(self):
        self.transport.replies = ["Sorry, here you go: not json", ANSWER]
        result = self.lookup("bucket")
        self.assertEqual("model", result["source"])
        self.assertEqual(2, len(self.transport.calls))
        self.assertIn("не була валідним JSON", self.transport.prompt(1))
        self.assertEqual(2, len(self.usage_rows()))

    def test_a_schema_violation_counts_as_invalid(self):
        bad = {**ANSWER, "translations": []}
        self.transport.replies = [bad, {**ANSWER, "termType": "sentence"}, ANSWER]
        with self.assertRaises(DictionaryError) as raised:
            self.lookup("bucket")
        self.assertEqual((502, "dictionary_invalid_response"), (raised.exception.http_status, raised.exception.code))
        self.assertEqual(2, len(self.transport.calls))  # one retry only
        self.assertEqual(2, len(self.usage_rows()))
        self.assertEqual(0, len(self.storage.list_dictionary_cache("bucket", "x", PRICED)))

    def test_json_in_a_code_fence_and_long_lists_are_accepted_and_trimmed(self):
        many = {**ANSWER, "translations": [{"text": f"v{i}"} for i in range(8)], "examples": [{"en": "a", "uk": "б"}] * 4}
        self.transport.replies = ["```json\n" + json.dumps(many) + "\n```"]
        result = self.lookup("bucket")["result"]
        self.assertEqual((5, 2), (len(result["translations"]), len(result["examples"])))

    def test_a_model_error_is_reported_and_nothing_is_cached(self):
        with patch.object(ClaudeProvider, "complete", side_effect=ValueError("Claude тимчасово обмежив кількість запитів")):
            with self.assertRaises(DictionaryError) as raised:
                self.lookup("bucket")
        self.assertEqual((502, "dictionary_model_error"), (raised.exception.http_status, raised.exception.code))
        self.assertIn("Claude тимчасово", str(raised.exception))

    def test_bad_requests(self):
        base = {"projectId": self.project_id, "paragraphId": self.paragraph_id, "text": "bucket", "offsetStart": 0, "offsetEnd": 6, "mode": "word"}
        for change in ({"mode": "x"}, {"offsetEnd": 0}, {"offsetStart": -1}, {"offsetStart": True}, {"text": 5}, {"projectId": None}):
            with self.subTest(change=change), self.assertRaises(DictionaryError) as raised:
                self.service.lookup({**base, **change})
            self.assertEqual(400, raised.exception.http_status)
        with self.assertRaises(DictionaryError) as raised:
            self.service.lookup({**base, "paragraphId": "nope"})
        self.assertEqual(404, raised.exception.http_status)
        other = self.storage.create_project({"title": "Other"})["projectId"]
        with self.assertRaises(DictionaryError) as raised:
            self.service.lookup({**base, "projectId": other})
        self.assertEqual(404, raised.exception.http_status)

    def test_a_long_phrase_is_refused_with_a_clear_message(self):
        text = plain_text(PARAGRAPH)
        long_text = text[:text.index("care") + 4]
        with self.assertRaises(DictionaryError) as raised:
            self.service.lookup({"projectId": self.project_id, "paragraphId": self.paragraph_id, "text": long_text,
                                 "offsetStart": 0, "offsetEnd": len(long_text), "mode": "phrase"})
        self.assertEqual("Виділіть коротшу фразу (до 8 слів).", str(raised.exception))
        self.assertEqual(0, len(self.transport.calls))

    def test_stale_offsets_are_corrected_by_the_text_or_refused(self):
        text = plain_text(PARAGRAPH)
        start = text.index("bucket")
        result = self.service.lookup({"projectId": self.project_id, "paragraphId": self.paragraph_id, "text": "bucket",
                                      "offsetStart": start + 7, "offsetEnd": start + 13, "mode": "word"})
        self.assertEqual(start, result["selection"]["start"])
        with self.assertRaises(DictionaryError) as raised:
            self.service.lookup({"projectId": self.project_id, "paragraphId": self.paragraph_id, "text": "missingword",
                                 "offsetStart": 0, "offsetEnd": 11, "mode": "word"})
        self.assertEqual(409, raised.exception.http_status)

    def test_a_selection_without_a_word_is_refused(self):
        with self.assertRaises(DictionaryError) as raised:
            self.service.lookup({"projectId": self.project_id, "paragraphId": self.paragraph_id, "text": ', "',
                                 "offsetStart": 7, "offsetEnd": 10, "mode": "word"})
        self.assertEqual("dictionary_no_word", raised.exception.code)


class WordShapeTests(DictionaryFixture):
    def test_apostrophes_and_hyphens_make_one_word(self):
        for needle in ("didn’t", "well-known", "o'clock"):
            with self.subTest(needle=needle):
                self.transport.replies.append({**ANSWER, "term": needle})
                result = self.lookup(needle)
                self.assertEqual((needle, "word"), (result["term"], result["mode"]))
        # a stray tap that includes punctuation is trimmed to the words
        self.assertEqual("Smith", self.lookup("Smith ")["term"])

    def test_curly_and_straight_apostrophes_share_the_cache(self):
        self.storage.update_paragraph(self.second_id, "", False)
        self.lookup("didn’t")
        text = plain_text(PARAGRAPH).replace("didn’t", "didn't")
        with patch.object(self.storage, "paragraph_lookup_context", return_value={
                "paragraphId": self.paragraph_id, "chapterId": self.chapter_id, "projectId": self.project_id,
                "originalText": text, "translationText": None}):
            second = self.lookup_straight(text)
        self.assertEqual("cache", second["source"])

    def lookup_straight(self, text):
        start = text.index("didn't")
        return self.service.lookup({"projectId": self.project_id, "paragraphId": self.paragraph_id, "text": "didn't",
                                    "offsetStart": start, "offsetEnd": start + 6, "mode": "word"})

    def test_offsets_count_in_the_text_the_browser_shows(self):
        self.assertEqual("Plain italic words & more.", plain_text(self.storage.paragraph_lookup_context(self.second_id)["originalText"]))
        result = self.lookup("words", paragraph=self.second_id)
        self.assertEqual("words", result["selection"]["term"])
        self.assertIn("Plain italic ⟦words⟧ & more.", self.transport.prompt())
        self.assertNotIn("Увесь абзац", self.transport.prompt())  # sentence == paragraph: sent once

    def test_the_sentence_is_the_whole_paragraph_when_the_term_crosses_a_boundary(self):
        text = plain_text(PARAGRAPH)
        phrase = text[text.index("bucket"):text.index("She did") + 3]
        self.service.lookup({"projectId": self.project_id, "paragraphId": self.paragraph_id, "text": phrase,
                             "offsetStart": text.index("bucket"), "offsetEnd": text.index("She did") + 3, "mode": "phrase"})
        self.assertIn(PARAGRAPH.replace("bucket", "⟦bucket", 1).split("She")[0][:20], self.transport.prompt())
        self.assertNotIn("Увесь абзац", self.transport.prompt())


class GlossaryTests(DictionaryFixture):
    def setUp(self):
        super().setUp()
        self.use_glossary = True
        self.court = self.storage.create_glossary_entry({"source": "Justice's Court", "target": "Двір Правосуддя", "note": "суд"})
        self.storage.create_glossary_entry({"source": "Bucket", "target": "Відро (термін)"})
        self.storage.update_paragraph(self.second_id, "", False)

    def with_court_paragraph(self):
        self.storage.update_paragraph(self.paragraph_id, "x", False)
        context = self.storage.paragraph_lookup_context(self.paragraph_id)
        return patch.object(self.storage, "paragraph_lookup_context", return_value={**context, "originalText": "They fled Justice’s court at dawn."})

    def test_a_glossary_hit_answers_without_the_model(self):
        result = self.lookup("bucket")
        self.assertEqual(("glossary", None, False), (result["source"], result["result"], result["cached"]))
        self.assertEqual([("Bucket", "Відро (термін)")], [(g["source"], g["target"]) for g in result["glossary"]])
        self.assertEqual((0, 0), (len(self.transport.calls), len(self.usage_rows())))

    def test_a_word_inside_a_longer_term_shows_the_longest_term_and_curly_apostrophes_match(self):
        with self.with_court_paragraph():
            result = self.lookup("Justice")
        self.assertEqual("glossary", result["source"])
        self.assertEqual([("Justice's Court", "Двір Правосуддя", "суд")], [(g["source"], g["target"], g["note"]) for g in result["glossary"]])
        self.assertEqual(0, len(self.transport.calls))

    def test_a_phrase_that_only_contains_a_term_still_asks_the_model_and_lists_the_term(self):
        result = self.lookup("kicked the bucket", mode="phrase")
        self.assertEqual("model", result["source"])
        self.assertEqual({"Bucket"}, {g["source"] for g in result["glossary"]})
        self.assertEqual(1, len(self.transport.calls))

    def test_more_values_go_to_the_model_even_for_a_glossary_word(self):
        result = self.lookup("bucket", mode="more")
        self.assertEqual(("model", "more"), (result["source"], result["mode"]))
        self.assertEqual(1, len(self.transport.calls))

    def test_inactive_entries_and_other_words_do_not_match(self):
        self.storage.update_glossary_entry(self.storage.list_glossary()[0]["glossaryEntryId"], {"source": "Bucket", "target": "x", "active": False})
        result = self.lookup("care")
        self.assertEqual(("model", []), (result["source"], result["glossary"]))


class MoreTests(DictionaryFixture):
    def test_more_values_exclude_what_was_shown_and_are_limited_to_three(self):
        self.lookup("bucket")
        for number in (1, 2, 3):
            self.transport.replies.append({**ANSWER, "translations": [{"text": f"нове{number}"}]})
            result = self.lookup("bucket", mode="more")
            self.assertEqual(3 - number, result["moreRemaining"])
        self.assertIn("відро", self.transport.prompt(1))  # shown meanings are excluded
        self.assertIn("нове1", self.transport.prompt(2))
        self.assertIn("ІНШІ значення", self.transport.prompt(3))
        with self.assertRaises(DictionaryError) as raised:
            self.lookup("bucket", mode="more")
        self.assertEqual((429, "dictionary_more_limit"), (raised.exception.http_status, raised.exception.code))
        self.assertEqual(4, len(self.transport.calls))
        self.assertEqual(4, len(self.usage_rows()))
        self.assertEqual(0, self.lookup("bucket")["moreRemaining"])  # the first answer is still cached

    def test_the_limit_is_per_word(self):
        for _ in range(3):
            self.lookup("bucket", mode="more")
        self.assertEqual(2, self.lookup("care", mode="more")["moreRemaining"])


class ConnectionTests(DictionaryFixture):
    def test_no_connection(self):
        self.storage.delete_integration_connection(self.connection["connectionId"])
        with self.assertRaises(DictionaryError) as raised:
            self.lookup("bucket")
        self.assertEqual((409, "dictionary_no_connection"), (raised.exception.http_status, raised.exception.code))
        self.assertEqual(0, len(self.transport.calls))

    def test_a_connection_that_is_not_checked_is_not_used(self):
        self.storage.update_integration_connection_status(self.connection["connectionId"], "error", "x", "x", {})
        with self.assertRaises(DictionaryError) as raised:
            self.lookup("bucket")
        self.assertEqual("dictionary_no_connection", raised.exception.code)

    def test_a_configured_connection_must_be_ready(self):
        self.storage.update_project(self.project_id, {"aiConfiguration": {"dictionary": {"connectionId": "nope"}}})
        with self.assertRaises(DictionaryError) as raised:
            self.lookup("bucket")
        self.assertEqual("dictionary_connection_unavailable", raised.exception.code)

    def test_deepl_is_never_used(self):
        self.storage.delete_integration_connection(self.connection["connectionId"])
        deepl = self.storage.create_integration_connection("deepl", "DeepL", b"x")
        self.storage.update_integration_connection_status(deepl["connectionId"], "connected", "ok", "ok", {})
        with self.assertRaises(DictionaryError) as raised:
            self.lookup("bucket")
        self.assertEqual("dictionary_no_connection", raised.exception.code)

    def test_a_glossary_hit_needs_no_connection(self):
        self.use_glossary = True
        self.storage.create_glossary_entry({"source": "bucket", "target": "відро"})
        self.storage.delete_integration_connection(self.connection["connectionId"])
        self.assertEqual("glossary", self.lookup("bucket")["source"])

    def test_the_default_model_is_the_cheapest_priced_one_of_the_connection(self):
        self.storage.save_model_prices([
            {"model": "cheap-fast", "inputPerMTok": 0.5, "outputPerMTok": 2.0},
            {"model": "mid", "inputPerMTok": 2.0, "outputPerMTok": 10.0},
        ])
        self.models = [{"id": "mid"}, {"id": "cheap-fast"}, {"id": "unpriced-new"}]
        result = self.lookup("bucket")
        self.assertEqual("cheap-fast", result["model"])
        self.assertEqual("cheap-fast", self.transport.calls[0]["payload"]["model"])
        self.assertIsNone(result["priceWarning"])

    def test_the_chosen_model_wins_and_a_model_without_a_price_is_flagged(self):
        self.storage.update_project(self.project_id, {"aiConfiguration": {"dictionary": {"connectionId": self.connection["connectionId"], "model": "model-no-price"}}})
        result = self.lookup("bucket")
        self.assertEqual("model-no-price", result["model"])
        self.assertIn("не задано ціну", result["priceWarning"])
        self.assertEqual("model-no-price", self.usage_rows()[0]["model"])

    def test_without_any_price_the_providers_default_model_is_used_when_the_list_fails(self):
        self.storage.save_model_prices([])
        self.service = DictionaryService(self.storage, self.vault, ProviderRegistry([ClaudeProvider(self.transport)]),
                                         lambda connection_id: (_ for _ in ()).throw(RuntimeError("down")), lambda project: [])
        result = self.lookup("bucket")
        self.assertEqual(ClaudeProvider.DEFAULT_TRANSLATION_MODEL, result["model"])


class PrivacyAndStorageTests(DictionaryFixture):
    def test_logs_carry_lengths_and_tokens_but_never_book_text(self):
        with self.assertLogs(level=logging.INFO) as logs:
            self.lookup("bucket")
            self.lookup("bucket")
        joined = "\n".join(logs.output)
        self.assertIn("termChars=6", joined)
        self.assertIn("inputTokens=400", joined)
        for secret in ("bucket", "Smith", "kicked", "Доктор", "She did not care"):
            self.assertNotIn(secret, joined)

    def test_the_migration_is_idempotent_and_rebuilds_an_old_usage_table(self):
        self.lookup("bucket")
        with sqlite3.connect(self.database_path) as connection:
            connection.executescript("""
                DROP TABLE dictionary_cache;
                ALTER TABLE translation_usage RENAME TO usage_keep;
                CREATE TABLE translation_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL, chapter_id TEXT, engine TEXT NOT NULL, model TEXT NOT NULL,
                    kind TEXT NOT NULL CHECK(kind IN ('translate', 'retry', 'qa', 'analysis', 'chat')),
                    input_tokens INTEGER NOT NULL DEFAULT 0, output_tokens INTEGER NOT NULL DEFAULT 0,
                    cache_read_tokens INTEGER NOT NULL DEFAULT 0, cache_write_tokens INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL, queue_id TEXT, source_chars INTEGER);
                INSERT INTO translation_usage SELECT * FROM usage_keep WHERE kind != 'dictionary';
                DROP TABLE usage_keep;
            """)
            connection.execute("INSERT INTO translation_usage(project_id, engine, model, kind, input_tokens, created_at) VALUES (?, 'claude', 'm', 'chat', 5, 'now')", (self.project_id,))
        for _ in range(3):
            self.storage = Storage(self.database_path)
        self.assertEqual([("chat", 5)], [(r["kind"], r["inputTokens"]) for r in self.storage.list_translation_usage(self.project_id)])
        self.storage.record_translation_usage(self.project_id, None, "claude", "m", "dictionary", USAGE)  # accepted now
        self.assertEqual(2, len(self.storage.list_translation_usage(self.project_id)))
        self.storage.put_dictionary_cache("a", "b", "m", "word", {"x": 1})
        self.assertEqual({"x": 1}, Storage(self.database_path).get_dictionary_cache("a", "b", "m", "word"))

    def test_the_provider_complete_call_keeps_the_limits(self):
        self.lookup("bucket")
        call = self.transport.calls[0]
        self.assertEqual(1500, call["payload"]["max_tokens"])
        self.assertEqual(45.0, call["timeout"])


class FakeHandler:
    def __init__(self, payload=None):
        self.payload = payload

    def read_json(self):
        return self.payload


class ApiTests(DictionaryFixture):
    def test_the_route_and_its_error_mapping(self):
        text = plain_text(PARAGRAPH)
        start = text.index("care")
        payload = {"projectId": self.project_id, "paragraphId": self.paragraph_id, "text": "care", "offsetStart": start, "offsetEnd": start + 4, "mode": "word"}
        with patch.object(server, "dictionary_service", self.service):
            status, body = server.WorkbenchHandler.handle_api(FakeHandler(payload), "POST", "/api/dictionary/lookup")
            self.assertEqual((200, "відро"), (status, body["result"]["meaningInContext"]))
            with self.assertRaises(DictionaryError):
                server.WorkbenchHandler.handle_api(FakeHandler({**payload, "mode": "bad"}), "POST", "/api/dictionary/lookup")

    def test_the_dictionary_model_setting_is_validated(self):
        connection_id = self.connection["connectionId"]
        for bad in ("x", {"model": 5}, {"extra": 1}, {"model": "m" * 101}):
            self.assertIsNotNone(server.validate_project_ai_configuration({"aiConfiguration": {"dictionary": bad}}, self.storage.list_integration_connections()), bad)
        self.assertIsNotNone(server.validate_project_ai_configuration({"aiConfiguration": {"dictionary": {"connectionId": "unknown"}}}, self.storage.list_integration_connections()))
        self.assertIsNone(server.validate_project_ai_configuration({"aiConfiguration": {"dictionary": {"connectionId": connection_id, "model": "m"}}}, self.storage.list_integration_connections()))
        self.assertIsNone(server.validate_project_ai_configuration({"aiConfiguration": {"dictionary": {"connectionId": None, "model": None}}}, self.storage.list_integration_connections()))


if __name__ == "__main__":
    unittest.main()
