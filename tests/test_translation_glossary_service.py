import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet

from backend.integrations.base import ConnectionTestResult, GlossaryDefinition, GlossaryLimitError, IntegrationProvider, ProviderDescriptor, TranslationRequest, TranslationResult
from backend.integrations.credentials import CredentialVault
from backend.integrations.registry import ProviderRegistry
from backend.storage import Storage
from backend.translations.service import TranslationService, TranslationServiceError


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


class WrongParagraphIdProvider(FakeGlossaryProvider):
    def translate(self, credentials, request: TranslationRequest):
        return TranslationResult('<chunk><p id="wrong-paragraph-id">Переклад</p></chunk>', "EN")


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

    def test_translate_chapter_rejects_provider_response_with_wrong_paragraph_id(self):
        service = TranslationService(self.storage, self.vault, ProviderRegistry([WrongParagraphIdProvider()]))
        chapter = self.storage.get_book_structure(self.project["projectId"])["chapters"][0]

        with self.assertRaises(TranslationServiceError) as error:
            service.translate_chapter(self.project["projectId"], chapter["chapterId"], {})

        self.assertEqual("chunk_mapping_failed", error.exception.code)

    def test_translate_paragraph_provider_context_skips_service_paragraph(self):
        self.storage.save_book_structure(
            self.project["projectId"],
            "book.epub",
            "application/epub+zip",
            b"book-with-service-text",
            {
                "chapters": [{
                    "title": "Chapter",
                    "elements": [
                        {"type": "paragraph", "text": "Before one. Before two."},
                        {"type": "paragraph", "text": "Chapter sixteen"},
                        {"type": "paragraph", "text": "Target paragraph."},
                        {"type": "paragraph", "text": "After one. After two."},
                    ],
                }]
            },
        )
        structure = self.storage.get_book_structure(self.project["projectId"])
        elements = structure["chapters"][0]["elements"]
        service_paragraph = elements[1]
        target_paragraph = elements[2]
        self.storage.update_paragraph(service_paragraph["paragraphId"], None, False, True)

        self.service.translate_paragraph(target_paragraph["paragraphId"], {})

        request = self.provider.translation_requests[-1]
        self.assertEqual("Target paragraph.", request.text)
        self.assertNotIn("Chapter sixteen", request.context or "")
        self.assertIn("Before one.", request.context or "")
        self.assertIn("After one.", request.context or "")

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

    def test_second_project_replaces_active_glossary_for_same_language_pair(self):
        first_item = self.storage.create_glossary_entry(
            {"source": "river", "target": "ріка", "note": "", "active": True}
        )
        first = self.service.commit_project_glossary_draft(
            self.project["projectId"],
            {"sourceLanguage": "EN", "targetLanguage": "UK", "glossaryEntryIds": [first_item["glossaryEntryId"]]},
        )
        second_project = self.storage.create_project({"title": "Second book", "status": "translation"})
        second_item = self.storage.create_glossary_entry(
            {"source": "forest", "target": "ліс", "note": "", "active": True}
        )

        second = self.service.commit_project_glossary_draft(
            second_project["projectId"],
            {"sourceLanguage": "EN", "targetLanguage": "UK", "glossaryEntryIds": [second_item["glossaryEntryId"]]},
        )

        self.assertEqual(["remote-1"], self.provider.deleted)
        self.assertEqual("remote-2", second["providerSync"]["remoteGlossaryId"])
        self.assertEqual(second["glossaryRuleId"], second["providerSync"]["glossaryRuleId"])
        replaced = self.storage.get_project_translation_glossary(first["glossaryRuleId"])
        self.assertEqual("unsynced", replaced["syncState"])
        self.assertEqual(second["glossaryRuleId"], replaced["providerSync"]["glossaryRuleId"])
        self.assertEqual(second_project["projectId"], replaced["providerSync"]["projectId"])
        active = self.storage.get_provider_glossary_sync(self.connection["connectionId"], "EN", "UK")
        self.assertEqual(second_project["projectId"], active["projectId"])

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

    def test_sync_state_failure_is_logged_and_reported_as_failed(self):
        item = self.storage.create_glossary_entry(
            {"source": "river", "target": "ріка", "note": "", "active": True}
        )

        with patch.object(
            self.storage,
            "save_provider_glossary_sync",
            side_effect=sqlite3.OperationalError("database is locked"),
        ):
            with self.assertLogs(level="ERROR") as logs:
                saved = self.service.commit_project_glossary_draft(
                    self.project["projectId"],
                    {"sourceLanguage": "EN", "targetLanguage": "UK", "glossaryEntryIds": [item["glossaryEntryId"]]},
                )

        self.assertEqual("failed", saved["providerSyncResult"]["status"])
        self.assertEqual("glossary_sync_state_failed", saved["providerSyncResult"]["code"])
        self.assertTrue(any("database is locked" in message for message in logs.output))


if __name__ == "__main__":
    unittest.main()
