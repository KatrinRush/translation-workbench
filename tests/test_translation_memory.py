"""Translation memory: a reference for the translator only (reviewed or proofread paragraphs of all her books), no model.
What it finds, in what order, how it highlights, and the guarantee that it never reaches a prompt."""
import ast
import itertools
import json
import re
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet

from backend import server, storage as storage_module
from backend.chat_service import ChatService
from backend.dictionary_service import DictionaryError, DictionaryService, translation_hash
from backend.integrations.base import ConnectionTestResult, IntegrationProvider, ProviderDescriptor
from backend.integrations.credentials import CredentialVault
from backend.integrations.providers.claude import ClaudeProvider
from backend.integrations.registry import ProviderRegistry
from backend.qa.service import QaService
from backend.storage import Storage
from backend.translation_memory import Query, TranslationMemory, canonical_rendering, clean_translation, english_word_forms, ukrainian_forms
from backend.translations.service import TranslationService

BACKEND = Path(__file__).resolve().parent.parent / "backend"


class MemoryFixture(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.directory.name) / "w.sqlite3")
        self.memory = TranslationMemory(self.storage)
        self.series = self.storage.create_series({"name": "Saga"})["seriesId"]

    def tearDown(self):
        self.directory.cleanup()

    def book(self, title, paragraphs, series=None, number=None):
        """paragraphs: (original, translation, flag) with flag 'reviewed', 'proofread', 'service' or None."""
        project = self.storage.create_project({"title": title, "status": "translation", "seriesId": series, "bookNumber": number})
        self.storage.save_book_structure(project["projectId"], "b.epub", "application/epub+zip", b"b", {"chapters": [
            {"title": f"{title} ch1", "elements": [{"type": "paragraph", "text": original} for original, _t, _f in paragraphs]}]})
        elements = self.storage.get_book_structure(project["projectId"])["chapters"][0]["elements"]
        ids = []
        for element, (_original, translation, flag) in zip(elements, paragraphs):
            self.storage.update_paragraph(element["paragraphId"], translation, flag == "reviewed", flag == "service", None, flag == "proofread")
            ids.append(element["paragraphId"])
        return project["projectId"], ids

    def search(self, project_id, query=None, paragraph_id=None, text=None, offset=0, limit=20):
        data = {"projectId": project_id, "offset": offset, "limit": limit}
        if query is not None:
            data["query"] = query
        else:
            plain = re.sub("<[^>]*>", "", self.storage.paragraph_lookup_context(paragraph_id)["originalText"])
            start = plain.index(text)
            data.update({"paragraphId": paragraph_id, "text": text, "offsetStart": start, "offsetEnd": start + len(text)})
        return self.memory.search(data)

    def originals(self, result):
        return [item["original"] for item in result["items"]]


class SourceTests(MemoryFixture):
    def test_only_reviewed_or_proofread_paragraphs_reach_the_memory(self):
        pid, ids = self.book("A", [
            ("The poker one.", "Кочерга раз.", "reviewed"),
            ("The poker two.", "Кочерга два.", "proofread"),
            ("The poker three.", "Кочерга три.", None),  # a translation nobody confirmed
            ("The poker four.", "", "reviewed"),  # reviewed but empty
            ("The poker five.", "Кочерга п'ять.", "service"),  # service text
        ])
        other, _ = self.book("B", [("Here is a poker.", "Ось кочерга.", "reviewed")])
        result = self.search(other, query="poker")
        self.assertEqual({"The poker one.", "The poker two.", "Here is a poker."}, set(self.originals(result)))
        self.assertEqual(3, result["total"])

    def test_the_tapped_paragraph_itself_is_left_out(self):
        pid, ids = self.book("A", [("A poker here.", "Кочерга тут.", "reviewed"), ("Another poker.", "Ще кочерга.", "reviewed")])
        result = self.search(pid, paragraph_id=ids[0], text="poker")
        self.assertEqual(["Another poker."], self.originals(result))

    def test_the_search_makes_no_model_call_and_changes_nothing(self):
        pid, ids = self.book("A", [("A poker here.", "Кочерга тут.", "reviewed")])
        path = Path(self.directory.name) / "w.sqlite3"

        def dump():
            with sqlite3.connect(path) as connection:
                return "\n".join(connection.iterdump())

        before = dump()
        with patch.object(ClaudeProvider, "complete", side_effect=AssertionError("no model")), \
                patch.object(ClaudeProvider, "translate", side_effect=AssertionError("no model")), \
                patch.object(ClaudeProvider, "analyze", side_effect=AssertionError("no model")):
            self.search(pid, query="poker")
            self.search(pid, query="кочерга")
        self.assertEqual(before, dump())  # nothing was written: not a usage row, not a cache row


