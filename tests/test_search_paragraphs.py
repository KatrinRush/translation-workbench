import tempfile
import unittest
from pathlib import Path

from backend.storage import Storage


class SearchParagraphsTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")
        project = self.storage.create_project({"title": "Search project", "status": "translation"})
        self.project_id = project["projectId"]
        self.storage.save_book_structure(
            self.project_id,
            "book.epub",
            "application/epub+zip",
            b"book",
            {"chapters": [{"title": "One", "elements": [
                {"type": "paragraph", "text": "The cat sat on the mat in a category of its own."},
                {"type": "paragraph", "text": "Nothing relevant here."},
            ]}]},
        )
        structure = self.storage.get_book_structure(self.project_id)
        self.paragraph_id = structure["chapters"][0]["elements"][0]["paragraphId"]
        self.storage.update_paragraph(self.paragraph_id, "Кіт сидів на килимку в категорії власній.", False)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_exact_mode_matches_whole_word_only(self):
        result = self.storage.search_paragraphs(
            "cat", scope="project", project_id=self.project_id, match_mode="exact"
        )
        self.assertEqual(1, result["total"])

        result = self.storage.search_paragraphs(
            "categ", scope="project", project_id=self.project_id, match_mode="exact"
        )
        self.assertEqual(0, result["total"])

    def test_partial_mode_matches_substrings_inside_words(self):
        result = self.storage.search_paragraphs(
            "categ", scope="project", project_id=self.project_id, match_mode="partial"
        )
        self.assertEqual(1, result["total"])
        self.assertIn("⟦categ⟧", result["results"][0]["snippet"])

    def test_partial_mode_is_case_insensitive_for_cyrillic(self):
        result = self.storage.search_paragraphs(
            "КИЛИМ", scope="project", project_id=self.project_id, match_mode="partial"
        )
        self.assertEqual(1, result["total"])
        self.assertEqual("translation_text", result["field"])

    def test_partial_mode_finds_nothing_for_absent_substring(self):
        result = self.storage.search_paragraphs(
            "zzz", scope="project", project_id=self.project_id, match_mode="partial"
        )
        self.assertEqual(0, result["total"])

    def test_unknown_match_mode_raises(self):
        with self.assertRaises(ValueError):
            self.storage.search_paragraphs(
                "cat", scope="project", project_id=self.project_id, match_mode="fuzzy"
            )


if __name__ == "__main__":
    unittest.main()
