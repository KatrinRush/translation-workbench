"""«Обрати для файлу весь розділ з…»: bulk choice of the newest variant per paragraph, its undo and redo."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend import server, storage as storage_module
from backend.storage import Storage

MARK = ""  # footnote marker delimiter


class FakeHandler:
    def __init__(self, payload=None):
        self.payload = payload

    def read_json(self):
        return self.payload


class BulkFixture(unittest.TestCase):
    """Chapter 1, in book order:
    p0 claude(2 versions) + openai, chosen: current        p3 claude "Same" == current text, reviewed
    p1 claude + openai, reviewed                            p4 only openai
    p2 claude, has a footnote marker in its text            p5 nothing at all (never translated)
    Chapter 2 has one paragraph with a claude variant (must never be touched)."""

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "workbench.sqlite3"
        self.storage = Storage(self.database_path)
        self.project_id = self.storage.create_project({"title": "Bulk", "status": "translation"})["projectId"]
        self.storage.save_book_structure(
            self.project_id, "b.epub", "application/epub+zip", b"b",
            {"chapters": [
                {"title": "CHAPTER 1", "elements": [{"type": "paragraph", "text": f"Original {index}."} for index in range(6)]},
                {"title": "CHAPTER 2", "elements": [{"type": "paragraph", "text": "Other chapter."}]},
            ]},
        )
        chapters = self.storage.get_book_structure(self.project_id)["chapters"]
        self.chapter_id = chapters[0]["chapterId"]
        self.other_chapter_id = chapters[1]["chapterId"]
        self.ids = [element["paragraphId"] for element in chapters[0]["elements"]]
        self.other_id = chapters[1]["elements"][0]["paragraphId"]
        self.storage.update_paragraph(self.ids[0], "Поточний 0", False)
        self.storage.update_paragraph(self.ids[1], "Поточний 1", True)
        self.storage.update_paragraph(self.ids[2], f"Поточний 2{MARK}fn1{MARK}", False)
        self.storage.update_paragraph(self.ids[3], "Same", True)
        self.storage.update_paragraph(self.ids[4], "Поточний 4", False)
        self.storage.update_paragraph(self.other_id, "Поточний інший", False)
        with self.storage.connection() as connection:
            connection.execute(
                "INSERT INTO paragraph_footnotes(footnote_id, paragraph_id, note_text, created_at) VALUES ('fn1', ?, 'Примітка', 'x')", (self.ids[2],)
            )
        self.storage = Storage(self.database_path)  # start-up migration: the existing text becomes the chosen «Поточний»
        add = self.storage.add_translation_variant
        add(self.ids[0], "claude", "Claude 0 v1")
        add(self.ids[0], "claude", "Claude 0 v2")
        add(self.ids[0], "openai", "GPT 0")
        add(self.ids[1], "claude", "Claude 1")
        add(self.ids[1], "openai", "GPT 1")
        add(self.ids[2], "claude", "Claude 2")
        add(self.ids[3], "claude", "Same")
        add(self.ids[4], "openai", "GPT 4")
        add(self.other_id, "claude", "Claude other")

    def tearDown(self):
        self.temporary_directory.cleanup()

    def state(self, paragraph_id):
        row = self.storage.get_paragraph(paragraph_id)
        engine = next((v["engine"] for v in row["translationVariants"] if v["variantId"] == row["selectedVariantId"]), None)
        return {"text": row["translationText"], "reviewed": row["reviewed"], "selected": row["selectedVariantId"], "engine": engine}

    def snapshot(self):
        return {pid: self.state(pid) for pid in (*self.ids, self.other_id)}

    def bulk(self, engine, include_reviewed=False, dry_run=False):
        return self.storage.select_chapter_variants(self.chapter_id, engine, include_reviewed, dry_run)

    def footnotes(self, paragraph_id):
        with sqlite3.connect(self.database_path) as connection:
            return [row[0] for row in connection.execute("SELECT footnote_id FROM paragraph_footnotes WHERE paragraph_id = ?", (paragraph_id,))]


class BulkSelectionTests(BulkFixture):
    def test_the_newest_version_of_the_engine_is_chosen_where_one_exists(self):
        result = self.bulk("claude")
        self.assertEqual({"changed": 2, "withoutVariant": 2, "skippedReviewed": 2, "alreadySelected": 0, "movedFootnotes": 1, "reviewedUnmarked": 0, "proofreadUnmarked": 0}, result["summary"])
        # p0: the newest of two Claude versions; p2: Claude text with its footnote marker carried to the end
        self.assertEqual(("Claude 0 v2", "claude"), (self.state(self.ids[0])["text"], self.state(self.ids[0])["engine"]))
        self.assertEqual(f"Claude 2{MARK}fn1{MARK}", self.state(self.ids[2])["text"])
        self.assertEqual(["fn1"], self.footnotes(self.ids[2]))
        self.assertEqual(["Claude 0 v2", "Claude 2"], [item["translationText"].replace(MARK + "fn1" + MARK, "") for item in result["paragraphs"]])
        self.assertEqual(2, len(result["undo"]["items"]))

    def test_paragraphs_without_the_variant_and_other_chapters_are_not_touched(self):
        before = self.snapshot()
        self.bulk("claude", include_reviewed=True)
        after = self.snapshot()
        for paragraph_id in (self.ids[4], self.ids[5], self.other_id):  # no Claude variant / another chapter
            self.assertEqual(before[paragraph_id], after[paragraph_id])
        self.assertEqual((None, None), (after[self.ids[5]]["text"], after[self.ids[5]]["selected"]))

    def test_proofread_paragraphs_are_skipped_by_default_and_counted(self):
        before = self.state(self.ids[1])
        result = self.bulk("claude")
        self.assertEqual(before, self.state(self.ids[1]))
        self.assertEqual(2, result["summary"]["skippedReviewed"])  # p1 and p3

    def test_including_proofread_clears_reviewed_only_where_the_text_changes(self):
        result = self.bulk("claude", include_reviewed=True)
        self.assertEqual({"changed": 4, "withoutVariant": 2, "skippedReviewed": 0, "alreadySelected": 0}, {k: result["summary"][k] for k in ("changed", "withoutVariant", "skippedReviewed", "alreadySelected")})
        self.assertEqual(1, result["summary"]["reviewedUnmarked"])  # only p1 loses «Перевірено»; p3 has the same text
        self.assertEqual((False, "Claude 1", "claude"), tuple(self.state(self.ids[1])[k] for k in ("reviewed", "text", "engine")))  # text changed
        self.assertEqual((True, "Same", "claude"), tuple(self.state(self.ids[3])[k] for k in ("reviewed", "text", "engine")))  # same text: still proofread

    def test_a_paragraph_that_already_has_the_newest_version_chosen_is_left_alone(self):
        self.bulk("claude")
        before = self.snapshot()
        result = self.bulk("claude")
        self.assertEqual({"changed": 0, "withoutVariant": 2, "skippedReviewed": 2, "alreadySelected": 2, "movedFootnotes": 0, "reviewedUnmarked": 0, "proofreadUnmarked": 0}, result["summary"])
        self.assertEqual(([], []), (result["paragraphs"], result["undo"]["items"]))
        self.assertEqual(before, self.snapshot())

    def test_an_older_version_chosen_by_hand_is_replaced_by_the_newest(self):
        versions = [v for v in self.storage.get_paragraph(self.ids[0])["translationVariants"] if v["engine"] == "claude"]
        self.storage.select_translation_variant(self.ids[0], versions[0]["variantId"])
        self.assertEqual("Claude 0 v1", self.state(self.ids[0])["text"])
        self.assertEqual(2, self.bulk("claude")["summary"]["changed"])  # p0 (older -> newest) and p2
        self.assertEqual("Claude 0 v2", self.state(self.ids[0])["text"])

    def test_the_engines_of_the_dialog_all_work(self):
        self.bulk("claude")
        gpt = self.bulk("openai")
        self.assertEqual({"changed": 2, "withoutVariant": 3}, {k: gpt["summary"][k] for k in ("changed", "withoutVariant")})  # p0, p4 (p1 reviewed)
        self.assertEqual("GPT 0", self.state(self.ids[0])["text"])
        self.assertEqual("GPT 4", self.state(self.ids[4])["text"])
        self.storage.add_translation_variant(self.ids[0], "deepl", "DeepL 0")
        self.assertEqual(1, self.bulk("deepl")["summary"]["changed"])
        back = self.bulk("current")  # «Поточний» is a variant like any other
        self.assertEqual(("Поточний 0", "current"), (self.state(self.ids[0])["text"], self.state(self.ids[0])["engine"]))
        self.assertGreaterEqual(back["summary"]["changed"], 2)

    def test_manual_and_unknown_engines_are_refused(self):
        for engine in ("manual", "grok", "", None, 5):
            with self.subTest(engine=engine), self.assertRaises(ValueError):
                self.bulk(engine)
        self.assertIsNone(self.storage.select_chapter_variants("nope", "claude"))

    def test_it_is_all_or_nothing(self):
        before = self.snapshot()
        original = Storage._choose_variant
        calls = []

        def fail_second(self_, connection, row, variant):
            calls.append(row["paragraph_id"])
            if len(calls) == 2:
                raise RuntimeError("boom")
            return original(self_, connection, row, variant)

        with patch.object(Storage, "_choose_variant", fail_second), self.assertRaises(RuntimeError):
            self.bulk("claude")
        self.assertEqual(2, len(calls))
        self.assertEqual(before, self.snapshot())


class DryRunTests(BulkFixture):
    def test_a_dry_run_writes_nothing_and_shows_up_to_three_shortened_examples(self):
        long_text = "Дуже довгий абзац " * 20
        self.storage.add_translation_variant(self.ids[0], "claude", long_text)
        before = self.snapshot()
        result = self.bulk("claude", dry_run=True)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(([], [], True), (result["paragraphs"], result["undo"]["items"], result["dryRun"]))
        self.assertEqual(2, result["summary"]["changed"])
        first = result["examples"][0]
        self.assertEqual((1, "Поточний 0", True), (first["number"], first["before"], first["after"].endswith("…")))
        self.assertLessEqual(len(first["after"]), 80)
        self.assertEqual("Поточний 2", result["examples"][1]["before"])  # footnote markers are not shown
        self.assertNotIn(MARK, str(result["examples"]))

    def test_at_most_three_examples_and_only_for_paragraphs_that_would_change(self):
        result = self.bulk("claude", include_reviewed=True, dry_run=True)
        self.assertEqual(4, result["summary"]["changed"])
        self.assertEqual([1, 2, 3], [item["number"] for item in result["examples"]])
        self.assertEqual("Поточний 1", result["examples"][1]["before"])
        self.assertTrue(result["examples"][1]["reviewed"])

    def test_the_dry_run_summary_equals_the_real_one(self):
        dry = self.bulk("claude", include_reviewed=True, dry_run=True)["summary"]
        real = self.bulk("claude", include_reviewed=True)["summary"]
        self.assertEqual(dry, real)


class UndoRedoTests(BulkFixture):
    def test_undo_restores_selection_text_reviewed_and_footnotes_of_every_changed_paragraph(self):
        before = self.snapshot()
        result = self.bulk("claude", include_reviewed=True)
        self.assertNotEqual(before, self.snapshot())
        restored = self.storage.restore_chapter_selection(self.chapter_id, result["undo"]["items"])
        self.assertEqual(4, restored["restored"])
        self.assertEqual(before, self.snapshot())
        self.assertEqual(["fn1"], self.footnotes(self.ids[2]))
        self.assertIn(MARK + "fn1" + MARK, self.state(self.ids[2])["text"])
        self.assertTrue(self.state(self.ids[1])["reviewed"])  # the proofread flag is back

    def test_undo_recreates_a_selected_version_pruned_by_the_choice(self):
        with patch.object(storage_module, "VARIANT_VERSIONS_KEPT", 1):
            versions = [v for v in self.storage.get_paragraph(self.ids[0])["translationVariants"] if v["engine"] == "claude"]
            self.storage.select_translation_variant(self.ids[0], versions[0]["variantId"])  # the older Claude version is in the file
            before = self.state(self.ids[0])
            result = self.bulk("openai")
            remaining = [v["variantId"] for v in self.storage.get_paragraph(self.ids[0])["translationVariants"]]
            self.assertNotIn(versions[0]["variantId"], remaining)  # pruned: only the newest Claude version is kept
            self.storage.restore_chapter_selection(self.chapter_id, result["undo"]["items"])
        self.assertEqual(before, self.state(self.ids[0]))

    def test_redo_applies_the_same_variants_again_and_can_be_undone_again(self):
        first = self.bulk("claude", include_reviewed=True)
        after_choice = self.snapshot()
        self.storage.restore_chapter_selection(self.chapter_id, first["undo"]["items"])
        before = self.snapshot()
        self.storage.add_translation_variant(self.ids[0], "claude", "Claude 0 v3 (newer than the redo)")
        redone = self.storage.apply_chapter_selection(self.chapter_id, [{"paragraphId": i["paragraphId"], "variantId": i["variantId"]} for i in first["undo"]["items"]])
        self.assertEqual(4, redone["applied"])
        self.assertEqual("Claude 0 v2", self.state(self.ids[0])["text"])  # exactly the earlier variants, not the newest
        for paragraph_id in self.ids[1:]:
            self.assertEqual(after_choice[paragraph_id], self.state(paragraph_id))
        self.storage.restore_chapter_selection(self.chapter_id, redone["undo"]["items"])
        self.assertEqual(before, self.snapshot())

    def test_undo_and_redo_are_all_or_nothing(self):
        result = self.bulk("claude")
        after = self.snapshot()
        items = [*result["undo"]["items"], {"paragraphId": self.other_id, "previous": {}}]  # a paragraph of another chapter
        with self.assertRaises(ValueError):
            self.storage.restore_chapter_selection(self.chapter_id, items)
        self.assertEqual(after, self.snapshot())
        good = result["undo"]["items"][0]
        for items in (
            [{"paragraphId": good["paragraphId"], "previous": good["previous"]}, {"paragraphId": self.ids[2], "previous": "oops"}],
            [good, good],  # the same paragraph twice
            "not a list",
            [{"paragraphId": 5, "previous": {}}],
            [{"previous": {}}],
        ):
            with self.subTest(items=str(items)[:50]), self.assertRaises(ValueError):
                self.storage.restore_chapter_selection(self.chapter_id, items)
        self.assertEqual(after, self.snapshot())
        before = self.snapshot()
        with self.assertRaises(ValueError):
            self.storage.apply_chapter_selection(self.chapter_id, [
                {"paragraphId": self.ids[4], "variantId": self.storage.get_paragraph(self.ids[4])["translationVariants"][-1]["variantId"]},
                {"paragraphId": self.ids[0], "variantId": "variant-does-not-exist"},
            ])
        self.assertEqual(before, self.snapshot())
        self.assertIsNone(self.storage.restore_chapter_selection("nope", []))
        self.assertIsNone(self.storage.apply_chapter_selection("nope", []))

    def test_a_variant_of_another_paragraph_cannot_be_applied(self):
        foreign = self.storage.get_paragraph(self.ids[1])["translationVariants"][-1]["variantId"]
        with self.assertRaises(ValueError):
            self.storage.apply_chapter_selection(self.chapter_id, [{"paragraphId": self.ids[0], "variantId": foreign}])


class BulkApiTests(BulkFixture):
    def api(self, path, payload):
        with patch.object(server, "storage", self.storage):
            return server.WorkbenchHandler.handle_api(FakeHandler(payload), "POST", path)

    def test_select_undo_redo_through_the_api(self):
        status, result = self.api(f"/api/chapters/{self.chapter_id}/select-variants", {"engine": "claude"})
        self.assertEqual((200, 2), (status, result["summary"]["changed"]))
        status, undone = self.api(f"/api/chapters/{self.chapter_id}/restore-selection", {"items": result["undo"]["items"]})
        self.assertEqual((200, 2), (status, undone["restored"]))
        status, redone = self.api(f"/api/chapters/{self.chapter_id}/apply-selection", {"items": [{"paragraphId": i["paragraphId"], "variantId": i["variantId"]} for i in result["undo"]["items"]]})
        self.assertEqual((200, 2), (status, redone["applied"]))

    def test_dry_run_flag_and_errors(self):
        status, result = self.api(f"/api/chapters/{self.chapter_id}/select-variants", {"engine": "claude", "includeReviewed": True, "dryRun": True})
        self.assertEqual((200, True, 4), (status, result["dryRun"], result["summary"]["changed"]))
        self.assertEqual(404, self.api("/api/chapters/nope/select-variants", {"engine": "claude"})[0])
        self.assertEqual(404, self.api("/api/chapters/nope/restore-selection", {"items": []})[0])
        self.assertEqual(404, self.api("/api/chapters/nope/apply-selection", {"items": []})[0])
        self.assertEqual(400, self.api(f"/api/chapters/{self.chapter_id}/select-variants", {"engine": "claude", "includeReviewed": "yes"})[0])
        with self.assertRaises(ValueError):  # the HTTP handler turns this into a 400
            self.api(f"/api/chapters/{self.chapter_id}/select-variants", {"engine": "manual"})


class SingleChoiceUnchangedTests(BulkFixture):
    """The single «У файл» and its undo share the refactored core: same behaviour as before."""

    def test_single_choice_and_undo(self):
        variant = next(v for v in self.storage.get_paragraph(self.ids[2])["translationVariants"] if v["engine"] == "claude")
        before = self.state(self.ids[2])
        chosen = self.storage.select_translation_variant(self.ids[2], variant["variantId"])
        self.assertEqual(["fn1"], chosen["movedFootnoteIds"])
        self.assertEqual(f"Claude 2{MARK}fn1{MARK}", chosen["translationText"])
        self.storage.restore_translation_selection(self.ids[2], chosen["previous"])
        self.assertEqual(before, self.state(self.ids[2]))


if __name__ == "__main__":
    unittest.main()