class FormsTests(MemoryFixture):
    def setUp(self):
        super().setUp()
        self.pid, self.ids = self.book("A", [
            ("He took the poker.", "Він узяв кочергу.", "reviewed"),
            ("Two pokers stood there.", "Там стояли дві кочерги.", "reviewed"),
            ("The poker's handle was hot.", "Ручка кочерги була гаряча.", "reviewed"),
            ("A pokerface is a pokerface.", "Незворушне обличчя.", "reviewed"),
            ("She went home.", "Вона пішла додому.", "reviewed"),
            ("Women went there, and the woman stayed.", "Жінки пішли, а жінка лишилась.", "reviewed"),
            ("He kicked the bucket.", "Він віддав Богу душу.", "reviewed"),
            ("She Kicked The Bucket too.", "І вона теж.", "reviewed"),
            ("He kicked a bucket.", "Він копнув відро.", "reviewed"),
            ("Draven came; Dravena smiled.", "Дрейвен прийшов; Дрейвену всміхнулась.", "reviewed"),
        ])
        self.other, _ = self.book("B", [("Nothing.", "Нічого.", "reviewed")])

    def test_english_regular_forms_and_not_longer_words(self):
        for needle in ("poker", "pokers"):
            result = self.search(self.other, query=needle)
            self.assertEqual({"He took the poker.", "Two pokers stood there.", "The poker's handle was hot."}, set(self.originals(result)), needle)
        self.assertEqual("poker", self.search(self.other, query="poker")["sourceTerm"])

    def test_the_tapped_form_finds_the_other_forms(self):
        result = self.search(self.pid, paragraph_id=self.ids[1], text="pokers")
        self.assertEqual({"He took the poker.", "The poker's handle was hot."}, set(self.originals(result)))  # not the paragraph tapped

    def test_irregular_forms(self):
        self.assertEqual(["She went home.", "Women went there, and the woman stayed."], self.originals(self.search(self.other, query="go")))
        self.assertEqual(["Women went there, and the woman stayed."], self.originals(self.search(self.other, query="women")))
        self.assertIn("woman", english_word_forms("women"))
        self.assertIn("went", english_word_forms("gone"))

    def test_a_phrase_is_an_exact_match_without_regard_to_case(self):
        result = self.search(self.other, query="kicked the bucket")
        self.assertEqual(["He kicked the bucket.", "She Kicked The Bucket too."], self.originals(result))
        self.assertTrue(result["phrase"])
        self.assertEqual([], self.originals(self.search(self.other, query="kick the bucket")))  # no forms for a phrase

    def test_ukrainian_forms_through_pymorphy(self):
        for needle in ("кочерга", "кочерги", "кочергу", "кочергою"):
            result = self.search(self.other, query=needle)
            self.assertEqual({"He took the poker.", "Two pokers stood there.", "The poker's handle was hot."}, set(self.originals(result)), needle)
        self.assertEqual("uk", self.search(self.other, query="кочергою")["language"])
        self.assertIn("кочергою", ukrainian_forms("кочерга")[0])

    def test_a_name_unknown_to_pymorphy_is_found_by_its_stem(self):
        result = self.search(self.other, query="Дрейвена")
        self.assertEqual(["Draven came; Dravena smiled."], self.originals(result))

    def test_the_translation_is_highlighted_for_a_ukrainian_query(self):
        item = self.search(self.other, query="кочергу")["items"][0]
        self.assertEqual(["кочергу"], [item["translation"][a:b] for a, b in item["translationRanges"]])
        self.assertEqual([], item["originalRanges"])  # unknown in the original until the dictionary knows it

    def test_the_original_is_highlighted_for_an_english_query(self):
        item = next(i for i in self.search(self.other, query="poker")["items"] if i["original"] == "Two pokers stood there.")
        self.assertEqual(["pokers"], [item["original"][a:b] for a, b in item["originalRanges"]])

    def test_a_footnote_marker_next_to_the_word_does_not_hide_it(self):
        pid, ids = self.book("C", [("A bucket here.", "Відроfn1 тут.", "reviewed")])
        found = self.originals(self.search(self.other, query="відро"))
        self.assertIn("A bucket here.", found)  # the marker is glued to the word in the FTS index: the prefix query still finds it
        self.assertIn("He kicked a bucket.", found)

    def test_bad_queries(self):
        for bad in ("", "   ", "!!!", "a b c d e f g h i"):
            with self.subTest(bad=bad):
                with self.assertRaises(DictionaryError):
                    self.memory.search({"projectId": self.other, "query": bad if bad.strip() else None, "paragraphId": None})
        with self.assertRaises(DictionaryError) as raised:
            self.memory.search({"projectId": "nope", "query": "x"})
        self.assertEqual(404, raised.exception.http_status)


