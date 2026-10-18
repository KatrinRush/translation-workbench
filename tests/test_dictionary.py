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
from backend.dictionary_service import DictionaryError, DictionaryService, normalize_variant, plain_text, split_sentences
from backend.integrations.credentials import CredentialVault
from backend.integrations.providers.claude import ClaudeProvider
from backend.integrations.registry import ProviderRegistry
from backend.storage import Storage
from backend.usage import project_report

USAGE = {"input_tokens": 400, "output_tokens": 120, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}
PRICED = "claude-sonnet-5-5"

SENSE_BUCKET = {"gloss": "відро", "pos": "іменник", "translations": [{"text": "відро", "register": "нейтральне"}, {"text": "цебро", "register": "застаріле"}],
                "examples": [{"en": "A bucket of water.", "uk": "Відро води."}]}
SENSE_LIST = {"gloss": "перелік бажань", "pos": "іменник", "translations": [{"text": "список бажань", "register": "розмовне"}, {"text": "перелік", "register": "нейтральне"}],
              "examples": []}
FULL_BUCKET = {"term": "bucket", "lemma": "bucket", "pos": "іменник", "termType": "word", "expandedPhrase": None,
               "senses": [SENSE_BUCKET, SENSE_LIST], "senseId": "s1"}
ANSWER = FULL_BUCKET  # the first answer of an unknown lemma: the inventory and the chosen sense


def generic_full(term):
    return {"term": term, "lemma": term.lower(), "pos": "іменник", "termType": "phrase" if " " in term else "word", "expandedPhrase": None,
            "senses": [{"gloss": f"значення {term}", "pos": "іменник", "translations": [{"text": f"{term}-а", "register": "нейтральне"}], "examples": []}],
            "senseId": "s1"}


PARAGRAPH = 'He said, "Dr. Smith kicked the bucket." She did not care. The well-known man didn’t stay till 5 o\'clock, Mr. Brown noted etc. Then he left.'


SYSTEM_MARKERS = {"full": "Дай повний перелік", "pick": "Тобі дано перелік значень", "extend": "РІДКІСНИХ", "rendering": "перевірити, як слово чи фразу",
                  "resolve": "пронумерованого абзацу"}


