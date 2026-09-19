import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from cryptography.fernet import Fernet

from backend.integrations.base import (
    ConnectionTestResult,
    IntegrationProvider,
    ProviderDescriptor,
    QuotaExceededError,
    TranslationRequest,
    TranslationResult,
)
from backend.integrations.credentials import CredentialVault
from backend.integrations.registry import ProviderRegistry
from backend.storage import Storage
from backend.translations.service import TranslationService, TranslationServiceError


class QuotaAwareProvider(IntegrationProvider):
    """Fake DeepL provider where specific connections are configured to be over quota."""

    def __init__(self, exhausted_api_keys):
        self.exhausted_api_keys = set(exhausted_api_keys)

    @property
    def descriptor(self):
        return ProviderDescriptor("deepl", "DeepL", "", ())

    def validate_credentials(self, credentials):
        return dict(credentials)

    def test_connection(self, credentials):
        return ConnectionTestResult("connected", "ok", "ok")

    def create_glossary(self, credentials, glossary):
        raise NotImplementedError

    def delete_glossary(self, credentials, glossary_id):
        raise NotImplementedError

    def translate(self, credentials, request: TranslationRequest):
        if credentials["apiKey"] in self.exhausted_api_keys:
            raise QuotaExceededError("DeepL вичерпав ліміт символів для цього підключення.")
        root = ET.fromstring(request.text)
        for element in root.findall(".//p"):
            element.text = "Переклад"
        return TranslationResult(ET.tostring(root, encoding="unicode"), "EN")


class DeepLQuotaSwitchTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")
        self.vault = CredentialVault(Fernet(Fernet.generate_key()))
        self.provider = QuotaAwareProvider(exhausted_api_keys={"exhausted-key"})
        self.service = TranslationService(self.storage, self.vault, ProviderRegistry([self.provider]))

        self.project = self.storage.create_project({"title": "Quota book", "status": "translation"})
        self.storage.save_book_structure(
            self.project["projectId"],
            "book.epub",
            "application/epub+zip",
            b"book",
            {"chapters": [{"title": "One", "elements": [{"type": "paragraph", "text": "Hello"}]}]},
        )
        self.paragraph_id = self.storage.get_book_structure(self.project["projectId"])["chapters"][0]["elements"][0]["paragraphId"]

        self.exhausted_connection = self.storage.create_integration_connection(
            "deepl", "DeepL primary", self.vault.encrypt({"apiKey": "exhausted-key"})
        )
        self.storage.update_integration_connection_status(
            self.exhausted_connection["connectionId"], "connected", "ok", "ok", {}
        )
        self.backup_connection = self.storage.create_integration_connection(
            "deepl", "DeepL backup", self.vault.encrypt({"apiKey": "fresh-key"})
        )
        self.storage.update_integration_connection_status(
            self.backup_connection["connectionId"], "connected", "ok", "ok", {}
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_translate_paragraph_reports_quota_exceeded_with_connection_details(self):
        with self.assertRaises(TranslationServiceError) as context:
            self.service.translate_paragraph(
                self.paragraph_id, {"connectionId": self.exhausted_connection["connectionId"]}
            )

        error = context.exception
        self.assertEqual("quota_exceeded", error.code)
        self.assertEqual(self.exhausted_connection["connectionId"], error.details["connectionId"])
        self.assertEqual("deepl", error.details["providerId"])

    def test_switching_to_a_different_connection_succeeds(self):
        with self.assertRaises(TranslationServiceError):
            self.service.translate_paragraph(
                self.paragraph_id, {"connectionId": self.exhausted_connection["connectionId"]}
            )

        result = self.service.translate_paragraph(
            self.paragraph_id, {"connectionId": self.backup_connection["connectionId"]}
        )

        self.assertEqual("Переклад", result["translationText"])
        self.assertEqual(self.backup_connection["connectionId"], result["connectionId"])

    def test_translate_chapter_reports_quota_exceeded_with_connection_details(self):
        with self.assertRaises(TranslationServiceError) as context:
            self.service.translate_chapter(
                self.project["projectId"],
                self.storage.get_book_structure(self.project["projectId"])["chapters"][0]["chapterId"],
                {"connectionId": self.exhausted_connection["connectionId"]},
            )

        error = context.exception
        self.assertEqual("quota_exceeded", error.code)
        self.assertEqual(self.exhausted_connection["connectionId"], error.details["connectionId"])


if __name__ == "__main__":
    unittest.main()