class OrderAndPagingTests(MemoryFixture):
    def test_current_book_then_the_series_by_number_then_the_rest(self):
        poker = lambda tag: [(f"{tag} poker.", f"{tag} кочерга.", "reviewed")]
        z_other, _ = self.book("Zeta other", poker("Zeta"))
        a_other, _ = self.book("Alpha other", poker("Alpha"))
        third, _ = self.book("Third", poker("Third"), series=self.series, number=3)
        first, _ = self.book("First", poker("First"), series=self.series, number=1)
        current, _ = self.book("Current", poker("Current"), series=self.series, number=2)
        result = self.search(current, query="poker")
        self.assertEqual(["Current poker.", "First poker.", "Third poker.", "Alpha poker.", "Zeta poker."], self.originals(result))
        self.assertEqual(["current", "series", "series", "other", "other"], [item["scope"] for item in result["items"]])
        self.assertEqual(["Current", "First", "Third", "Alpha other", "Zeta other"], [item["projectTitle"] for item in result["items"]])

    def test_twenty_at_a_time_and_show_more(self):
        pid, _ = self.book("A", [(f"Poker number {i:02d}.", f"Кочерга {i}.", "reviewed") for i in range(45)])
        other, _ = self.book("B", [("x", "x", None)])
        first = self.search(other, query="poker")
        self.assertEqual((20, 45, True), (len(first["items"]), first["total"], first["hasMore"]))
        second = self.search(other, query="poker", offset=20)
        third = self.search(other, query="poker", offset=40)
        self.assertEqual((20, 5, True, False), (len(second["items"]), len(third["items"]), second["hasMore"], third["hasMore"]))
        seen = self.originals(first) + self.originals(second) + self.originals(third)
        self.assertEqual(sorted(seen), seen)  # the book order, no repeats
        self.assertEqual(45, len(set(seen)))
        self.assertEqual(3, len(self.search(other, query="poker", limit=3)["items"]))


