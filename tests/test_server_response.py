from io import BytesIO
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

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
    def test_paragraph_update_api_passes_is_service_to_storage(self):
        handler = object.__new__(WorkbenchHandler)
        handler.read_json = lambda: {
            "translationText": "Переклад",
            "reviewed": True,
            "isService": True,
        }
        updated = {
            "paragraphId": "paragraph-1",
            "translationText": "Переклад",
            "reviewed": True,
            "isService": True,
        }

        with patch("backend.server.storage.update_paragraph", return_value=updated) as update_paragraph:
            status, payload = WorkbenchHandler.handle_api(handler, "PUT", "/api/paragraphs/paragraph-1")

        self.assertEqual(200, status)
        self.assertEqual(updated, payload)
        update_paragraph.assert_called_once_with("paragraph-1", "Переклад", True, True)

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


class ServerLogsEndpointTests(unittest.TestCase):
    def _handler_with_path(self, path, headers=None):
        handler = FakeHandler()
        handler.path = path
        handler.headers = headers or {}
        return handler

    def test_disabled_when_no_token_configured(self):
        handler = self._handler_with_path("/api/logs")
        with patch("backend.server.LOG_VIEWER_TOKEN", ""):
            status, payload = WorkbenchHandler.handle_api(handler, "GET", "/api/logs")

        self.assertEqual(403, status)
        self.assertIn("error", payload)

    def test_rejects_missing_or_wrong_token(self):
        handler = self._handler_with_path("/api/logs", {"X-Workbench-Log-Token": "wrong"})
        with patch("backend.server.LOG_VIEWER_TOKEN", "secret-token"):
            status, payload = WorkbenchHandler.handle_api(handler, "GET", "/api/logs")

        self.assertEqual(403, status)
        self.assertIn("error", payload)

    def test_returns_recent_lines_with_valid_token(self):
        handler = self._handler_with_path("/api/logs?limit=2", {"X-Workbench-Log-Token": "secret-token"})
        with patch("backend.server.LOG_VIEWER_TOKEN", "secret-token"), \
                patch("backend.server.read_recent_lines", return_value=["a", "b"]) as read_recent_lines:
            status, payload = WorkbenchHandler.handle_api(handler, "GET", "/api/logs")

        self.assertEqual(200, status)
        self.assertEqual({"lines": ["a", "b"]}, payload)
        read_recent_lines.assert_called_once_with(2)


if __name__ == "__main__":
    unittest.main()