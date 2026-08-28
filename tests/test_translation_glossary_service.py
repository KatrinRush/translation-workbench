import tempfile
import unittest
from pathlib import Path

from cryptography.fernet import Fernet

from backend.integrations.base import ConnectionTestResult, GlossaryDefinition, GlossaryLimitError, IntegrationProvider, ProviderDescriptor, TranslationRequest, TranslationResult
from backend.integrations.credentials import CredentialVault
from backend.integrations.registry import ProviderRegistry
from backend.storage import Storage
from backend.translations.service import TranslationService


class FakeGlossaryProvider(IntegrationProvider):
    def __init__(self):
        self.created = []
        self.deleted = []
        self.translation_requests = []
        self.limit_reached_once = False

    @property
    def descriptor(self):
        return ProviderDescriptor("deepl", "DeepL", "", ())

    def validate_credentials(self, credentials):
        return dict(credentials)

    def test_connection(self, credentials):
        return ConnectionTestResult("connected", "ok", "ok")

    def create_glossary(self, credentials, glossary: GlossaryDefinition):
        if self.limit_reached_once:
            self.limit_reached_once = False
            raise GlossaryLimitError("Too many glossaries")
        glossary_id = f"remote-{len(self.created) + 1}"
        self.created.append((glossary_id, glossary))
        return glossary_id

    def delete_glossary(self, credentials, glossary_id):
        self.deleted.append(glossary_id)

    def translate(self, credentials, request: TranslationRequest):
        self.translation_requests.append(request)
        text = "домінант" if request.glossary_id else "панівний"
        return TranslationResult(text, "EN")


class FailingGlossaryProvider(FakeGlossaryProvider):
    def create_glossary(self, credentials, glossary: GlossaryDefinition):
        raise ValueError("DeepL не зміг створити глосарій.")


class TranslationGlossaryServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")
        self.vault = CredentialVault(Fernet(Fernet.generate_key()))
        self.provider = FakeGlossaryProvider()
        self.service = TranslationService(self.storage, self.vault, ProviderRegistry([self.provider]))
        self.project = self.storage.create_project({"title": "Glossary book", "status": "translation"})
        self.storage.save_book_structure(
            self.project["projectId"],
            "book.epub",
            "application/epub+zip",
            b"book",
            {"chapters": [{"title": "One", "elements": [{"type": "paragraph", "text": "dominant"}]}]},
        )
        self.paragraph_id = self.storage.get_book_structure(self.project["projectId"])["chapters"][0]["elements"][0]["paragraphId"]
        self.connection = self.storage.create_integration_connection(
            "deepl", "DeepL", self.vault.encrypt({"apiKey": "test-key"})
        )
        self.storage.update_integration_connection_status(
            self.connection["connectionId"], "connected", "ok", "ok", {}
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_glossary_is_reused_replaced_and_affects_translation(self):
        payload = {
            "sourceLanguage": "EN",
            "targetLanguage": "UK",
            "entries": [{"source": "dominant", "target": "домінант", "context": "role"}],
        }
        saved = self.service.save_project_glossary(self.project["projectId"], payload)
        payload["glossaryRuleId"] = saved["glossaryRuleId"]

        self.service.save_project_glossary(self.project["projectId"], payload)
        self.assertEqual(1, len(self.provider.created))

        payload["entries"][0]["context"] = "changed local note"
        self.service.save_project_glossary(self.project["projectId"], payload)
        self.assertEqual(1, len(self.provider.created))

        payload["entries"][0]["target"] = "домінантний"
        updated = self.service.save_project_glossary(self.project["projectId"], payload)
        self.assertEqual(2, len(self.provider.created))
        self.assertEqual(["remote-1"], self.provider.deleted)
        self.assertEqual("remote-2", updated["providerSync"]["remoteGlossaryId"])

        translated = self.service.translate_paragraph(self.paragraph_id, {})
        self.assertEqual("домінант", translated["translationText"])
        self.assertEqual("remote-2", self.provider.translation_requests[0].glossary_id)
        self.assertEqual("EN", self.provider.translation_requests[0].source_language)

    def test_commit_draft_syncs_to_provider_and_translation_uses_current_glossary_id(self):
        item = self.storage.create_glossary_entry(
            {"source": "poppy girl", "target": "макове дівчисько", "note": "", "active": True}
        )

        saved = self.service.commit_project_glossary_draft(
            self.project["projectId"],
            {
                "sourceLanguage": "EN",
                "targetLanguage": "UK",
                "glossaryEntryIds": [item["glossaryEntryId"]],
            },
        )

        self.assertEqual("synced", saved["providerSyncResult"]["status"])
        self.assertEqual("remote-1", saved["providerSync"]["remoteGlossaryId"])
        self.assertEqual(saved["contentHash"], saved["providerSync"]["contentHash"])

        found = self.storage.find_synced_project_glossary(
            self.project["projectId"], self.connection["connectionId"], "UK"
        )
        self.assertIsNotNone(found)
        self.assertEqual("remote-1", found["providerSync"]["remoteGlossaryId"])

        translated = self.service.translate_paragraph(self.paragraph_id, {})
        self.assertEqual("домінант", translated["translationText"])
        self.assertEqual("remote-1", self.provider.translation_requests[0].glossary_id)

    def test_glossary_limit_reached_replaces_old_remote_glossary(self):
        item = self.storage.create_glossary_entry(
            {"source": "Dadzbog", "target": "Дажбог", "note": "", "active": True}
        )
        first = self.service.commit_project_glossary_draft(
            self.project["projectId"],
            {"sourceLanguage": "EN", "targetLanguage": "UK", "glossaryEntryIds": [item["glossaryEntryId"]]},
        )
        self.assertEqual("remote-1", first["providerSync"]["remoteGlossaryId"])

        second_item = self.storage.create_glossary_entry(
            {"source": "Jaga", "target": "Яга", "note": "", "active": True}
        )
        self.provider.limit_reached_once = True
        second = self.service.commit_project_glossary_draft(
            self.project["projectId"],
            {
                "glossaryRuleId": first["glossaryRuleId"],
                "sourceLanguage": "EN",
                "targetLanguage": "UK",
                "glossaryEntryIds": [item["glossaryEntryId"], second_item["glossaryEntryId"]],
            },
        )

        self.assertEqual("synced", second["providerSyncResult"]["status"])
        self.assertEqual(["remote-1"], self.provider.deleted)
        self.assertEqual("remote-2", second["providerSync"]["remoteGlossaryId"])

    def test_failed_sync_keeps_local_glossary_but_does_not_mark_it_synced(self):
        failing_provider = FailingGlossaryProvider()
        service = TranslationService(self.storage, self.vault, ProviderRegistry([failing_provider]))
        item = self.storage.create_glossary_entry(
            {"source": "river", "target": "ріка", "note": "", "active": True}
        )

        saved = service.commit_project_glossary_draft(
            self.project["projectId"],
            {"sourceLanguage": "EN", "targetLanguage": "UK", "glossaryEntryIds": [item["glossaryEntryId"]]},
        )

        self.assertEqual("failed", saved["providerSyncResult"]["status"])
        self.assertIsNotNone(saved["currentVersionId"])
        self.assertIsNone(saved["providerSync"])

        found = self.storage.find_synced_project_glossary(
            self.project["projectId"], self.connection["connectionId"], "UK"
        )
        self.assertIsNone(found)


if __name__ == "__main__":
    unittest.main()