class HighlightTests(MemoryFixture):
    def setUp(self):
        super().setUp()
        self.pid, self.ids = self.book("A", [
            ("The poker burned.", "Кочергу розпечено.", "reviewed"),
            ("A poker lay there.", "Там лежала коцюба.", "reviewed"),
            ("Another poker.", "Ще щось.", "reviewed"),
        ])
        self.other, _ = self.book("B", [("x", "x", None)])

    def known(self, index, rendering, translation=None, lemma="poker", term="poker"):
        text = translation if translation is not None else self.storage.paragraph_lookup_context(self.ids[index])["translationText"]
        self.storage.put_dictionary_rendering(self.pid, self.ids[index], term, lemma, "s1", f"{translation_hash(text)}:s1", rendering, None, [], "m", "lookup")

    def items(self):
        return {item["original"]: item for item in self.search(self.other, query="poker")["items"]}

    def test_the_rendering_is_marked_only_when_the_dictionary_knows_it_and_the_hash_matches(self):
        self.known(0, "Кочергу")
        item = self.items()["The poker burned."]
        self.assertEqual(["Кочергу"], [item["translation"][a:b] for a, b in item["translationRanges"]])
        self.assertEqual("Кочергу", item["rendering"])
        self.assertEqual([], self.items()["A poker lay there."]["translationRanges"])  # nothing is known there: the whole paragraph, no mark

    def test_a_changed_translation_takes_the_mark_away(self):
        self.known(0, "Кочергу")
        self.storage.update_paragraph(self.ids[0], "Кочергу розпечено ще дужче.", True)
        item = self.items()["The poker burned."]
        self.assertEqual(([], None), (item["translationRanges"], item["rendering"]))

    def test_a_row_for_the_old_text_is_not_trusted(self):
        self.known(1, "коцюба", translation="Старий переклад: коцюба.")
        self.assertEqual(([], None), (self.items()["A poker lay there."]["translationRanges"], self.items()["A poker lay there."]["rendering"]))

    def test_a_rendering_that_is_not_in_the_text_marks_nothing(self):
        self.known(0, "жердина")
        item = self.items()["The poker burned."]
        self.assertEqual([], item["translationRanges"])

    def test_the_summary_counts_known_renderings_and_the_rest_as_undecided(self):
        self.known(0, "Кочергу")
        self.known(1, "коцюба")
        pid2, ids2 = self.book("C", [("Poker again.", "Кочерга знову.", "reviewed"), ("Poker thrice.", "Кочерга втретє.", "reviewed")])
        for pid_, pid_ids, index in ((pid2, ids2, 0), (pid2, ids2, 1)):
            text = self.storage.paragraph_lookup_context(pid_ids[index])["translationText"]
            self.storage.put_dictionary_rendering(pid_, pid_ids[index], "poker", "poker", "s1", f"{translation_hash(text)}:s1", "кочерга", None, [], "m", "lookup")
        summary = self.search(self.other, query="poker")["summary"]
        self.assertEqual([("кочерга", 3), ("коцюба", 1)], [(group["text"], group["count"]) for group in summary["groups"]])
        self.assertEqual(1, summary["unresolved"])  # «Another poker»

    def test_no_summary_without_a_known_rendering(self):
        self.assertIsNone(self.search(self.other, query="poker")["summary"])

    def test_the_original_is_marked_for_a_ukrainian_query_when_the_dictionary_knows_the_term(self):
        self.known(1, "коцюба", term="poker")
        item = self.search(self.other, query="коцюбу")["items"][0]
        self.assertEqual(["poker"], [item["original"][a:b] for a, b in item["originalRanges"]])
        self.assertEqual(["коцюба"], [item["translation"][a:b] for a, b in item["translationRanges"]])

    def test_canonical_renderings_join_case_forms(self):
        self.assertEqual(canonical_rendering("кочергу"), canonical_rendering("кочерга"))
        self.assertEqual("віддав богу душу", canonical_rendering("Віддав Богу душу"))


