import tempfile
import unittest
from pathlib import Path

from backend.storage import Storage


class ListGlossaryUsedInTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_entry_not_used_by_any_project_has_empty_used_in(self):
        self.storage.create_glossary_entry({"source": "wraith", "target": "привид"})

        [entry] = self.storage.list_glossary()

        self.assertEqual([], entry["usedIn"])

    def test_entry_used_by_a_project_reports_its_series_and_author(self):
        author = self.storage.create_author({"name": "Author One"})
        series = self.storage.create_series({"name": "Court of Pain"})
        project = self.storage.create_project({
            "title": "Fool Me Once",
            "authorId": author["authorId"],
            "seriesId": series["seriesId"],
        })
        entry = self.storage.create_glossary_entry({"source": "wraith", "target": "привид"})
        self.storage.update_project(project["projectId"], {"projectGlossaryEntryIds": [entry["glossaryEntryId"]]})

        [listed] = self.storage.list_glossary()

        self.assertEqual([{
            "projectId": project["projectId"],
            "projectTitle": "Fool Me Once",
            "seriesId": series["seriesId"],
            "seriesName": "Court of Pain",
            "authorId": author["authorId"],
            "authorName": "Author One",
        }], listed["usedIn"])

    def test_entry_used_by_multiple_projects_lists_all_of_them(self):
        author = self.storage.create_author({"name": "Author One"})
        project_a = self.storage.create_project({"title": "Book A", "authorId": author["authorId"]})
        project_b = self.storage.create_project({"title": "Book B", "authorId": author["authorId"]})
        entry = self.storage.create_glossary_entry({"source": "wraith", "target": "привид"})
        self.storage.update_project(project_a["projectId"], {"projectGlossaryEntryIds": [entry["glossaryEntryId"]]})
        self.storage.update_project(project_b["projectId"], {"projectGlossaryEntryIds": [entry["glossaryEntryId"]]})

        [listed] = self.storage.list_glossary()

        self.assertEqual(2, len(listed["usedIn"]))
        self.assertEqual(
            {"Book A", "Book B"},
            {item["projectTitle"] for item in listed["usedIn"]},
        )

    def test_project_without_series_reports_null_series_fields(self):
        author = self.storage.create_author({"name": "Author One"})
        project = self.storage.create_project({"title": "Standalone", "authorId": author["authorId"]})
        entry = self.storage.create_glossary_entry({"source": "wraith", "target": "привид"})
        self.storage.update_project(project["projectId"], {"projectGlossaryEntryIds": [entry["glossaryEntryId"]]})

        [listed] = self.storage.list_glossary()

        self.assertIsNone(listed["usedIn"][0]["seriesId"])
        self.assertIsNone(listed["usedIn"][0]["seriesName"])


if __name__ == "__main__":
    unittest.main()