class Transport:
    """Answers by the kind of the request (the system prompt tells): replies[kind] is a queue, else a default."""

    def __init__(self):
        self.replies = {kind: [] for kind in SYSTEM_MARKERS}
        self.calls = []

    @staticmethod
    def kind_of(payload):
        system = payload["system"][0]["text"]
        return next(kind for kind, marker in SYSTEM_MARKERS.items() if marker in system)

    def default(self, kind, prompt):
        term = (prompt.split("Термін: ")[1].split("\n")[0] if "Термін: " in prompt else "")
        if kind == "full":
            return FULL_BUCKET if term == "bucket" else generic_full(term)
        if kind == "pick":
            return {"term": term, "lemma": term.lower(), "pos": "іменник", "termType": "word", "expandedPhrase": None, "senseId": "s1", "newSense": None}
        if kind == "extend":
            return {"senses": [{"gloss": f"рідкісне {len(self.calls)}", "translations": [{"text": f"рідкісне-{len(self.calls)}"}]}]}
        if kind == "rendering":
            return {"rendering": "відро", "reason": None, "issues": []}
        return {"items": []}

    def post(self, url, headers, body, timeout):
        payload = json.loads(body)
        kind = self.kind_of(payload)
        prompt = payload["messages"][0]["content"]
        self.calls.append({"payload": payload, "timeout": timeout, "kind": kind})
        queue = self.replies[kind]
        reply = queue.pop(0) if queue else self.default(kind, prompt)
        text = reply if isinstance(reply, str) else json.dumps(reply, ensure_ascii=False)
        return 200, json.dumps({"model": payload["model"], "stop_reason": "end_turn", "content": [{"type": "text", "text": text}], "usage": USAGE}).encode()

    def prompt(self, index=-1):
        return self.calls[index]["payload"]["messages"][0]["content"]

    def kinds(self):
        return [call["kind"] for call in self.calls]


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
        self.assertNotIn("Доктор Сміт віддав Богу душу", prompt)  # the neutral part never sees the translation
        self.assertNotIn("Поточний переклад", prompt)
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
        self.transport.replies["full"].append({**generic_full("kicked the bucket"), "termType": "idiom", "lemma": "kick the bucket",
                                               "senses": [{"gloss": "померти", "translations": [{"text": "віддати Богу душу"}]}]})
        result = self.lookup("kicked the bucket", mode="phrase")
        self.assertEqual(("phrase", "idiom"), (result["mode"], result["result"]["termType"]))
        self.assertIn("Що це: фраза", self.transport.prompt())

    def test_a_word_inside_an_idiom_reports_where_the_wider_phrase_stands(self):
        self.transport.replies["full"].append({**FULL_BUCKET, "termType": "idiom", "expandedPhrase": "kicked the bucket"})
        result = self.lookup("bucket")
        text = plain_text(PARAGRAPH)
        expanded = result["expanded"]
        self.assertEqual("kicked the bucket", expanded["text"])
        self.assertEqual("kicked the bucket", text[expanded["start"]:expanded["end"]])
        self.transport.replies["full"].append({**generic_full("care"), "termType": "phrasal_verb", "expandedPhrase": "an invented phrase"})
        self.assertIsNone(self.lookup("care")["expanded"])  # not found around the word: no range

    def test_the_second_identical_lookup_is_free(self):
        first = self.lookup("bucket")
        second = self.lookup("bucket")
        self.assertEqual(("cache", True), (second["source"], second["cached"]))
        self.assertEqual(first["result"], second["result"])
        self.assertEqual((1, 1), (len(self.transport.calls), len(self.usage_rows())))
        self.lookup("care")  # another word: a new call
        self.assertEqual(2, len(self.transport.calls))

    def test_the_sense_pick_is_per_sentence_the_inventory_is_shared_and_the_model_does_not_matter(self):
        self.lookup("the")                      # an unknown lemma: the full inventory and the pick
        self.assertEqual(["full"], self.transport.kinds())
        self.lookup("The")                      # another sentence, the same lemma: only the pick, against the stored inventory
        self.assertEqual(["full", "pick"], self.transport.kinds())
        self.assertIn("Відомі значення", self.transport.prompt())
        with sqlite3.connect(self.database_path) as connection:
            self.assertEqual(1, connection.execute("SELECT COUNT(*) FROM dictionary_senses").fetchone()[0])
            self.assertEqual(2, connection.execute("SELECT COUNT(*) FROM dictionary_picks").fetchone()[0])
        self.storage.update_project(self.project_id, {"aiConfiguration": {"dictionary": {"model": "other-model"}}})
        again = self.lookup("the")              # another model: the sense does not change with it, nothing is asked
        self.assertEqual(("cache", "other-model"), (again["source"], again["model"]))
        self.assertEqual(2, len(self.transport.calls))

    def test_the_cache_keys_have_no_book_text(self):
        self.lookup("bucket")
        with sqlite3.connect(self.database_path) as connection:
            picks = connection.execute("SELECT term_key, sentence_hash, inventory_version FROM dictionary_picks").fetchall()
            lemmas = connection.execute("SELECT lemma_key FROM dictionary_senses").fetchall()
        self.assertEqual([("bucket", picks[0][1], 1)], picks)
        self.assertEqual([("bucket",)], lemmas)
        self.assertNotIn("Smith", picks[0][1])
        self.assertEqual(32, len(picks[0][1]))


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
            stored = " ".join(row[0] for row in connection.execute("SELECT response FROM dictionary_picks UNION ALL SELECT inventory FROM dictionary_senses"))
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
        self.transport.replies["full"] = ["Sorry, here you go: not json", ANSWER]
        result = self.lookup("bucket")
        self.assertEqual("model", result["source"])
        self.assertEqual(2, len(self.transport.calls))
        self.assertIn("не була валідним JSON", self.transport.prompt(1))
        self.assertEqual(2, len(self.usage_rows()))

    def test_a_schema_violation_counts_as_invalid(self):
        bad = {**ANSWER, "senses": []}
        self.transport.replies["full"] = [bad, {**ANSWER, "termType": "sentence"}, ANSWER]
        with self.assertRaises(DictionaryError) as raised:
            self.lookup("bucket")
        self.assertEqual((502, "dictionary_invalid_response"), (raised.exception.http_status, raised.exception.code))
        self.assertEqual(2, len(self.transport.calls))  # one retry only
        self.assertEqual(2, len(self.usage_rows()))
        self.assertIsNone(self.storage.get_dictionary_senses("bucket"))  # nothing is stored for a rejected answer

    def test_json_in_a_code_fence_and_long_lists_are_accepted_and_trimmed(self):
        sense = lambda i: {"gloss": f"g{i}", "translations": [{"text": f"v{i}-{j}"} for j in range(8)], "examples": [{"en": "a", "uk": "б"}] * 4}
        many = {**ANSWER, "senses": [sense(i) for i in range(10)], "senseId": "s1"}
        self.transport.replies["full"] = ["```json\n" + json.dumps(many) + "\n```"]
        result = self.lookup("bucket")["result"]
        self.assertEqual((6, 1, 7), (len(result["translations"]), len(result["examples"]), len(result["otherSenses"])))  # four equal examples are one

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
        self.assertEqual(["full", "extend"], self.transport.kinds())

    def test_inactive_entries_and_other_words_do_not_match(self):
        self.storage.update_glossary_entry(self.storage.list_glossary()[0]["glossaryEntryId"], {"source": "Bucket", "target": "x", "active": False})
        result = self.lookup("care")
        self.assertEqual(("model", []), (result["source"], result["glossary"]))


