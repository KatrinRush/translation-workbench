import tempfile
import unittest
from pathlib import Path

from backend.qa.service import QaService
from backend.storage import Storage


class NarratorStorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_project_narrator_gender_round_trips_through_create_and_update(self):
        project = self.storage.create_project({"title": "Book", "narratorGender": "femn"})
        self.assertEqual("femn", project["narratorGender"])

        updated = self.storage.update_project(project["projectId"], {"title": "Book", "narratorGender": "masc"})
        self.assertEqual("masc", updated["narratorGender"])

        cleared = self.storage.update_project(project["projectId"], {"title": "Book", "narratorGender": None})
        self.assertIsNone(cleared["narratorGender"])

    def test_project_narrator_gender_rejects_invalid_value(self):
        project = self.storage.create_project({"title": "Book"})
        with self.assertRaises(ValueError):
            self.storage.update_project(project["projectId"], {"title": "Book", "narratorGender": "nonbinary"})

    def test_paragraph_narrator_change_marks_and_clears(self):
        project = self.storage.create_project({"title": "Book", "status": "translation"})
        structure = self.storage.save_book_structure(
            project["projectId"], "book.epub", "application/epub+zip", b"book",
            {"chapters": [{"title": "One", "elements": [{"type": "paragraph", "text": "Para"}]}]},
        )
        paragraph_id = structure["chapters"][0]["elements"][0]["paragraphId"]

        marked = self.storage.set_paragraph_narrator_change(paragraph_id, "masc")
        self.assertEqual({"paragraphId": paragraph_id, "narratorChange": "masc"}, marked)

        [paragraph] = self.storage.get_chapter_paragraphs(structure["chapters"][0]["chapterId"])
        self.assertEqual("masc", paragraph["narratorChange"])

        cleared = self.storage.set_paragraph_narrator_change(paragraph_id, None)
        self.assertIsNone(cleared["narratorChange"])

    def test_paragraph_narrator_change_rejects_invalid_value(self):
        project = self.storage.create_project({"title": "Book", "status": "translation"})
        structure = self.storage.save_book_structure(
            project["projectId"], "book.epub", "application/epub+zip", b"book",
            {"chapters": [{"title": "One", "elements": [{"type": "paragraph", "text": "Para"}]}]},
        )
        paragraph_id = structure["chapters"][0]["elements"][0]["paragraphId"]
        with self.assertRaises(ValueError):
            self.storage.set_paragraph_narrator_change(paragraph_id, "nonbinary")

    def test_paragraph_narrator_change_returns_none_for_unknown_paragraph(self):
        self.assertIsNone(self.storage.set_paragraph_narrator_change("missing", "masc"))


class EffectiveNarratorTests(unittest.TestCase):
    def _paragraphs(self, *narrator_changes):
        return [
            {"paragraphId": f"p{index}", "narratorChange": change}
            for index, change in enumerate(narrator_changes)
        ]

    def test_no_markers_uses_project_default(self):
        paragraphs = self._paragraphs(None, None, None)
        effective = QaService._effective_narrators("femn", paragraphs)
        self.assertEqual({"p0": "femn", "p1": "femn", "p2": "femn"}, effective)

    def test_missing_project_default_falls_back_to_third(self):
        paragraphs = self._paragraphs(None)
        effective = QaService._effective_narrators(None, paragraphs)
        self.assertEqual({"p0": "third"}, effective)

    def test_marker_switches_narrator_for_rest_of_chapter(self):
        paragraphs = self._paragraphs(None, None, "masc", None, "third", None)
        effective = QaService._effective_narrators("femn", paragraphs)
        self.assertEqual(
            {"p0": "femn", "p1": "femn", "p2": "masc", "p3": "masc", "p4": "third", "p5": "third"},
            effective,
        )


class BuildQualityPromptNarratorSectionTests(unittest.TestCase):
    def test_prompt_lists_one_narrator_line_per_paragraph_in_batch(self):
        paragraphs = [
            {"paragraphId": "p1", "originalText": "He ran.", "translationText": "Він біг."},
            {"paragraphId": "p2", "originalText": "She ran.", "translationText": "Вона бігла."},
        ]
        narrators = {"p1": "masc", "p2": "femn"}
        prompt = QaService._build_quality_prompt(paragraphs, {}, {"critical"}, narrators)

        self.assertIn("[p1]: оповідач — чоловік", prompt)
        self.assertIn("[p2]: оповідач — жінка", prompt)
        self.assertLess(prompt.index("=== СТАТЬ/ОСОБА ОПОВІДАЧА ==="), prompt.index("[p1]: оповідач"))
        self.assertLess(prompt.index("[p1]: оповідач"), prompt.index("Ти перевіряєш якість"))

    def test_unmapped_paragraph_defaults_to_third_person_label(self):
        paragraphs = [{"paragraphId": "p1", "originalText": "It rained.", "translationText": "Йшов дощ."}]
        prompt = QaService._build_quality_prompt(paragraphs, {}, {"critical"}, {})
        self.assertIn("[p1]: оповідач — третя особа", prompt)


if __name__ == "__main__":
    unittest.main()
