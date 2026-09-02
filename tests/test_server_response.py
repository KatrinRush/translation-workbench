from io import BytesIO
from pathlib import Path
import json
import tempfile
import unittest

from cryptography.fernet import Fernet

from backend.integrations.base import ConnectionTestResult, GlossaryDefinition, IntegrationProvider, ProviderDescriptor
from backend.integrations.credentials import CredentialVault
from backend.integrations.registry import ProviderRegistry
from backend.server import WorkbenchHandler
from backend.storage import Storage
from backend.translations.service import TranslationService


class FakeHandler:
    def __init__(self):
        self.status = None
        self.headers = {}
        self.wfile = BytesIO()

    def send_response(self, status):
        self.status = status

    def send_header(self, name, value):
        self.headers[name] = value

    def end_headers(self):
        pass


class FailingGlossaryProvider(IntegrationProvider):
    """Mirrors a provider whose glossary sync always fails, without any network access."""

    @property
    def descriptor(self):
        return ProviderDescriptor("deepl", "DeepL", "", ())

    def validate_credentials(self, credentials):
        return dict(credentials)

    def test_connection(self, credentials):
        return ConnectionTestResult("connected", "ok", "ok")

    def create_glossary(self, credentials, glossary: GlossaryDefinition):
        raise ValueError("DeepL не зміг створити глосарій.")

    def delete_glossary(self, credentials, glossary_id):
        pass

    def translate(self, credentials, request):
        raise AssertionError("translate() should not be called by this test.")


class WorkbenchHandlerResponseTests(unittest.TestCase):
    def test_204_response_has_no_body(self):
        handler = FakeHandler()

        WorkbenchHandler.send_json(handler, 204, None)

        self.assertEqual(handler.status, 204)
        self.assertEqual(handler.headers.get("Content-Length"), "0")
        self.assertNotIn("Content-Type", handler.headers)
        self.assertEqual(handler.wfile.getvalue(), b"")

    def _assert_valid_complete_json_response(self, handler):
        body = handler.wfile.getvalue()
        self.assertEqual(str(len(body)), handler.headers.get("Content-Length"))
        # Must not raise "Unexpected end of JSON input" on the frontend.
        return json.loads(body.decode("utf-8"))

    def test_commit_glossary_draft_response_is_complete_json_when_provider_sync_fails(self):
        """Regression for the 'Зберегти глосарій' bug: response body must always be full, valid JSON."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            storage = Storage(Path(temporary_directory) / "workbench.sqlite3")
            vault = CredentialVault(Fernet(Fernet.generate_key()))
            service = TranslationService(storage, vault, ProviderRegistry([FailingGlossaryProvider()]))
            project = storage.create_project({"title": "Glossary book", "status": "translation"})
            storage.create_integration_connection("deepl", "DeepL", vault.encrypt({"apiKey": "test-key"}))
            item = storage.create_glossary_entry(
                {"source": "river", "target": "ріка", "note": "", "active": True}
            )

            payload = service.commit_project_glossary_draft(
                project["projectId"],
                {"sourceLanguage": "EN", "targetLanguage": "UK", "glossaryEntryIds": [item["glossaryEntryId"]]},
            )

            handler = FakeHandler()
            WorkbenchHandler.send_json(handler, 200, payload)

            parsed = self._assert_valid_complete_json_response(handler)
            self.assertEqual("failed", parsed["providerSyncResult"]["status"])


if __name__ == "__main__":
    unittest.main()