class MoreTests(DictionaryFixture):
    def test_more_values_are_appended_to_the_inventory_for_good_and_limited_to_three(self):
        self.lookup("bucket")
        for number in (1, 2, 3):
            self.transport.replies["extend"].append({"senses": [{"gloss": f"рідкісне {number}", "translations": [{"text": f"нове{number}"}]}]})
            result = self.lookup("bucket", mode="more")
            self.assertEqual(3 - number, result["moreRemaining"])
        self.assertIn("відро", self.transport.prompt(1))  # the shown meanings are excluded
        self.assertIn("рідкісне 1", self.transport.prompt(2))
        with self.assertRaises(DictionaryError) as raised:
            self.lookup("bucket", mode="more")
        self.assertEqual((429, "dictionary_more_limit"), (raised.exception.http_status, raised.exception.code))
        self.assertEqual(["full", "extend", "extend", "extend"], self.transport.kinds())
        self.assertEqual(4, len(self.usage_rows()))
        again = self.lookup("bucket")  # a plain lookup: free, and the added senses are there
        self.assertEqual((0, "cache"), (again["moreRemaining"], again["source"]))
        self.assertEqual(["перелік бажань", "рідкісне 1", "рідкісне 2", "рідкісне 3"], [item["gloss"] for item in again["result"]["otherSenses"]])

    def test_the_limit_is_per_word(self):
        for _ in range(3):
            self.lookup("bucket", mode="more")
        self.assertEqual(2, self.lookup("care", mode="more")["moreRemaining"])


# --- the neutral part: the same word, the same sense, the same answer -------------------------------------

THIRD = "Then the bucket rang. A bucket of water stood by the well."


class NeutralFixture(DictionaryFixture):
    def setUp(self):
        super().setUp()
        # two paragraphs with the word «bucket» and DIFFERENT translations of it
        self.storage.update_paragraph(self.paragraph_id, "Він сказав: «Доктор Сміт віддав Богу душу, коцюба».", False)

    def neutral(self, result):
        keep = ("lemma", "lemmaKey", "pos", "termType", "senseId", "meaningInContext", "translations", "otherSenses", "examples", "special")
        return {key: result["result"][key] for key in keep}


class NeutralTests(NeutralFixture):
    def test_the_neutral_part_never_sees_a_translation_and_is_the_same_for_every_paragraph(self):
        # the second paragraph holds the word too, translated differently
        self.storage.save_book_structure(self.project_id, "c.epub", "application/epub+zip", b"c", {"chapters": [
            {"title": "A", "elements": [{"type": "paragraph", "text": PARAGRAPH}]}, {"title": "B", "elements": [{"type": "paragraph", "text": THIRD}]}]})
        chapters = self.storage.get_book_structure(self.project_id)["chapters"]
        first, second = chapters[0]["elements"][0]["paragraphId"], chapters[1]["elements"][0]["paragraphId"]
        self.storage.update_paragraph(first, "Він сказав: «Доктор Сміт копнув кочергу».", False)
        self.storage.update_paragraph(second, "Тоді задзвеніла коцюба.", False)
        one = self.lookup("bucket", paragraph=first)
        two = self.lookup("bucket", paragraph=second)
        self.assertEqual(self.neutral(one), self.neutral(two))  # the same sense, the same blocks
        self.assertEqual(["full", "pick"], self.transport.kinds())
        for call in self.transport.calls:  # no call of the neutral part carried a translation
            self.assertNotIn("кочерг", json.dumps(call["payload"], ensure_ascii=False))
            self.assertNotIn("коцюб", json.dumps(call["payload"], ensure_ascii=False))
        self.assertNotIn("Поточний переклад", self.transport.prompt(0) + self.transport.prompt(1))

    def test_no_translation_variant_is_shown_twice_in_the_answer(self):
        # «відро» is in both senses; «Відро́» (stress, case) is the same variant
        self.transport.replies["full"].append({**FULL_BUCKET, "senses": [
            SENSE_BUCKET,
            {"gloss": "ємність для льоду", "translations": [{"text": "Відро́"}, {"text": "відерце"}, {"text": "цебро"}]},
            {"gloss": "список", "translations": [{"text": "відерце"}]},
        ]})
        result = self.lookup("bucket")["result"]
        shown = [item["text"] for item in result["translations"]] + [t["text"] for sense in result["otherSenses"] for t in sense["translations"]]
        keys = [normalize_variant(text) for text in shown]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(["відерце"], [t["text"] for t in result["otherSenses"][0]["translations"]])  # what is new in the sense
        self.assertEqual(1, len(result["otherSenses"]))  # «список» shares «відерце» with the sense above: one meaning told twice

    def test_every_variant_has_a_register(self):
        result = self.lookup("bucket")["result"]
        self.assertEqual(["нейтральне", "застаріле"], [item["register"] for item in result["translations"]])
        self.transport.replies["full"].append({**generic_full("care"), "senses": [{"gloss": "g", "translations": [{"text": "турбота", "register": None}]}]})
        self.assertEqual("нейтральне", self.lookup("care")["result"]["translations"][0]["register"])

    def test_the_lemma_is_learned_from_the_first_answer_and_a_known_one_keeps_its_inventory(self):
        self.transport.replies["full"].append({**generic_full("kicked"), "lemma": "kick", "senses": [{"gloss": "копнути", "translations": [{"text": "копнути"}]}]})
        self.lookup("kicked")
        self.assertEqual("kick", self.storage.lemma_for_surface("kicked"))
        stored = self.storage.get_dictionary_senses("kick")["senses"]
        self.assertEqual(["копнути"], [sense["gloss"] for sense in stored])
        # a form never seen before whose lemma turns out to be «kick» (here «Smith» stands in for it): the stored inventory is
        # kept, the inventory of the answer is dropped, and only the sense is picked against the stored one
        self.transport.replies["full"].append({**generic_full("Smith"), "lemma": "kick", "senses": [{"gloss": "зовсім інше", "translations": [{"text": "інше"}]}]})
        result = self.lookup("Smith")
        self.assertEqual(["full", "full", "pick"], self.transport.kinds())
        self.assertIn("копнути", self.transport.prompt())
        self.assertEqual(stored, self.storage.get_dictionary_senses("kick")["senses"])
        self.assertEqual("kick", self.storage.lemma_for_surface("smith"))
        self.assertEqual("копнути", result["result"]["meaningInContext"])


