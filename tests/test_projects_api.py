import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend import server
from backend.storage import Storage


class FakeHandler:
    def __init__(self, payload=None):
        self.payload = payload

    def read_json(self):
        return self.payload


class ProjectsApiResponseTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")
        self.project = self.storage.create_project({
            "title": "Response Shape",
            "authorId": None,
            "seriesId": None,
            "status": "analysis",
            "analysisResult": {"chapters": [{"elements": [{"type": "paragraph", "text": "large content"}]}]},
            "projectRuleIds": [],
            "projectGlossaryEntryIds": [],
            "inheritedRules": [],
            "inheritedGlossary": [],
        })

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_projects_list_returns_only_card_metadata(self):
        with patch.object(server, "storage", self.storage):
            status, projects = server.WorkbenchHandler.handle_api(FakeHandler(), "GET", "/api/projects")

        self.assertEqual(status, 200)
        self.assertEqual(len(projects), 1)
        self.assertEqual(set(projects[0]), {"projectId", "title", "authorId", "seriesId", "status"})
        self.assertNotIn("analysisResult", projects[0])

    def test_project_detail_preserves_full_response(self):
        with patch.object(server, "storage", self.storage):
            status, project = server.WorkbenchHandler.handle_api(
                FakeHandler(), "GET", f"/api/projects/{self.project['projectId']}"
            )

        self.assertEqual(status, 200)
        self.assertEqual(project["analysisResult"], {
            "chapters": [{"elements": [{"type": "paragraph", "text": "large content"}]}]
        })
        self.assertIn("projectRuleIds", project)
        self.assertIn("inheritedGlossary", project)

    def test_translation_rules_persist_on_project(self):
        self.storage.save_book_structure(
            self.project["projectId"],
            "book.epub",
            "application/epub+zip",
            b"book",
            {"chapters": []},
        )

        updated = self.storage.update_project_translation_rules(
            self.project["projectId"],
            "Keep dialogue informal.",
        )

        self.assertEqual("Keep dialogue informal.", updated["translationRules"])
        self.assertEqual(
            "Keep dialogue informal.",
            self.storage.get_project(self.project["projectId"])["translationRules"],
        )
        self.assertIsNotNone(self.storage.get_book_structure(self.project["projectId"]))

    def test_ai_configuration_is_saved_and_returned(self):
        configuration = {
            "translationConnectionId": "deepl-connection",
            "orchestrationConnectionId": "openai-connection",
            "analysisConnectionIds": ["openai-connection", "gemini-connection"],
            "qaConnectionIds": ["gemini-connection", "claude-connection"],
        }

        updated = self.storage.update_project(self.project["projectId"], {"aiConfiguration": configuration})

        self.assertEqual(configuration, updated["aiConfiguration"])
        self.assertEqual(configuration, self.storage.get_project(self.project["projectId"])["aiConfiguration"])

    def test_existing_project_has_empty_ai_configuration_by_default(self):
        self.assertEqual({}, self.project["aiConfiguration"])

    def test_ai_configuration_can_be_updated(self):
        self.storage.update_project(
            self.project["projectId"],
            {"aiConfiguration": {"translationConnectionId": "deepl-connection"}},
        )

        updated = self.storage.update_project(
            self.project["projectId"],
            {"aiConfiguration": {"qaConnectionIds": ["claude-connection"]}},
        )

        self.assertEqual({"qaConnectionIds": ["claude-connection"]}, updated["aiConfiguration"])

    def test_unknown_ai_connection_is_rejected_by_project_api(self):
        with patch.object(server, "storage", self.storage):
            status, response = server.WorkbenchHandler.handle_api(
                FakeHandler({"aiConfiguration": {"translationConnectionId": "missing-connection"}}),
                "PUT",
                f"/api/projects/{self.project['projectId']}",
            )

        self.assertEqual(400, status)
        self.assertIn("unknown connection", response["error"])

        with patch.object(server, "storage", self.storage):
            status, response = server.WorkbenchHandler.handle_api(
                FakeHandler({
                    "title": "Invalid AI project",
                    "status": "new",
                    "aiConfiguration": {"qaConnectionIds": ["missing-connection"]},
                }),
                "POST",
                "/api/projects",
            )

        self.assertEqual(400, status)
        self.assertIn("unknown connection", response["error"])

    def test_structured_translation_glossary_and_provider_sync_persist(self):
        glossary = self.storage.upsert_project_translation_glossary(self.project["projectId"], {
            "sourceLanguage": "EN",
            "targetLanguage": "UK",
            "entries": [
                {"source": "dominant", "target": "домінант", "context": "Character role"},
            ],
            "contentHash": "content-hash",
        })
        self.storage.save_provider_glossary_sync(
            glossary["glossaryRuleId"], "connection-1", "deepl", "remote-1", "content-hash"
        )

        restored = self.storage.list_project_translation_glossaries(self.project["projectId"])[0]

        self.assertEqual("glossary", restored["type"])
        self.assertEqual("Character role", restored["entries"][0]["context"])
        self.assertEqual("remote-1", restored["providerSync"]["remoteGlossaryId"])


if __name__ == "__main__":
    unittest.main()