class AlignmentTests(MemoryFixture):
    """Renderings found without a model: the forms of the lemma's variants and the known renderings in the translation."""

    HAND = "— Вони зв'яжуться зі мною пізніше, якщо буде потреба, — він недбало змахує рукою і хапає кочергу\ue000fn1\ue000 біля каміна."
    SWING = "— Ти досі не їси, — містер Спрингтон повертається і хмуриться на мене, кочерга тепер ліниво гойдається в його руці."

    def setUp(self):
        super().setUp()
        self.storage.put_dictionary_senses("poker", {"senses": [
            {"id": "s1", "gloss": "кочерга", "pos": "іменник", "translations": [{"text": "кочерга", "register": "нейтральне"}], "examples": []},
            {"id": "s2", "gloss": "карткова гра", "pos": "іменник", "translations": [{"text": "покер", "register": "нейтральне"}], "examples": []},
        ], "extended": 0}, "m")
        self.pid, self.ids = self.book("A", [
            ("“They’ll contact me later if needed,” he waves a careless hand and grabs the poker by the fireplace.", self.HAND, "reviewed"),
            ("“You’re still not eating,” Mr. Springton turns and frowns at me, poker swinging idly in his hand now.", self.SWING, "reviewed"),
            ("He played poker with the poker.", "Він грав у покер кочергою.", "reviewed"),   # two candidates: undecided
            ("A poker stood there.", "Там стояло щось.", "reviewed"),                      # none: undecided
        ])
        self.other, _ = self.book("B", [("x", "x", None)])

    def items(self):
        return {item["original"][:20]: item for item in self.search(self.other, query="poker")["items"]}

    def item(self, start):
        return next(item for item in self.search(self.other, query="poker")["items"] if item["original"].startswith(start))

    def stored(self):
        with self.storage.connection() as connection:
            return {row["paragraph_id"]: dict(row) for row in connection.execute("SELECT * FROM dictionary_renderings")}

    def test_a_single_candidate_is_marked_counted_and_stored_with_the_translation_hash(self):
        result = self.search(self.other, query="poker")
        by_start = {item["original"][:12]: item for item in result["items"]}
        hand, swing = by_start["“They’ll con"], by_start["“You’re stil"]
        self.assertEqual(["кочергу"], [hand["translation"][a:b] for a, b in hand["translationRanges"]])
        self.assertEqual(["кочерга"], [swing["translation"][a:b] for a, b in swing["translationRanges"]])
        self.assertEqual(["poker"], [hand["original"][a:b] for a, b in hand["originalRanges"]])
        self.assertEqual([("кочерга", 2)], [(group["text"], group["count"]) for group in result["summary"]["groups"]])
        self.assertEqual(2, result["summary"]["unresolved"])
        rows = self.stored()
        self.assertEqual({self.ids[0], self.ids[1]}, set(rows))
        row = rows[self.ids[0]]
        self.assertEqual(("memory", "кочергу", "poker", f"{translation_hash(clean_translation(self.HAND))}:"),
                         (row["source"], row["rendering"], row["lemma_key"], row["translation_hash"]))

    def test_several_candidates_or_none_mark_nothing_and_are_undecided(self):
        items = self.items()
        for start in ("He played poker with", "A poker stood there."):
            self.assertEqual(([], None), (items[start]["translationRanges"], items[start]["rendering"]), start)

    def test_a_rendering_the_inventory_lacks_but_the_project_knows_is_found(self):
        self.assertEqual([], self.items()["A poker stood there."]["translationRanges"])
        self.storage.update_paragraph(self.ids[3], "Там стояла коцюба.", True)
        self.assertEqual([], self.items()["A poker stood there."]["translationRanges"])  # «коцюба» is not a variant yet
        self.storage.add_known_rendering(self.pid, "poker", "коцюба", "коцюбу", "model")
        item = self.items()["A poker stood there."]
        self.assertEqual(["коцюба"], [item["translation"][a:b] for a, b in item["translationRanges"]])

    def test_a_not_found_from_a_lookup_does_not_hide_a_form_that_is_there(self):
        digest = translation_hash(clean_translation(self.HAND))
        self.storage.put_dictionary_rendering(self.pid, self.ids[0], "poker", "poker", "s1", f"{digest}:s1", None, None, [], "m", "lookup")
        item = self.item("“They")
        self.assertEqual("кочергу", item["rendering"])
        self.assertEqual("кочергу", self.stored()[self.ids[0]]["rendering"])

    def test_a_changed_translation_is_aligned_again_and_the_old_hash_goes(self):
        self.items()
        self.storage.update_paragraph(self.ids[1], "Містер Спрингтон мовчав, і кочерги не було.", True)
        item = self.item("“You’re")
        self.assertEqual(["кочерги"], [item["translation"][a:b] for a, b in item["translationRanges"]])
        self.assertEqual(f"{translation_hash('Містер Спрингтон мовчав, і кочерги не було.')}:", self.stored()[self.ids[1]]["translation_hash"])

    def test_the_summary_joins_case_forms_into_one_group(self):
        self.storage.update_paragraph(self.ids[1], "Містер Спрингтон мовчав, і кочерги не було.", True)
        groups = self.search(self.other, query="poker")["summary"]["groups"]
        self.assertEqual([("кочерга", 2)], [(group["text"], group["count"]) for group in groups])
        self.assertEqual(canonical_rendering("кочерги"), canonical_rendering("кочерга"))

    def test_her_confirmation_makes_a_word_a_known_rendering_and_marks_it_everywhere(self):
        self.storage.update_paragraph(self.ids[3], "Там стояла коцюба.", True)
        other, other_ids = self.book("C", [("Another poker.", "Він узяв коцюбу.", "reviewed")])
        self.assertEqual([], self.item("A poker stood").get("translationRanges"))
        answer = self.memory.confirm_rendering({"projectId": self.other, "paragraphId": self.ids[3], "lemma": "poker", "text": "коцюба"})
        self.assertEqual("коцюба", answer["rendering"])
        self.assertEqual(["коцюба"], [item["text"] for item in self.storage.list_known_renderings([self.other], "poker")])
        self.assertEqual("confirmed", self.stored()[self.ids[3]]["source"])
        result = self.search(self.other, query="poker")
        by_start = {item["original"][:12]: item for item in result["items"]}
        marked = by_start["A poker stoo"]
        self.assertEqual(["коцюба"], [marked["translation"][a:b] for a, b in marked["translationRanges"]])
        form = by_start["Another poke"]  # the other book's paragraph, another case form, is found at once
        self.assertEqual(["коцюбу"], [form["translation"][a:b] for a, b in form["translationRanges"]])
        self.assertEqual({"кочерга": 2, "коцюба": 2}, {group["text"]: group["count"] for group in result["summary"]["groups"]})

    def test_a_confirmation_needs_the_word_to_stand_in_the_translation(self):
        for text in ("жердина", ""):
            with self.assertRaises(DictionaryError):
                self.memory.confirm_rendering({"projectId": self.other, "paragraphId": self.ids[3], "lemma": "poker", "text": text})
        self.assertEqual([], self.storage.list_known_renderings([self.other], "poker"))

    def test_a_stored_rendering_marks_every_form_of_the_word_in_the_paragraph(self):
        self.storage.update_paragraph(self.ids[3], "Кочерги тут, кочерга там, кочергою звідси.", True)
        self.item("A poker stood")  # aligned and stored with the first form
        item = self.item("A poker stood")  # read back from the stored row
        self.assertEqual(["Кочерги", "кочерга", "кочергою"], [item["translation"][a:b] for a, b in item["translationRanges"]])

    def test_a_second_search_changes_nothing(self):
        self.items()
        with self.storage.connection() as connection:
            before = [tuple(row) for row in connection.execute("SELECT * FROM dictionary_renderings ORDER BY paragraph_id")]
        self.items()
        with self.storage.connection() as connection:
            after = [tuple(row) for row in connection.execute("SELECT * FROM dictionary_renderings ORDER BY paragraph_id")]
        self.assertEqual(before, after)