class SpecialSenseTests(NeutralFixture):
    NEW = {"gloss": "бойовий пес-сторож у цій книжці", "pos": "іменник", "translations": [{"text": "відро-вартовий", "register": "нейтральне"}], "examples": []}

    def test_none_of_the_senses_fits_adds_the_books_own_meaning_to_the_inventory(self):
        self.lookup("bucket")  # the inventory: two ordinary senses
        self.transport.replies["pick"].append({"term": "care", "lemma": "bucket", "pos": "іменник", "termType": "word", "expandedPhrase": None,
                                               "senseId": "none", "newSense": self.NEW})
        self.storage.set_surface("care", "bucket")  # «care» is a form of this lemma here
        result = self.lookup("care")
        self.assertEqual(["full", "pick"], self.transport.kinds())
        self.assertTrue(result["result"]["special"])
        self.assertEqual("s3", result["result"]["senseId"])
        self.assertEqual(self.NEW["gloss"], result["result"]["meaningInContext"])  # not the nearest of the known senses
        inventory = self.storage.get_dictionary_senses("bucket")
        self.assertEqual(["s1", "s2", "s3"], [sense["id"] for sense in inventory["senses"]])
        self.assertTrue(inventory["senses"][2]["special"])
        self.assertEqual(1, inventory["version"])  # appending does not rebuild: the other picks stay valid
        self.assertIn("none", self.transport.calls[1]["payload"]["system"][0]["text"])  # the prompt offers the way out
        # the same sentence again: free, the same sense; another sentence now sees the new sense in the inventory
        again = self.lookup("care")
        self.assertEqual(("cache", "s3"), (again["source"], again["result"]["senseId"]))
        self.storage.set_surface("smith", "bucket")  # another sentence, the same lemma: the pick sees the new sense
        self.lookup("Smith")
        self.assertIn("s3:", self.transport.prompt())
        self.assertIn("бойовий пес-сторож", self.transport.prompt())
        self.assertIn(self.NEW["gloss"], [sense["gloss"] for sense in self.lookup("care")["result"]["otherSenses"]] + [self.lookup("care")["result"]["meaningInContext"]])

    def test_a_new_sense_that_is_already_known_is_not_added_twice(self):
        self.lookup("bucket")
        self.storage.set_surface("care", "bucket")
        self.transport.replies["pick"].append({"term": "care", "lemma": "bucket", "pos": None, "termType": "word", "expandedPhrase": None,
                                               "senseId": "none", "newSense": {**SENSE_BUCKET, "gloss": "Відро"}})
        result = self.lookup("care")
        self.assertEqual("s1", result["result"]["senseId"])
        self.assertEqual(2, len(self.storage.get_dictionary_senses("bucket")["senses"]))

    def test_none_without_a_described_sense_is_an_invalid_answer(self):
        self.lookup("bucket")
        self.storage.set_surface("care", "bucket")
        broken = {"term": "care", "lemma": "bucket", "termType": "word", "expandedPhrase": None, "senseId": "none", "newSense": None}
        self.transport.replies["pick"] = [broken, broken]
        with self.assertRaises(DictionaryError) as raised:
            self.lookup("care")
        self.assertEqual("dictionary_invalid_response", raised.exception.code)
        self.assertEqual(2, len(self.storage.get_dictionary_senses("bucket")["senses"]))


class RefreshTests(NeutralFixture):
    def test_refresh_rebuilds_the_inventory_and_drops_the_old_picks(self):
        self.lookup("the")
        self.lookup("The")  # another sentence, the same lemma: a pick against the stored inventory
        self.assertEqual(["full", "pick"], self.transport.kinds())
        self.transport.replies["full"].append({**generic_full("the"), "senses": [{"gloss": "новий артикль", "translations": [{"text": "бадейка"}]}]})
        text = plain_text(PARAGRAPH)
        start = text.index("the")
        refreshed = self.service.refresh_senses({"projectId": self.project_id, "paragraphId": self.paragraph_id, "text": "the",
                                                 "offsetStart": start, "offsetEnd": start + 3})
        self.assertEqual(("новий артикль", ["бадейка"]), (refreshed["result"]["meaningInContext"], [t["text"] for t in refreshed["result"]["translations"]]))
        inventory = self.storage.get_dictionary_senses("the")
        self.assertEqual((2, 0, ["s1"]), (inventory["version"], inventory["extended"], [s["id"] for s in inventory["senses"]]))
        # the pick made for the other sentence with the old inventory does not count any more: it is made again
        self.lookup("The")
        self.assertEqual(["full", "pick", "full", "pick"], self.transport.kinds())
        self.assertEqual("cache", self.lookup("the")["source"])  # the refreshed sentence is cached again


