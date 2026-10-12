"""«Знайти й замінити» in the translation text: match modes, Ukrainian case forms, case, apostrophes,
tags and footnotes, proofread paragraphs, the engine variants option, all-or-nothing, undo and redo."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend import server
from backend.storage import Storage
from backend.text_replace import Matcher

MARK = ""


class ReplaceFixture(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "w.sqlite3"
        self.storage = Storage(self.path)
        self.project_id = self.storage.create_project({"title": "Replace", "status": "translation"})["projectId"]
        self.storage.save_book_structure(self.project_id, "b.epub", "application/epub+zip", b"b", {"chapters": [
            {"title": "One", "elements": [{"type": "paragraph", "text": f"o{i}"} for i in range(5)]},
            {"title": "Two", "elements": [{"type": "paragraph", "text": f"o{i}"} for i in range(4)]},
        ]})
        chapters = self.storage.get_book_structure(self.project_id)["chapters"]
        self.chapter_ids = [chapter["chapterId"] for chapter in chapters]
        self.ids = [[element["paragraphId"] for element in chapter["elements"]] for chapter in chapters]
        self.footnote = self.storage.create_paragraph_footnote(self.ids[0][1], {"noteText": "Примітка"})["footnoteId"]
        self.texts = {
            self.ids[0][0]: "Дрейвен прийшов. Дрейвена бачили, Дрейвену сказали.",
            self.ids[0][1]: f"<b>Дрейвен</b> і <i>дрейвенський</i> Дрейвеном {MARK}{self.footnote}{MARK}.",
            self.ids[0][2]: "Тоні &amp; Дрейвен &lt;друзі&gt;",
            self.ids[0][3]: "Дрей<i>вен</i> перетин, а ще Дрейвен.",
            self.ids[1][0]: "Андрій, Андрія, Андрієві, Андрієм.",
            self.ids[1][1]: "Дрейвен’с і Дрейвен'с, дрейвен.",
        }
        for paragraph_id, text in self.texts.items():
            self.storage.update_paragraph(paragraph_id, text, paragraph_id == self.ids[0][1])
        self.storage = Storage(self.path)  # existing translations become the chosen «Поточний» variant

    def tearDown(self):
        self.directory.cleanup()

    def request(self, query="Дрейвен", replacement="Дравен", mode="start", match_case=False, scope="project", **extra):
        data = {"query": query, "replacement": replacement, "options": {"mode": mode, "matchCase": match_case},
                "scope": scope, "chapterId": self.chapter_ids[0], **extra}
        return data

    def find(self, **kwargs):
        return self.storage.find_translation_matches(self.project_id, self.request(**kwargs))

    def replace(self, **kwargs):
        return self.storage.replace_in_translation(self.project_id, self.request(**kwargs))

    def state(self, strict=True):
        """Everything a replacement may touch. Not strict: variant ids are left out (a redo makes a new manual variant)."""
        out = {}
        for chapter in self.storage.get_book_structure(self.project_id)["chapters"]:
            for element in chapter["elements"]:
                variants = element["translationVariants"]
                selected = next((v for v in variants if v["variantId"] == element["selectedVariantId"]), None)
                out[element["paragraphId"]] = (
                    element["translationText"], element["reviewed"],
                    element["selectedVariantId"] if strict else (selected["engine"], selected["text"]) if selected else None,
                    sorted((v["variantId"] if strict else "", v["engine"], v["text"]) for v in variants),
                    sorted(f["footnoteId"] for f in element["footnotes"]),
                )
        return out

    def text(self, paragraph_id):
        return self.storage.get_paragraph(paragraph_id)["translationText"]


class MatchTests(ReplaceFixture):
    def olds(self, **kwargs):
        return [m["matchedText"] for m in self.find(**kwargs)["matches"]]

    def test_start_of_word_finds_case_forms_but_not_other_words(self):
        olds = self.olds(mode="start", scope="chapter")
        self.assertEqual(["Дрейвен", "Дрейвена", "Дрейвену", "Дрейвен", "Дрейвеном", "Дрейвен", "Дрейвен"], olds)
        self.assertNotIn("дрейвенський", " ".join(olds).lower())

    def test_whole_word_and_any_part(self):
        self.assertEqual(["Дрейвен", "Дрейвен", "Дрейвен", "Дрейвен"], self.olds(mode="word", scope="chapter"))
        any_part = self.olds(mode="any", scope="chapter")
        self.assertIn("Дрейвен", any_part)
        self.assertEqual(8, len(self.olds(query="рейвен", mode="any", scope="chapter")))  # incl. дрейвенський, not the split one

    def test_case_off_by_default_and_on_when_asked(self):
        self.assertIn("дрейвен", self.olds(query="дрейвен", scope="project"))
        self.assertEqual(["дрейвен"], self.olds(query="дрейвен", scope="project", match_case=True)[-1:])
        self.assertEqual([], self.olds(query="ДРЕЙВЕН", scope="project", match_case=True))

    def test_apostrophes_are_normalized(self):
        found = self.olds(query="Дрейвен’с", mode="word", scope="chapter")
        self.assertEqual([], found)  # chapter 1 has none
        both = [m["matchedText"] for m in self.storage.find_translation_matches(self.project_id, self.request(query="Дрейвен'с", mode="start", scope="chapter", chapterId=self.chapter_ids[1]))["matches"]]
        self.assertEqual(["Дрейвен’с", "Дрейвен'с"], both)

    def test_names_in_ij_take_their_oblique_forms_in_start_mode_only(self):
        olds = self.olds(query="Андрій", mode="start", chapterId=self.chapter_ids[1], scope="chapter")
        self.assertEqual(["Андрій", "Андрія", "Андрієві", "Андрієм"], olds)
        self.assertEqual(["Андрій"], self.olds(query="Андрій", mode="word", scope="project"))
        self.assertEqual(["Андрій"], self.olds(query="Андрій", mode="any", scope="project"))

    def test_the_inflection_is_checked_after_the_last_word_only(self):
        self.storage.update_paragraph(self.ids[1][2], "Дрейвен Холлу і Дрейвена Холла і Дрейвеном Холл.", False)
        olds = [m["matchedText"] for m in self.find(query="Дрейвен Холл", scope="project")["matches"]]
        self.assertEqual(["Дрейвен Холлу"], olds)  # the first word must be exact: «Дрейвена Холла» is not found

    def test_matches_across_formatting_are_counted_not_listed(self):
        result = self.find(scope="chapter")
        self.assertEqual(1, result["acrossMarkup"])
        self.assertNotIn(self.ids[0][3] + ":Дрей", [m["paragraphId"] + ":" + m["matchedText"][:4] for m in result["matches"] if m["matchedText"] == "Дрей"])
        self.assertEqual(self.text(self.ids[0][3]), "Дрей<i>вен</i> перетин, а ще Дрейвен.")

    def test_totals_and_reviewed(self):
        result = self.find(scope="project")
        self.assertEqual((8, 5), (result["total"], result["paragraphs"]))
        self.assertEqual((2, 1), (result["chapters"], result["reviewedParagraphs"]))
        self.assertEqual([0, 1, 2], [m["occurrence"] for m in result["matches"] if m["paragraphId"] == self.ids[0][0]])
        first = result["matches"][0]
        self.assertTrue(first["snippet"].startswith("⟦Дрейвен⟧ прийшов. Дрейвена бачили, Дрейвену"))

    def test_validation(self):
        for bad in ({"query": ""}, {"query": "Dreyven"}, {"query": "Дрейвен", "options": {"mode": "x"}},
                    {"query": "Дрейвен", "options": {"matchCase": "yes"}}, {"query": "Дрейвен", "scope": "all"},
                    {"query": "Дрейвен", "replacement": "a\nb"}, {"query": "Дрейвен", "replacement": MARK}, {"query": "д" * 201},
                    {"query": "Дрейвен", "target": {"paragraphId": "x", "occurrence": -1}}, "x"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.storage.find_translation_matches(self.project_id, {"scope": "project", **bad} if isinstance(bad, dict) else bad)
        self.assertIsNone(self.storage.find_translation_matches("nope", self.request()))
        self.assertIsNone(self.storage.find_translation_matches(self.project_id, self.request(scope="chapter", chapterId="nope")))


class ReplaceTests(ReplaceFixture):
    def test_replace_all_changes_only_text_pieces_and_keeps_tags_markers_entities_and_reviewed(self):
        result = self.replace()
        self.assertEqual((8, 5, 2, 1, 1), tuple(result["summary"][k] for k in ("matches", "paragraphs", "chapters", "reviewedParagraphs", "acrossMarkup")))
        self.assertEqual("Дравен прийшов. Дравена бачили, Дравену сказали.", self.text(self.ids[0][0]))
        self.assertEqual(f"<b>Дравен</b> і <i>дрейвенський</i> Дравеном {MARK}{self.footnote}{MARK}.", self.text(self.ids[0][1]))
        self.assertEqual("Тоні &amp; Дравен &lt;друзі&gt;", self.text(self.ids[0][2]))
        self.assertEqual("Дрей<i>вен</i> перетин, а ще Дравен.", self.text(self.ids[0][3]))
        self.assertEqual("Дрейвен’с і Дрейвен'с, дравен.", self.text(self.ids[1][1]))  # «Дрейвен’с» is not a case form
        self.assertTrue(self.storage.get_paragraph(self.ids[0][1])["reviewed"])
        self.assertEqual([self.footnote], [f["footnoteId"] for f in self.storage.list_paragraph_footnotes(self.ids[0][1])])

    def test_the_first_letter_keeps_its_case_and_the_case_option_switches_that_off(self):
        self.replace(replacement="Дравен")
        self.assertTrue(self.text(self.ids[1][1]).endswith("дравен."))
        self.replace(query="дравен", replacement="Дрейвен", match_case=True, scope="chapter", chapterId=self.chapter_ids[1])
        self.assertTrue(self.text(self.ids[1][1]).endswith("Дрейвен."))

    def test_the_ending_of_the_name_is_kept_and_oblique_forms_follow_the_replacement(self):
        self.replace(query="Андрій", replacement="Юрій", scope="chapter", chapterId=self.chapter_ids[1])
        self.assertEqual("Юрій, Юрія, Юрієві, Юрієм.", self.text(self.ids[1][0]))
        self.replace(query="Юрій", replacement="Дрейвен", scope="chapter", chapterId=self.chapter_ids[1])
        self.assertEqual("Дрейвен, Дрейвена, Дрейвенові, Дрейвеном.", self.text(self.ids[1][0]))

    def test_one_match_by_occurrence(self):
        before = self.state()
        result = self.replace(scope="chapter", target={"paragraphId": self.ids[0][0], "occurrence": 1})
        self.assertEqual(1, result["summary"]["matches"])
        self.assertEqual("Дрейвен прийшов. Дравена бачили, Дрейвену сказали.", self.text(self.ids[0][0]))
        self.assertEqual({k: v for k, v in before.items() if k != self.ids[0][0]}, {k: v for k, v in self.state().items() if k != self.ids[0][0]})
        with self.assertRaises(ValueError):
            self.replace(scope="chapter", target={"paragraphId": self.ids[0][0], "occurrence": 9})
        with self.assertRaises(ValueError):
            self.replace(scope="chapter", target={"paragraphId": self.ids[0][4], "occurrence": 0})

    def test_the_result_is_a_manual_edit_with_one_manual_variant(self):
        self.replace(scope="chapter")
        paragraph = self.storage.get_paragraph(self.ids[0][0])
        engines = sorted(v["engine"] for v in paragraph["translationVariants"])
        self.assertEqual(["current", "manual"], engines)
        selected = next(v for v in paragraph["translationVariants"] if v["variantId"] == paragraph["selectedVariantId"])
        self.assertEqual(("manual", paragraph["translationText"]), (selected["engine"], selected["text"]))
        old = next(v for v in paragraph["translationVariants"] if v["engine"] == "current")
        self.assertIn("Дрейвен прийшов", old["text"])  # the engine variant keeps the old name by default
        self.replace(query="Дравен", replacement="Дрівен", scope="chapter")
        again = self.storage.get_paragraph(self.ids[0][0])
        self.assertEqual(["current", "manual"], sorted(v["engine"] for v in again["translationVariants"]))
        self.assertEqual(paragraph["selectedVariantId"], again["selectedVariantId"])

    def test_engine_variants_are_changed_only_when_asked(self):
        self.storage.add_translation_variant(self.ids[0][0], "claude", "Дрейвена видно, Дрейвенський не чіпати")
        self.replace(scope="chapter")
        claude = [v for v in self.storage.get_paragraph(self.ids[0][0])["translationVariants"] if v["engine"] == "claude"][0]
        self.assertIn("Дрейвена", claude["text"])
        result = self.replace(query="Дрейвена", replacement="Дравена", scope="chapter", includeVariants=True)
        self.assertGreaterEqual(result["summary"]["variantsChanged"], 1)
        paragraph = self.storage.get_paragraph(self.ids[0][0])
        by_engine = {v["engine"]: v["text"] for v in paragraph["translationVariants"]}
        self.assertEqual("Дравена видно, Дрейвенський не чіпати", by_engine["claude"])
        self.assertTrue(by_engine["current"].startswith("Дрейвен прийшов. Дравена"))
        # a bulk choice of that engine now brings the new name, not the old one
        self.storage.select_chapter_variants(self.chapter_ids[0], "claude")
        self.assertTrue(self.text(self.ids[0][0]).startswith("Дравена видно"))

    def test_dry_run_changes_nothing_and_gives_examples(self):
        before = self.state()
        result = self.replace(dryRun=True)
        self.assertEqual(before, self.state())
        self.assertEqual(8, result["summary"]["matches"])
        self.assertEqual(5, len(result["examples"]))
        self.assertTrue(result["examples"][0]["before"].startswith("⟦Дрейвен⟧ прийшов. Дрейвена бачили"))
        self.assertTrue(result["examples"][0]["after"].startswith("⟦Дравен⟧ прийшов. Дрейвена бачили"))
        self.assertEqual([], result["undo"]["items"])

    def test_nothing_found_changes_nothing(self):
        before = self.state()
        result = self.replace(query="Неіснуюче")
        self.assertEqual((0, 0), (result["summary"]["matches"], len(result["undo"]["items"])))
        self.assertEqual(before, self.state())

    def test_service_and_untranslated_paragraphs_are_not_touched(self):
        self.storage.update_paragraph(self.ids[0][4], "Дрейвен службовий", False, is_service=True)
        result = self.replace(scope="chapter")
        self.assertEqual("Дрейвен службовий", self.text(self.ids[0][4]))
        self.assertEqual(4, result["summary"]["paragraphs"])

    def test_the_replacement_is_inserted_as_plain_text(self):
        self.replace(replacement="Д<b>&р", scope="chapter", target={"paragraphId": self.ids[0][0], "occurrence": 0})
        self.assertTrue(self.text(self.ids[0][0]).startswith("Д&lt;b&gt;&amp;р прийшов"))

    def test_an_empty_replacement_deletes_the_match(self):
        self.replace(query="Дрейвен", replacement="", mode="word", scope="chapter", target={"paragraphId": self.ids[0][0], "occurrence": 0})
        self.assertTrue(self.text(self.ids[0][0]).startswith(" прийшов"))

    def test_all_or_nothing(self):
        before = self.state()
        original = Storage._manual_edit_in
        calls = []

        def fail_on_third(self_, connection, row, text):
            calls.append(1)
            if len(calls) == 3:
                raise RuntimeError("boom")
            return original(self_, connection, row, text)

        with patch.object(Storage, "_manual_edit_in", fail_on_third), self.assertRaises(RuntimeError):
            self.replace()
        self.assertEqual(before, self.state())


class UndoRedoTests(ReplaceFixture):
    def test_undo_restores_everything_and_redo_applies_the_same_texts(self):
        self.storage.add_translation_variant(self.ids[0][0], "claude", "Дрейвена Claude")
        before = self.state()
        done = self.replace(includeVariants=True, returnChapterId=self.chapter_ids[0])
        after = self.state()
        after_loose = self.state(strict=False)
        self.assertNotEqual(before, after)
        self.assertEqual(sorted(done["chapterIds"]), sorted(self.chapter_ids))
        self.assertEqual(4, len(done["paragraphs"]))  # only the chapter the client has open
        undone = self.storage.restore_replacement(self.project_id, done["undo"]["items"], self.chapter_ids[0])
        self.assertEqual(5, undone["restored"])
        self.assertEqual(before, self.state())
        redone = self.storage.apply_replacement(self.project_id, [{k: v for k, v in item.items() if k != "previous"} for item in done["undo"]["items"]], None)
        self.assertEqual(5, redone["applied"])
        self.assertEqual(after_loose, self.state(strict=False))
        self.storage.restore_replacement(self.project_id, redone["undo"]["items"])
        self.assertEqual(before, self.state())

    def test_undo_of_one_match_and_of_a_second_replacement_in_a_paragraph_with_a_manual_variant(self):
        self.storage.save_paragraph_edit(self.ids[0][0], "Дрейвен ручний", False)
        before = self.state()
        first = self.replace(scope="chapter", target={"paragraphId": self.ids[0][0], "occurrence": 0})
        self.assertEqual("Дравен ручний", self.text(self.ids[0][0]))
        self.storage.restore_replacement(self.project_id, first["undo"]["items"])
        self.assertEqual(before, self.state())

    def test_undo_removes_the_manual_variant_the_replacement_created(self):
        paragraph = self.storage.get_paragraph(self.ids[1][0])
        self.assertEqual(["current"], [v["engine"] for v in paragraph["translationVariants"]])
        done = self.replace(query="Андрій", replacement="Юрій", scope="chapter", chapterId=self.chapter_ids[1])
        self.assertIn("manual", [v["engine"] for v in self.storage.get_paragraph(self.ids[1][0])["translationVariants"]])
        self.storage.restore_replacement(self.project_id, done["undo"]["items"])
        self.assertEqual(["current"], [v["engine"] for v in self.storage.get_paragraph(self.ids[1][0])["translationVariants"]])

    def test_bad_undo_input_changes_nothing(self):
        done = self.replace()
        before = self.state()
        items = done["undo"]["items"]
        for bad in (None, [], "x", [{"paragraphId": "nope", "previous": {}}], [items[0], items[0]],
                    [{**items[0], "previous": {"selection": "x"}}], items[:1] + [{**items[1], "previous": None}]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.storage.restore_replacement(self.project_id, bad)
            self.assertEqual(before, self.state())
        other = self.storage.create_project({"title": "Other"})["projectId"]
        with self.assertRaises(ValueError):
            self.storage.restore_replacement(other, items)
        with self.assertRaises(ValueError):
            self.storage.apply_replacement(self.project_id, [{"paragraphId": items[0]["paragraphId"], "text": "x", "variants": [{"variantId": "nope", "text": "y"}]}])
        self.assertEqual(before, self.state())
        self.assertIsNone(self.storage.restore_replacement("nope", items))


class MatcherUnitTests(unittest.TestCase):
    def test_pieces_around_tags_and_entities_are_exact(self):
        matcher = Matcher("Дрейвен", "Дравен", False, "start")
        stored = f"&amp;<b>Дрейвен</b>&lt; {MARK}x{MARK}Дрейвена&gt;"
        self.assertEqual(f"&amp;<b>Дравен</b>&lt; {MARK}x{MARK}Дравена&gt;", matcher.replace(stored)[0])

    def test_sentence_start_capital_is_kept(self):
        matcher = Matcher("дрейвен", "дравен", False, "word")
        self.assertEqual("Дравен і дравен", matcher.replace("Дрейвен і дрейвен")[0])


class ReplaceApiTests(ReplaceFixture):
    class Handler:
        def __init__(self, payload):
            self.payload = payload

        def read_json(self):
            return self.payload

    def call(self, path, payload):
        with patch.object(server, "storage", self.storage):
            return server.WorkbenchHandler.handle_api(self.Handler(payload), "POST", f"/api/projects/{self.project_id}/{path}")

    def test_routes(self):
        status, found = self.call("translation-find", self.request())
        self.assertEqual((200, 8), (status, found["total"]))
        status, done = self.call("translation-replace", self.request(returnChapterId=self.chapter_ids[0]))
        self.assertEqual((200, 8), (status, done["summary"]["matches"]))
        status, undone = self.call("translation-replace/restore", {"items": done["undo"]["items"], "chapterId": self.chapter_ids[0]})
        self.assertEqual((200, 5), (status, undone["restored"]))
        items = [{k: v for k, v in item.items() if k != "previous"} for item in done["undo"]["items"]]
        status, redone = self.call("translation-replace/apply", {"items": items})
        self.assertEqual((200, 5), (status, redone["applied"]))
        with self.assertRaises(ValueError):
            self.call("translation-replace", {**self.request(), "query": "Dreyven"})
        with patch.object(server, "storage", self.storage):
            status, _ = server.WorkbenchHandler.handle_api(self.Handler(self.request()), "POST", "/api/projects/nope/translation-find")
        self.assertEqual(404, status)


if __name__ == "__main__":
    unittest.main()