class IsolationTests(unittest.TestCase):
    PROMPT_MODULES = [
        *sorted((BACKEND / "translations").glob("*.py")), *sorted((BACKEND / "qa").glob("*.py")),
        *sorted((BACKEND / "integrations").rglob("*.py")), BACKEND / "chat_service.py", BACKEND / "dictionary_service.py",
        BACKEND / "queue_service.py", BACKEND / "usage.py", BACKEND / "export_service.py", BACKEND / "storage.py",
    ]

    def test_no_prompt_building_module_imports_or_names_the_memory(self):
        for path in self.PROMPT_MODULES:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or "", *[alias.name for alias in node.names]]
                self.assertFalse(any("translation_memory" in name for name in names), f"{path.name} imports the translation memory")
            self.assertNotIn("TranslationMemory", path.read_text(encoding="utf-8"), path.name)

    def test_only_the_http_layer_imports_the_memory(self):
        importers = [path.name for path in BACKEND.rglob("*.py") if path.name != "translation_memory.py" and "translation_memory" in path.read_text(encoding="utf-8")]
        self.assertEqual(["server.py"], importers)

    def test_the_memory_module_has_no_provider_in_it(self):
        text = (BACKEND / "translation_memory.py").read_text(encoding="utf-8")
        for forbidden in ("integrations", "complete(", "TranslationRequest", "UsageRecorder", "capture_usage"):
            self.assertNotIn(forbidden, text)