class RenderingTests(NeutralFixture):
    def rendering(self, needle="bucket", paragraph=None, **extra):
        paragraph_id = paragraph or self.paragraph_id
        result = self.lookup(needle, paragraph=paragraph_id)["result"]
        text = plain_text(self.storage.paragraph_lookup_context(paragraph_id)["originalText"])
        start = text.index(needle)
        return self.service.rendering({"projectId": self.project_id, "paragraphId": paragraph_id, "text": needle, "offsetStart": start,
                                       "offsetEnd": start + len(needle), "lemma": result["lemma"], "senseId": result["senseId"], **extra})

    def test_how_it_was_translated_here_comes_from_the_translation_and_sees_it(self):
        self.transport.replies["rendering"].append({"rendering": "коцюба", "reason": None, "issues": []})
        answer = self.rendering()
        self.assertEqual(("коцюба", "model"), (answer["rendering"], answer["source"]))
        prompt = self.transport.prompt()
        self.assertIn("Переклад абзацу: Він сказав: «Доктор Сміт віддав Богу душу, коцюба».", prompt)
        self.assertIn("відро", prompt)  # the dictionary's variants of the sense
        self.assertEqual(["full", "rendering"], self.transport.kinds())
        self.assertEqual(["dictionary", "dictionary"], [row["kind"] for row in self.usage_rows()])

    def test_a_reason_and_remarks_are_shown_only_when_there_is_one(self):
        self.transport.replies["rendering"].append({"rendering": "коцюба", "reason": "Немає очевидної причини.", "issues": ["Зауважень немає.", "", "  "]})
        answer = self.rendering()
        self.assertEqual((None, []), (answer["reason"], answer["issues"]))
        self.storage.update_paragraph(self.paragraph_id, "Він сказав: «Доктор Сміт віддав Богу душу, коцюба»!", False)
        self.transport.replies["rendering"].append({"rendering": "коцюба", "reason": "Каже вуличний хлопчисько: просте слово.",
                                                    "issues": ["Глосарій радить «кочерга»."]})
        answer = self.rendering()
        self.assertEqual(("Каже вуличний хлопчисько: просте слово.", ["Глосарій радить «кочерга»."]), (answer["reason"], answer["issues"]))

    def test_the_prompt_allows_no_remarks_and_names_the_real_grounds_only(self):
        self.use_glossary = True
        self.storage.create_glossary_entry({"source": "Smith", "target": "Сміт", "note": "завжди так"})
        self.storage.update_project_translation_rules(self.project_id, "Не вживай «коцюба».")
        self.rendering()
        system = self.transport.calls[-1]["payload"]["system"][0]["text"]
        self.assertIn("reason: null", system)
        self.assertIn("порожній список []", system)
        prompt = self.transport.prompt()
        self.assertIn("Глосарій у цьому абзаці: Smith → Сміт (завжди так)", prompt)
        self.assertIn("Правила проєкту: Не вживай «коцюба».", prompt)

    def test_without_a_translation_nothing_is_asked(self):
        self.storage.update_paragraph(self.paragraph_id, "", False)
        answer = self.rendering()
        self.assertEqual((False, None, "none"), (answer["hasTranslation"], answer["rendering"], answer["source"]))
        self.assertEqual(["full"], self.transport.kinds())

    def test_the_answer_is_cached_until_the_translation_changes(self):
        self.storage.update_paragraph(self.paragraph_id, "Він ударив ногою відро.", False)
        self.rendering()
        again = self.rendering()
        self.assertEqual("cache", again["source"])
        self.assertEqual(["full", "rendering"], self.transport.kinds())
        self.storage.update_paragraph(self.paragraph_id, "Інший переклад, відро.", False)
        changed = self.rendering()
        self.assertEqual("model", changed["source"])
        self.assertEqual(["full", "rendering", "rendering"], self.transport.kinds())
        self.assertEqual(1, len(self.storage.list_dictionary_renderings(self.project_id, "bucket")))

    def test_a_stale_sense_is_refused(self):
        self.lookup("bucket")
        text = plain_text(PARAGRAPH)
        start = text.index("bucket")
        with self.assertRaises(DictionaryError) as raised:
            self.service.rendering({"projectId": self.project_id, "paragraphId": self.paragraph_id, "text": "bucket", "offsetStart": start,
                                    "offsetEnd": start + 6, "lemma": "bucket", "senseId": "s9"})
        self.assertEqual("dictionary_stale", raised.exception.code)


