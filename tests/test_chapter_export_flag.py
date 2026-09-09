import tempfile
import unittest
from pathlib import Path
import sqlite3

from backend.storage import Storage


class ChapterExportFlagTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")
        project = self.storage.create_project({"title": "Export flags", "status": "translation"})
        self.project_id = project["projectId"]
        self.storage.save_book_structure(
            self.project_id,
            "book.epub",
            "application/epub+zip",
            b"book",
            {"chapters": [{"title": "One", "elements": [{"type": "paragraph", "text": "Text"}]}]},
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_export_flag_defaults_to_false_and_can_be_updated(self):
        chapter = self.storage.get_book_structure(self.project_id)["chapters"][0]
        self.assertFalse(chapter["excludeFromExport"])

        self.assertTrue(self.storage.set_chapter_export_flag(chapter["chapterId"], True))

        updated = self.storage.get_book_structure(self.project_id)["chapters"][0]
        self.assertTrue(updated["excludeFromExport"])

    def test_export_flag_returns_false_for_unknown_chapter(self):
        self.assertFalse(self.storage.set_chapter_export_flag("missing", True))

    def test_existing_chapters_table_is_migrated_with_false_default(self):
        legacy_database = Path(self.temporary_directory.name) / "legacy.sqlite3"
        with sqlite3.connect(legacy_database) as connection:
            connection.execute(
                "CREATE TABLE book_chapters ("
                "chapter_id TEXT PRIMARY KEY, book_id TEXT NOT NULL, chapter_index INTEGER NOT NULL, "
                "title TEXT, translation_title TEXT, title_reviewed INTEGER NOT NULL DEFAULT 0, "
                "word_count INTEGER NOT NULL DEFAULT 0, paragraph_count INTEGER NOT NULL DEFAULT 0, "
                "ai_analysis_results TEXT NOT NULL DEFAULT '{}', UNIQUE(book_id, chapter_index))"
            )
            connection.execute(
                "INSERT INTO book_chapters(chapter_id, book_id, chapter_index, title) VALUES ('chapter-old', 'book-old', 1, 'Old')"
            )

        Storage(legacy_database)

        with sqlite3.connect(legacy_database) as connection:
            value = connection.execute(
                "SELECT exclude_from_export FROM book_chapters WHERE chapter_id = 'chapter-old'"
            ).fetchone()[0]
        self.assertEqual(0, value)


if __name__ == "__main__":
    unittest.main()