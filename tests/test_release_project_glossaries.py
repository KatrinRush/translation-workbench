import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet

from backend import server
from backend.integrations.base import ConnectionTestResult, GlossaryDefinition, IntegrationProvider, ProviderDescriptor, TranslationRequest, TranslationResult
from backend.integrations.credentials import CredentialVault
from backend.integrations.registry import ProviderRegistry
from backend.storage import Storage
from backend.translations.service import TranslationService


class FakeHandler:
    def __init__(self, payload=None):
        self.payload = payload

    def read_json(self):
        return self.payload


class FakeGlossaryProvider(IntegrationProvider):
    def __init__(self):
        self.created = []
        self.deleted = []

    @property
    def descriptor(self):
        return ProviderDescriptor("deepl", "DeepL", "", ())

    def validate_credentials(self, credentials):
        return dict(credentials)

    def test_connection(self, credentials):
        return ConnectionTestResult("connected", "ok", "ok")

    def create_glossary(self, credentials, glossary: GlossaryDefinition):
        glossary_id = f"remote-{len(self.created) + 1}"
        self.created.append((glossary_id, glossary))
        return glossary_id

    def delete_glossary(self, credentials, glossary_id):
        self.deleted.append(glossary_id)

    def translate(self, credentials, request: TranslationRequest):
        return TranslationResult("переклад", "EN")


class ReleaseProjectGlossariesTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")
        self.vault = CredentialVault(Fernet(Fernet.generate_key()))
        self.provider = FakeGlossaryProvider()
        self.service = TranslationService(self.storage, self.vault, ProviderRegistry([self.provider]))
        self.project = self.storage.create_project({"title": "Glossary book", "status": "translation"})
        self.connection = self.storage.create_integration_connection(
            "deepl", "DeepL", self.vault.encrypt({"apiKey": "test-key"})
        )
        self.storage.update_integration_connection_status(
            self.connection["connectionId"], "connected", "ok", "ok", {}
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _delete_project(self):
        with patch.object(server, "storage", self.storage), \
                patch.object(server, "translation_service", self.service):
            return server.WorkbenchHandler.handle_api(
                FakeHandler(), "DELETE", f"/api/projects/{self.project['projectId']}"
            )

    def _create_synced_glossary(self):
        item = self.storage.create_glossary_entry(
            {"source": "river", "target": "ріка", "note": "", "active": True}
        )
        return self.service.commit_project_glossary_draft(
            self.project["projectId"],
            {
                "sourceLanguage": "EN",
                "targetLanguage": "UK",
                "glossaryEntryIds": [item["glossaryEntryId"]],
            },
        )

    def test_project_delete_releases_remote_glossary(self):
        saved = self._create_synced_glossary()
        remote_glossary_id = saved["providerSync"]["remoteGlossaryId"]

        status, _ = self._delete_project()

        self.assertEqual(204, status)
        self.assertEqual([remote_glossary_id], self.provider.deleted)
        self.assertIsNone(self.storage.get_project(self.project["projectId"]))
        remaining = self.storage.list_project_translation_glossaries(self.project["projectId"])
        self.assertEqual([], remaining)

    def test_project_delete_succeeds_when_remote_delete_fails(self):
        saved = self._create_synced_glossary()
        glossary_rule_id = saved["glossaryRuleId"]
        connection_id = self.connection["connectionId"]

        def failing_delete(credentials, glossary_id):
            raise ValueError("DeepL unavailable")

        self.provider.delete_glossary = failing_delete

        status, _ = self._delete_project()

        self.assertEqual(204, status)
        self.assertIsNone(self.storage.get_project(self.project["projectId"]))

    def test_provider_is_not_called_for_glossary_without_sync(self):
        self.storage.upsert_project_translation_glossary(self.project["projectId"], {
            "sourceLanguage": "EN",
            "targetLanguage": "UK",
            "entries": [{"source": "river", "target": "ріка", "context": ""}],
            "contentHash": "content-hash",
        })

        with patch.object(self.provider, "delete_glossary") as delete_mock:
            status, _ = self._delete_project()

        self.assertEqual(204, status)
        delete_mock.assert_not_called()
        self.assertIsNone(self.storage.get_project(self.project["projectId"]))


if __name__ == "__main__":
    unittest.main()