class OtherChaptersTests(DictionaryFixture):
    def setUp(self):
        super().setUp()
        elements = [{"type": "paragraph", "text": f"The bucket number {i} stood there."} for i in range(1, 5)] + [{"type": "paragraph", "text": "No such thing."}]
        self.storage.save_book_structure(self.project_id, "d.epub", "application/epub+zip", b"d", {"chapters": [
            {"title": "Ch1", "elements": elements[:2]}, {"title": "Ch2", "elements": elements[2:]}]})
        chapters = self.storage.get_book_structure(self.project_id)["chapters"]
        self.ids = [e["paragraphId"] for chapter in chapters for e in chapter["elements"]]
        for paragraph_id, text in zip(self.ids, ("Відро стояло.", "Відерце стояло.", "Коцюба стояла.", "", "Нічого.")):
            self.storage.update_paragraph(paragraph_id, text, False)
        self.lookup("bucket", paragraph=self.ids[0])  # the inventory exists now

    def scan(self, resolve=False):
        data = {"projectId": self.project_id, "lemma": "bucket"}
        return self.service.resolve_occurrences(data) if resolve else self.service.occurrences(data)

    def test_the_scan_needs_no_model_and_groups_by_rendering_and_chapter(self):
        calls = len(self.transport.calls)
        report = self.scan()
        self.assertEqual(calls, len(self.transport.calls))
        self.assertEqual(4, report["total"])
        self.assertEqual(["відро"], [group["text"] for group in report["renderings"]])
        self.assertEqual(1, report["renderings"][0]["paragraphs"])
        self.assertEqual([("Ch1", 1)], [(c["title"], c["count"]) for c in report["renderings"][0]["chapters"]])
        self.assertEqual(3, report["unresolved"]["paragraphs"])  # «Відерце», «Коцюба» and the paragraph without a translation
        self.assertEqual(2, report["resolvable"])  # the last one has nothing to look at
        self.assertEqual([1, 2], [chapter["chapterIndex"] for chapter in report["unresolved"]["chapters"]])

    def test_a_stored_rendering_from_a_lookup_is_used_and_resolve_asks_once_for_the_rest(self):
        text = plain_text(self.storage.paragraph_lookup_context(self.ids[2])["originalText"])
        start = text.index("bucket")
        self.transport.replies["rendering"].append({"rendering": "коцюбу", "reason": None, "issues": []})
        result = self.lookup("bucket", paragraph=self.ids[2])["result"]
        self.service.rendering({"projectId": self.project_id, "paragraphId": self.ids[2], "text": "bucket", "offsetStart": start,
                               "offsetEnd": start + 6, "lemma": "bucket", "senseId": result["senseId"]})
        report = self.scan()
        self.assertEqual({"відро": 1, "коцюбу": 1}, {group["text"]: group["paragraphs"] for group in report["renderings"]})
        self.assertEqual(2, report["unresolved"]["paragraphs"])  # «Відерце» and the paragraph without a translation
        self.assertEqual(1, report["resolvable"])

    def test_resolve_is_one_request_limited_and_never_repeated_for_the_same_answer(self):
        self.storage.update_paragraph(self.ids[3], "Бочка стояла.", False)
        before = len(self.transport.calls)
        self.transport.replies["resolve"].append({"items": [{"n": 1, "rendering": "відерце"}, {"n": 2, "rendering": "коцюба"}, {"n": 3, "rendering": "бочка"}]})
        report = self.scan(resolve=True)
        self.assertEqual(before + 1, len(self.transport.calls))
        self.assertEqual("resolve", self.transport.kinds()[-1])
        self.assertIn("Бочка стояла.", self.transport.prompt())
        self.assertIn("бочка", [group["text"] for group in report["renderings"]])
        self.assertEqual("dictionary", self.usage_rows()[-1]["kind"])
        self.scan(resolve=True)
        self.assertEqual(before + 1, len(self.transport.calls))  # nothing left to ask

    def test_at_most_twenty_paragraphs_go_into_one_request(self):
        elements = [{"type": "paragraph", "text": f"A bucket {i}."} for i in range(30)]
        self.storage.save_book_structure(self.project_id, "e.epub", "application/epub+zip", b"e", {"chapters": [{"title": "Many", "elements": elements}]})
        for element in self.storage.get_book_structure(self.project_id)["chapters"][0]["elements"]:
            self.storage.update_paragraph(element["paragraphId"], "Щось інше.", False)
        self.transport.replies["resolve"].append({"items": []})
        report = self.scan(resolve=True)
        self.assertEqual(20, self.transport.prompt().count("Переклад абзацу:"))
        self.assertEqual(10, report["resolvable"])


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
                DROP TABLE IF EXISTS dictionary_cache;
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
        self.storage.put_dictionary_pick("a", "b", 1, {"x": 1})
        self.assertEqual({"x": 1, "inventoryVersion": 1}, Storage(self.database_path).get_dictionary_pick("a", "b"))

    def test_the_provider_complete_call_keeps_the_limits(self):
        self.lookup("bucket")
        call = self.transport.calls[0]
        self.assertEqual(1500, call["payload"]["max_tokens"])
        self.assertEqual(45.0, call["timeout"])


