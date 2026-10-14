"""«Вичитано» (proofread): the second stage after «Перевірено» (reviewed), and the progress figures built on it."""
import contextlib
import sqlite3
import tempfile
import unittest
from pathlib import Path

from backend.storage import Storage
from backend.translations.chunker import chapter_paragraph_units
from tests.test_translation_queue import QueueFixture


class ProofreadStorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "workbench.sqlite3"
        self.storage = Storage(self.database_path)
        self.project_id = self.storage.create_project({"title": "Proofread", "status": "translation"})["projectId"]
        self.storage.save_book_structure(
            self.project_id, "b.epub", "application/epub+zip", b"b",
            {"chapters": [
                {"title": "One", "elements": [
                    {"type": "paragraph", "text": "One two three four."},          # 4 words
                    {"type": "paragraph", "text": "Five six."},                     # 2 words
                    {"type": "paragraph", "text": "Seven eight nine."},             # 3 words
                    {"type": "paragraph", "text": "Service line here."},            # service text
                    {"type": "paragraph", "text": "   "},                            # no original text
                ]},
                {"title": "Two", "elements": [{"type": "paragraph", "text": "Ten eleven twelve thirteen five."}]},   # 5 words
                {"title": "Hidden", "elements": [{"type": "paragraph", "text": "Never exported text."}]},
            ]},
        )
        structure = self.storage.get_book_structure(self.project_id)
        self.chapter_ids = [chapter["chapterId"] for chapter in structure["chapters"]]
        self.ids = [[element["paragraphId"] for element in chapter["elements"]] for chapter in structure["chapters"]]

    def tearDown(self):
        self.temporary_directory.cleanup()

    def paragraph(self, paragraph_id):
        return self.storage.get_paragraph(paragraph_id)

    def columns(self):
        with sqlite3.connect(self.database_path) as raw:
            return [row[1] for row in raw.execute("PRAGMA table_info(book_paragraphs)")]

    # --- data -------------------------------------------------------------------------------------------

    def test_migration_adds_the_column_once_with_zero_as_the_default(self):
        with sqlite3.connect(self.database_path) as raw:  # an older database: no such column
            raw.execute("ALTER TABLE book_paragraphs DROP COLUMN proofread")
        self.assertNotIn("proofread", self.columns())
        Storage(self.database_path)
        Storage(self.database_path)  # idempotent
        self.assertEqual(1, self.columns().count("proofread"))
        self.assertEqual(1, self.columns().count("reviewed"))              # «Перевірено» is untouched
        self.assertFalse(self.paragraph(self.ids[0][0])["proofread"])

    def test_the_marks_are_independent_and_saved_with_the_paragraph(self):
        pid = self.ids[0][0]
        self.storage.update_paragraph(pid, "Переклад", False, proofread=True)
        saved = self.paragraph(pid)
        self.assertEqual((False, True), (saved["reviewed"], saved["proofread"]))   # proofread does not need reviewed
        self.storage.save_paragraph_edit(pid, "Переклад", True)                    # omitted: proofread stays
        self.assertEqual((True, True), (self.paragraph(pid)["reviewed"], self.paragraph(pid)["proofread"]))
        self.storage.save_paragraph_edit(pid, "Переклад", True, proofread=False)
        self.assertEqual((True, False), (self.paragraph(pid)["reviewed"], self.paragraph(pid)["proofread"]))
        element = self.storage.get_book_structure(self.project_id)["chapters"][0]["elements"][0]
        self.assertIn("proofread", element)
        self.assertEqual([self.paragraph(pid)["proofread"]], [element["proofread"]])

    def test_manual_edits_never_clear_proofread(self):
        pid = self.ids[0][0]
        self.storage.update_paragraph(pid, "Переклад", False, proofread=True)
        self.storage.save_paragraph_edit(pid, "Інший текст у редакторі", False)
        self.assertTrue(self.paragraph(pid)["proofread"])

    # --- «У файл» and undo -----------------------------------------------------------------------------

    def test_choosing_another_text_clears_both_marks_the_same_text_keeps_them_and_undo_restores(self):
        pid = self.ids[0][0]
        self.storage.add_translation_variant(pid, "claude", "Текст Claude", "m")      # chosen automatically
        self.storage.add_translation_variant(pid, "gemini", "Текст Gemini", "m")
        self.storage.update_paragraph(pid, "Текст Claude", True, proofread=True)
        variants = {v["engine"]: v["variantId"] for v in self.paragraph(pid)["translationVariants"]}

        same = self.storage.select_translation_variant(pid, variants["claude"])
        self.assertEqual((True, True), (same["reviewed"], same["proofread"]))             # the same chosen text

        other = self.storage.select_translation_variant(pid, variants["gemini"])
        self.assertEqual((False, False), (other["reviewed"], other["proofread"]))        # the text changed
        self.assertEqual({"reviewed": True, "proofread": True}, {k: other["previous"][k] for k in ("reviewed", "proofread")})

        restored = self.storage.restore_translation_selection(pid, other["previous"])
        self.assertEqual((True, True), (restored["reviewed"], restored["proofread"]))

    def test_bulk_choice_skips_proofread_unless_included_and_then_clears_the_mark(self):
        first, second = self.ids[0][0], self.ids[0][1]
        for pid in (first, second):
            self.storage.add_translation_variant(pid, "claude", f"Claude {pid[-4:]}", "m")
            self.storage.add_translation_variant(pid, "gemini", f"Gemini {pid[-4:]}", "m")
        self.storage.update_paragraph(first, self.paragraph(first)["translationText"], False, proofread=True)
        chapter_id = self.chapter_ids[0]

        skipped = self.storage.select_chapter_variants(chapter_id, "gemini")
        self.assertEqual({"changed": 1, "skippedReviewed": 1}, {k: skipped["summary"][k] for k in ("changed", "skippedReviewed")})
        self.assertTrue(self.paragraph(first)["proofread"])

        preview = self.storage.select_chapter_variants(chapter_id, "gemini", include_reviewed=True, dry_run=True)
        self.assertEqual(1, preview["summary"]["proofreadUnmarked"])
        applied = self.storage.select_chapter_variants(chapter_id, "gemini", include_reviewed=True)
        self.assertEqual(1, applied["summary"]["changed"])
        self.assertFalse(self.paragraph(first)["proofread"])

    # --- replace --------------------------------------------------------------------------------------------

    def test_replace_counts_proofread_paragraphs_and_keeps_their_mark(self):
        pid = self.ids[0][0]
        self.storage.update_paragraph(pid, "Дрейвен прийшов.", False, proofread=True)
        self.storage.update_paragraph(self.ids[0][1], "Дрейвен пішов.", False)
        request = {"query": "Дрейвен", "replacement": "Андрій", "scope": "project", "mode": "word"}
        found = self.storage.find_translation_matches(self.project_id, request)
        self.assertEqual((2, 1), (found["paragraphs"], found["proofreadParagraphs"]))
        self.storage.replace_in_translation(self.project_id, {**request, "confirmed": True})
        replaced = self.paragraph(pid)
        self.assertIn("Андрій", replaced["translationText"])
        self.assertTrue(replaced["proofread"])                                           # a replacement never clears it

    # --- translation and the queue --------------------------------------------------------------------------

    def test_a_whole_chapter_translation_skips_reviewed_and_proofread_paragraphs(self):
        chapter = self.storage.get_book_structure(self.project_id)["chapters"][0]
        self.storage.update_paragraph(self.ids[0][0], "Є", False, proofread=True)
        self.storage.update_paragraph(self.ids[0][1], "Є", True)
        chapter = self.storage.get_book_structure(self.project_id)["chapters"][0]
        units = chapter_paragraph_units(chapter, skip_reviewed=True)
        self.assertNotIn(self.ids[0][0], [unit.paragraph_id for unit in units])
        self.assertNotIn(self.ids[0][1], [unit.paragraph_id for unit in units])
        self.assertIn(self.ids[0][2], [unit.paragraph_id for unit in units])

    # --- progress ------------------------------------------------------------------------------------------------

    def mark_progress(self):
        self.storage.update_paragraph(self.ids[0][3], "Службовий", True, is_service=True, proofread=True)   # not counted
        self.storage.update_paragraph(self.ids[0][0], "П1", True, proofread=True)                           # 4 words: all three
        self.storage.update_paragraph(self.ids[0][1], "П2", True)                                           # 2 words: translated + reviewed
        self.storage.update_paragraph(self.ids[0][2], "П3", False)                                          # 3 words: translated only
        self.storage.update_paragraph(self.ids[1][0], "П4", False, proofread=True)                          # 5 words: translated + proofread
        self.storage.update_paragraph(self.ids[2][0], "Приховане", True, proofread=True)                    # «Не експортувати»
        self.storage.set_chapter_export_flag(self.chapter_ids[2], True)

    def test_aggregates_count_paragraphs_and_words_without_service_empty_or_excluded_text(self):
        self.mark_progress()
        progress = self.storage.project_progress(self.project_id)
        paragraphs, words = progress["paragraphs"], progress["words"]
        # denominator: 3 + 1 paragraphs (the service line, the empty original and the hidden chapter are out)
        self.assertEqual((4, 4, 2, 2), tuple(paragraphs[key] for key in ("total", "translated", "reviewed", "proofread")))
        self.assertEqual((14, 14, 6, 9), tuple(words[key] for key in ("total", "translated", "reviewed", "proofread")))
        self.assertEqual({"translated": 100.0, "reviewed": 50.0, "proofread": 50.0, "overall": 66.7}, paragraphs["percent"])
        self.assertAlmostEqual((100 + 6 / 14 * 100 + 9 / 14 * 100) / 3, words["percent"]["overall"], places=1)
        # the overall figure is the mean of the three percents (equal weights)
        percent = paragraphs["percent"]
        self.assertAlmostEqual((percent["translated"] + percent["reviewed"] + percent["proofread"]) / 3, percent["overall"], places=1)

    def test_every_chapter_has_its_own_figures_and_the_excluded_one_is_listed_but_not_summed(self):
        self.mark_progress()
        chapters = self.storage.project_progress(self.project_id)["chapters"]
        self.assertEqual([False, False, True], [chapter["excluded"] for chapter in chapters])
        self.assertEqual((3, 3, 2, 1), tuple(chapters[0]["paragraphs"][key] for key in ("total", "translated", "reviewed", "proofread")))
        self.assertEqual((1, 1, 0, 1), tuple(chapters[1]["paragraphs"][key] for key in ("total", "translated", "reviewed", "proofread")))
        self.assertEqual(1, chapters[2]["paragraphs"]["total"])          # listed with its own figures
        self.assertIsNone(self.storage.project_progress("no-such-project"))

    def test_the_project_list_carries_the_figures_of_both_units_and_keeps_the_old_key(self):
        self.mark_progress()
        other = self.storage.create_project({"title": "No book", "status": "translation"})["projectId"]
        listed = {item["projectId"]: item["progress"] for item in self.storage.list_projects()}
        self.assertEqual(67, listed[self.project_id]["progress"])                       # round(66.7): what older clients read
        self.assertEqual(4, listed[self.project_id]["paragraphs"]["total"])
        self.assertEqual(14, listed[self.project_id]["words"]["total"])
        self.assertEqual(0, listed[other]["progress"])                                  # a project without a book
        self.assertEqual(0, listed[other]["paragraphs"]["total"])

    def test_the_project_list_is_one_aggregate_query_whatever_the_number_of_projects(self):
        for number in range(5):
            self.storage.create_project({"title": f"Another {number}", "status": "translation"})
        statements = []
        original = self.storage.connection

        @contextlib.contextmanager
        def traced():
            with original() as connection:
                connection.set_trace_callback(statements.append)
                yield connection

        self.storage.connection = traced
        self.storage.list_projects()
        selects = [sql for sql in statements if sql.lstrip().upper().startswith("SELECT") and "book_paragraphs" in sql]
        self.assertEqual(1, len(selects))                                                 # one query, not one per project


class ProofreadQueueTests(QueueFixture):
    def test_the_queue_plan_skips_proofread_paragraphs_like_reviewed_ones(self):
        self.storage.update_paragraph(self.ids[0][2], "Вичитаний у другий спосіб", False, proofread=True)
        estimate = self.queues.estimate(self.project_id, {"mode": "untranslated"})
        self.assertEqual([1, 2, 4], [chapter["number"] for chapter in estimate["chapters"]])
        self.assertEqual([1, 2, 3], [chapter["paragraphs"] for chapter in estimate["chapters"]])  # chapter 1: only p3 is left
        self.assertEqual(2, estimate["skipped"]["reviewedParagraphs"])                           # p1 (reviewed) and p2 (proofread)
        including = self.queues.estimate(self.project_id, {"mode": "untranslated", "includeTranslated": True})
        self.assertEqual([2, 2, 3], [chapter["paragraphs"] for chapter in including["chapters"]])


if __name__ == "__main__":
    unittest.main()