class CaptureTransport:
    """A Claude transport that records every request body and answers by the kind of the request."""

    def __init__(self):
        self.bodies = []

    def post(self, url, headers, body, timeout):
        self.bodies.append(body)
        payload = json.loads(body)
        prompt = payload["messages"][0]["content"]
        system = payload["system"][0]["text"] if isinstance(payload.get("system"), list) else str(payload.get("system"))
        chunk = re.search(r"<chunk>.*</chunk>", prompt, re.S)
        if "англо-український словник" in system:
            term = re.search(r"Термін: (.+)", prompt).group(1).strip()
            if "Дай повний перелік" in system:
                answer = {"term": term, "lemma": term.lower(), "pos": "іменник", "termType": "word", "expandedPhrase": None,
                          "senses": [{"gloss": "значення", "translations": [{"text": "кочерга"}]}], "senseId": "s1"}
            else:
                answer = {"term": term, "lemma": term.lower(), "pos": None, "termType": "word", "expandedPhrase": None, "senseId": "s1", "newSense": None}
            text = json.dumps(answer, ensure_ascii=False)
        elif "перевірити, як слово чи фразу" in system:
            text = json.dumps({"rendering": "кочерга", "reason": None, "issues": []}, ensure_ascii=False)
        elif chunk:
            text = re.sub(r'(<p id="[^"]+">).*?(</p>)', r"\1Переклад\2", chunk.group(0), flags=re.S)
        else:
            text = "OK"
        return 200, json.dumps({"model": payload["model"], "stop_reason": "end_turn", "content": [{"type": "text", "text": text}],
                                "usage": {"input_tokens": 10, "output_tokens": 5}}).encode()


class AnalyzeProvider(IntegrationProvider):
    def __init__(self):
        self.prompts = []

    @property
    def descriptor(self):
        return ProviderDescriptor("claude", "Claude", "", ())

    def validate_credentials(self, credentials):
        return dict(credentials)

    def test_connection(self, credentials):
        return ConnectionTestResult("connected", "ok", "ok")

    def translate(self, credentials, request):
        raise AssertionError("not used")

    def analyze(self, credentials, prompt):
        self.prompts.append(prompt)
        return "===JSON===\n[]" if "JSON" in prompt else "Відповідь."


class PromptBytesTests(unittest.TestCase):
    """The requests that go to a model are the same, byte for byte, whether the memory has something to find or not."""

    def run_everything(self, with_memory):
        counter = itertools.count(1)
        with tempfile.TemporaryDirectory() as directory, patch.object(storage_module, "_new_id", lambda prefix: f"{prefix}-{next(counter):04d}"):
            storage = Storage(Path(directory) / "w.sqlite3")
            vault = CredentialVault(Fernet(Fernet.generate_key()))
            transport = CaptureTransport()
            connection = storage.create_integration_connection("claude", "Claude", vault.encrypt({"apiKey": "k"}))
            storage.update_integration_connection_status(connection["connectionId"], "connected", "ok", "ok", {})
            harry = storage.create_glossary_entry({"source": "Harry", "target": "Гаррі", "characterGender": "masc"})
            project = storage.create_project({"title": "Current", "status": "translation", "narratorGender": "masc",
                                              "projectGlossaryEntryIds": [harry["glossaryEntryId"]],
                                              "aiConfiguration": {"translationConnectionId": connection["connectionId"],
                                                                  "dictionary": {"connectionId": connection["connectionId"], "model": "m-dict"}}})
            project_id = project["projectId"]
            storage.save_book_structure(project_id, "b.epub", "application/epub+zip", b"b", {"chapters": [{"title": "One", "elements": [
                {"type": "paragraph", "text": "Harry took the poker."}, {"type": "paragraph", "text": "He put the poker down."},
                {"type": "paragraph", "text": "Then he left."}]}]})
            chapter = storage.get_book_structure(project_id)["chapters"][0]
            ids = [element["paragraphId"] for element in chapter["elements"]]
            storage.update_paragraph(ids[0], "Гаррі взяв кочергу.", True)
            if with_memory:  # the same word in other books, reviewed, with renderings the dictionary knows: everything the memory could show
                other = storage.create_project({"title": "Other", "status": "translation"})["projectId"]
                storage.save_book_structure(other, "o.epub", "application/epub+zip", b"o", {"chapters": [{"title": "O", "elements": [
                    {"type": "paragraph", "text": "A poker, a poker."}]}]})
                other_id = storage.get_book_structure(other)["chapters"][0]["elements"][0]["paragraphId"]
                storage.update_paragraph(other_id, "Коцюба, коцюба.", True)
                storage.put_dictionary_rendering(other, other_id, "poker", "poker", "s1", f"{translation_hash('Коцюба, коцюба.')}:s1", "коцюба", None, [], "m", "lookup")
                for _ in range(2):
                    TranslationMemory(storage).search({"projectId": project_id, "query": "poker"})
                    TranslationMemory(storage).search({"projectId": project_id, "query": "кочерга"})
            registry = ProviderRegistry([ClaudeProvider(transport)])
            captured = {}

            translation = TranslationService(storage, vault, registry)
            translation.translate_chapter(project_id, chapter["chapterId"], {"batchIndex": 0})
            captured["translation"] = list(transport.bodies)
            transport.bodies.clear()

            dictionary = DictionaryService(storage, vault, registry, lambda connection_id: {"models": []}, lambda p: translation._llm_glossary_entries(p))
            plain = "He put the poker down."
            start = plain.index("poker")
            request = {"projectId": project_id, "paragraphId": ids[1], "text": "poker", "offsetStart": start, "offsetEnd": start + 5, "mode": "word"}
            looked = dictionary.lookup(request)
            dictionary.rendering({**request, "lemma": looked["result"]["lemmaKey"], "senseId": looked["result"]["senseId"]})
            captured["dictionary"] = list(transport.bodies)

            provider = AnalyzeProvider()
            analyze_registry = ProviderRegistry([provider])
            ChatService(storage, vault, analyze_registry).send_message(project_id, "Як перекласти poker?", "claude")
            qa_target = [connection["connectionId"]]
            storage.update_project(project_id, {"aiConfiguration": {"qaConnectionIds": qa_target}})
            QaService(storage, vault, analyze_registry).check_chapter_translation_quality(project_id, chapter["chapterId"], qa_target, batch_index=0)
            captured["analyze"] = list(provider.prompts)
            return captured

    def test_translation_dictionary_chat_and_qa_requests_are_byte_identical_with_and_without_memory(self):
        without = self.run_everything(False)
        with_memory = self.run_everything(True)
        for kind in ("translation", "dictionary", "analyze"):
            self.assertTrue(without[kind], f"{kind}: nothing was sent, the test would prove nothing")
            self.assertEqual(without[kind], with_memory[kind], f"{kind} requests differ when the memory has content")
        # and the memory's own words are nowhere in them
        joined = json.dumps([*[body.decode() for body in with_memory["translation"] + with_memory["dictionary"]], *with_memory["analyze"]], ensure_ascii=False)
        self.assertNotIn("Коцюба", joined)
        self.assertNotIn("коцюба", joined)