class PokerTests(DictionaryFixture):
    """«Як перекладено тут» finds a form that is there (chapter 14 of the book), and the inventory has no doubles."""

    HAND = "— Вони зв'яжуться зі мною пізніше, якщо буде потреба, — він недбало змахує рукою і хапає кочергу\ue000f1\ue000 біля каміна."
    SWING = "— Ти досі не їси, — містер Спрингтон повертається і хмуриться на мене, кочерга тепер ліниво гойдається в його руці."
    FULL = {"term": "poker", "lemma": "poker", "pos": "іменник", "termType": "word", "expandedPhrase": None, "senseId": "s1", "senses": [
        {"gloss": "залізний прут для вогню", "pos": "іменник", "translations": [{"text": "кочерга"}, {"text": "пушкар"}],
         "examples": [{"en": "He took the poker.", "uk": "Він узяв кочергу."}, {"en": "He took the poker.", "uk": "Він узяв кочергу."}]},
        {"gloss": "кочерга, інакше", "pos": "іменник", "translations": [{"text": "Кочерга"}, {"text": "коцюба"}], "examples": []},
        {"gloss": "карткова гра", "pos": "іменник", "translations": [{"text": "покер"}], "examples": []},
    ]}

    def setUp(self):
        super().setUp()
        self.storage.save_book_structure(self.project_id, "p.epub", "application/epub+zip", b"p", {"chapters": [{"title": "Ch14", "elements": [
            {"type": "paragraph", "text": "“They’ll contact me later if needed,” he waves a careless hand and grabs the poker by the fireplace."},
            {"type": "paragraph", "text": "“You’re still not eating,” Mr. Springton turns and frowns at me, poker swinging idly in his hand now."}]}]})
        self.hand, self.swing = [e["paragraphId"] for e in self.storage.get_book_structure(self.project_id)["chapters"][0]["elements"]]
        self.storage.update_paragraph(self.hand, self.HAND, False)
        self.storage.update_paragraph(self.swing, self.SWING, False)
        self.transport.replies["full"].append(self.FULL)

    def how(self, paragraph_id):
        result = self.lookup("poker", paragraph=paragraph_id)["result"]
        text = plain_text(self.storage.paragraph_lookup_context(paragraph_id)["originalText"])
        start = text.index("poker")
        return self.service.rendering({"projectId": self.project_id, "paragraphId": paragraph_id, "text": "poker", "offsetStart": start,
                                       "offsetEnd": start + 5, "lemma": "poker", "senseId": result["senseId"]})

    def test_the_inventory_has_one_sense_for_one_meaning_and_one_example(self):
        result = self.lookup("poker", paragraph=self.hand)["result"]
        self.assertEqual(["кочерга", "пушкар", "коцюба"], [item["text"] for item in result["translations"]])
        self.assertEqual(1, len(result["examples"]))
        self.assertEqual(["карткова гра"], [sense["gloss"] for sense in result["otherSenses"]])

    def test_a_form_in_the_translation_is_found_even_when_the_model_says_not_found(self):
        self.transport.replies["rendering"] += [{"rendering": None, "reason": None, "issues": []}] * 2
        for paragraph_id, expected in ((self.hand, "кочергу"), (self.swing, "кочерга")):
            answer = self.how(paragraph_id)
            self.assertEqual(expected, answer["rendering"])

    def test_the_word_the_model_names_must_stand_in_the_translation(self):
        self.transport.replies["rendering"].append({"rendering": "пушкар", "reason": None, "issues": []})
        self.assertEqual("кочергу", self.how(self.hand)["rendering"])  # «пушкар» is not there: the program's candidate

    def test_nothing_is_cached_for_a_not_found_and_it_is_asked_again(self):
        self.storage.update_paragraph(self.swing, "Містер Спрингтон мовчить.", False)
        self.transport.replies["rendering"] += [{"rendering": None, "reason": None, "issues": []}] * 2
        self.assertIsNone(self.how(self.swing)["rendering"])
        self.assertEqual("model", self.how(self.swing)["source"])

    def test_the_prompt_carries_every_sense_and_the_candidate(self):
        self.how(self.hand)
        prompt = self.transport.prompt()
        for needle in ("Інше значення: карткова гра; відповідники: покер", "Кандидат від програми (знайдено в перекладі): кочергу"):
            self.assertIn(needle, prompt)
        self.assertNotIn("\ue000", prompt)

    def test_a_word_she_used_becomes_a_known_rendering_even_when_the_inventory_lacks_it(self):
        self.storage.update_paragraph(self.swing, "Містер Спрингтон бере залізну пальницю.", False)
        self.transport.replies["rendering"].append({"rendering": "пальницю", "reason": None, "issues": []})
        self.assertEqual("пальницю", self.how(self.swing)["rendering"])
        self.assertEqual(["пальницю"], [item["text"] for item in self.storage.list_known_renderings([self.project_id], "poker")])
        extra = self.lookup("poker", paragraph=self.hand)["result"]["knownRenderings"]
        self.assertEqual(["пальницю"], extra)
        self.storage.update_paragraph(self.hand, "Він схопив пальницю.", False)  # the known rendering is a candidate for the program too
        self.transport.replies["rendering"].append({"rendering": None, "reason": None, "issues": []})
        self.assertEqual("пальницю", self.how(self.hand)["rendering"])

    def test_a_rendering_the_model_names_that_is_not_in_the_text_is_not_remembered(self):
        self.transport.replies["rendering"].append({"rendering": "жердина", "reason": None, "issues": []})
        self.how(self.swing)
        self.assertNotIn("жердина", [item["text"] for item in self.storage.list_known_renderings([self.project_id], "poker")])


class LambTests(DictionaryFixture):
    """What the model makes up: empty «Чому так», words that do not exist, a part of speech in English."""

    LAMB = {"term": "lamb", "lemma": "lamb", "pos": "noun", "termType": "word", "expandedPhrase": None, "senseId": "s1", "senses": [
        {"gloss": "молода вівця", "pos": "noun", "translations": [{"text": "ягня"}, {"text": "баранння"}, {"text": "Ягнятко"}],
         "examples": []},
        {"gloss": "м'ясо молодої вівці", "pos": "іменник", "translations": [{"text": "баранина"}], "examples": []},
        {"gloss": "вигадане", "pos": "adjective", "translations": [{"text": "ягнятизм"}], "examples": []},
    ]}

    def setUp(self):
        super().setUp()
        self.storage.save_book_structure(self.project_id, "l.epub", "application/epub+zip", b"l", {"chapters": [{"title": "L", "elements": [
            {"type": "paragraph", "text": "Frozen little lamb, hoping the wolf isn’t going to snap her tender neck."}]}]})
        self.para = self.storage.get_book_structure(self.project_id)["chapters"][0]["elements"][0]["paragraphId"]
        self.storage.update_paragraph(self.para, "Заціпеніле ягнятко, яке сподівається, що вовк не зламає їй ніжну шию.", False)
        self.transport.replies["full"].append(self.LAMB)

    def how(self):
        result = self.lookup("lamb", paragraph=self.para)["result"]
        text = plain_text(self.storage.paragraph_lookup_context(self.para)["originalText"])
        start = text.index("lamb")
        return self.service.rendering({"projectId": self.project_id, "paragraphId": self.para, "text": "lamb", "offsetStart": start,
                                       "offsetEnd": start + 4, "lemma": "lamb", "senseId": result["senseId"]})

    def test_a_reason_that_only_restates_the_dictionary_or_the_grammar_is_no_reason(self):
        for number, empty in enumerate(("Перекладено як молода вівця, що відповідає першому значенню за словником; форма збіглася з оригіналом (однина, називний відмінок).",
                      "Відповідає основному значенню слова.", "Слово в однині, як в оригіналі.", "Дослівний переклад.")):
            self.transport.replies["rendering"].append({"rendering": "ягнятко", "reason": empty, "issues": [empty, "Регістр не відповідає мовцеві."]})
            self.storage.update_paragraph(self.para, f"Заціпеніле ягнятко, яке сподівається, що вовк не зламає їй ніжну шию ({number}).", False)  # a new text: not cached
            answer = self.how()
            self.assertEqual((None, ["Регістр не відповідає мовцеві."]), (answer["reason"], answer["issues"]), empty)

    def test_a_real_ground_stays(self):
        self.transport.replies["rendering"].append({"rendering": "ягнятко", "reason": "Зменшувальна форма передає little (little lamb).", "issues": []})
        self.assertEqual("Зменшувальна форма передає little (little lamb).", self.how()["reason"])

    def test_the_prompt_forbids_restating_and_names_bad_examples(self):
        self.how()
        system = self.transport.calls[-1]["payload"]["system"][0]["text"]
        for needle in ("відповідає першому значенню за словником", "форма збіглася з оригіналом", "відмінок", "reason: null", "Зменшувальна форма передає little"):
            self.assertIn(needle, system)

    def test_words_the_morphology_does_not_know_are_not_shown_and_the_part_of_speech_is_ukrainian(self):
        result = self.lookup("lamb", paragraph=self.para)["result"]
        self.assertEqual(["ягня", "Ягнятко"], [item["text"] for item in result["translations"]])  # «баранння» is made up
        self.assertEqual("іменник", result["pos"])
        self.assertEqual(["іменник"], [sense["pos"] for sense in result["otherSenses"][:1]])
        # a sense none of whose variants could be checked keeps them, marked
        unchecked = result["otherSenses"][-1]
        self.assertEqual("прикметник", unchecked["pos"])
        self.assertEqual([("ягнятизм", True)], [(item["text"], item.get("unverified")) for item in unchecked["translations"]])
        stored = self.storage.get_dictionary_senses("lamb")["senses"]
        self.assertTrue(all(sense["pos"] in ("іменник", "прикметник") for sense in stored))

    def test_the_prompt_asks_for_real_words_in_ukrainian_and_the_natural_variants_first(self):
        self.lookup("lamb", paragraph=self.para)
        system = self.transport.calls[0]["payload"]["system"][0]["text"]
        for needle in ("реальне слово сучасної української", "ягнятко", "українською"):
            self.assertIn(needle, system)

    def test_the_inventory_may_have_a_stronger_model_than_the_rest(self):
        self.models = [{"id": PRICED, "displayName": "Sonnet"}, {"id": "strong-model", "displayName": "Strong"}]
        self.storage.update_project(self.project_id, {"aiConfiguration": {"dictionary": {"model": PRICED, "inventoryModel": "strong-model"}}})
        self.transport.replies["rendering"].append({"rendering": "ягнятко", "reason": None, "issues": []})
        self.how()
        self.assertEqual([("full", "strong-model"), ("rendering", PRICED)], [(call["kind"], call["payload"]["model"]) for call in self.transport.calls])
        self.assertIsNone(server.validate_project_ai_configuration({"aiConfiguration": {"dictionary": {"inventoryModel": "x"}}}, self.storage.list_integration_connections()))


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
            self.assertEqual((200, "значення care"), (status, body["result"]["meaningInContext"]))
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