class ApiTests(MemoryFixture):
    class Handler:
        def __init__(self, payload):
            self.payload = payload

        def read_json(self):
            return self.payload

    def test_the_route(self):
        pid, ids = self.book("A", [("A poker.", "Кочерга.", "reviewed")])
        other, _ = self.book("B", [("x", "x", None)])
        with patch.object(server, "translation_memory", self.memory), patch.object(server, "storage", self.storage):
            status, body = server.WorkbenchHandler.handle_api(self.Handler({"projectId": other, "query": "poker"}), "POST", "/api/memory/search")
        self.assertEqual((200, 1), (status, body["total"]))
        self.assertEqual({"A poker."}, {item["original"] for item in body["items"]})


class DictionaryWithoutModelTests(MemoryFixture):
    def test_allow_model_false_answers_the_glossary_or_waits(self):
        from backend.integrations.providers.claude import ClaudeProvider as Provider
        vault = CredentialVault(Fernet(Fernet.generate_key()))
        pid, ids = self.book("A", [("A poker here.", "Кочерга тут.", "reviewed")])
        registry = ProviderRegistry([Provider(CaptureTransport())])
        entries = []
        service = DictionaryService(self.storage, vault, registry, lambda c: {"models": []}, lambda project: entries)
        request = {"projectId": pid, "paragraphId": ids[0], "text": "poker", "offsetStart": 2, "offsetEnd": 7, "mode": "word", "allowModel": False}
        waiting = service.lookup(request)  # no connection, no model: still an answer
        self.assertEqual(("pending", None, False), (waiting["source"], waiting["result"], waiting["cached"]))
        self.assertEqual("poker", waiting["term"])
        entries.append({"source": "poker", "target": "кочерга", "note": None, "active": True})
        covered = service.lookup(request)
        self.assertEqual("glossary", covered["source"])
        self.assertEqual("poker", covered["glossary"][0]["source"])


if __name__ == "__main__":
    unittest.main()
