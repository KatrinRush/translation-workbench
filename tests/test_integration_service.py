import tempfile
import unittest
from pathlib import Path

from cryptography.fernet import Fernet

from backend.integrations.credentials import CredentialVault
from backend.integrations.providers.deepl import DeepLProvider
from backend.integrations.providers.openai import OpenAIProvider
from backend.integrations.registry import ProviderRegistry
from backend.integrations.service import IntegrationService, IntegrationServiceError
from backend.storage import Storage
from tests.test_deepl_provider import FakeTransport
from tests.test_openai_provider import FakeTransport as FakeOpenAITransport


class IntegrationServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")
        self.transport = FakeTransport(payload={"character_count": 7, "character_limit": 100})
        self.vault = CredentialVault(Fernet(Fernet.generate_key()))
        self.service = IntegrationService(
            self.storage,
            self.vault,
            ProviderRegistry([DeepLProvider(self.transport)]),
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_create_and_test_connection_without_exposing_credentials(self):
        connection = self.service.create_connection(
            {"providerId": "deepl", "displayName": "DeepL", "credentials": {"apiKey": "private-key"}}
        )

        self.assertNotIn("credentials", connection)
        self.assertNotIn("credentialsCiphertext", connection)
        tested = self.service.test_connection(connection["connectionId"])
        self.assertEqual("connected", tested["status"])
        self.assertNotIn("private-key", str(tested))

    def test_openai_connection_uses_shared_storage_without_exposing_credentials(self):
        service = IntegrationService(
            self.storage,
            self.vault,
            ProviderRegistry([OpenAIProvider(FakeOpenAITransport())]),
        )

        connection = service.create_connection(
            {"providerId": "openai", "displayName": "OpenAI / GPT", "credentials": {"apiKey": "private-key"}}
        )
        tested = service.test_connection(connection["connectionId"])

        self.assertEqual("connected", tested["status"])
        self.assertEqual("openai", tested["providerId"])
        self.assertNotIn("private-key", str(service.list_connections()))

    def test_missing_vault_keeps_providers_visible_but_blocks_create(self):
        service = IntegrationService(
            self.storage,
            CredentialVault(None, "not configured"),
            ProviderRegistry([DeepLProvider(self.transport)]),
        )

        self.assertFalse(service.list_providers()["credentialStorage"]["available"])
        with self.assertRaises(IntegrationServiceError) as context:
            service.create_connection(
                {"providerId": "deepl", "credentials": {"apiKey": "private-key"}}
            )
        self.assertEqual(503, context.exception.http_status)

    def test_existing_connection_is_locked_without_key_and_can_be_deleted(self):
        connection = self.service.create_connection(
            {"providerId": "deepl", "credentials": {"apiKey": "private-key"}}
        )
        unavailable_service = IntegrationService(
            self.storage,
            CredentialVault(None, "not configured"),
            ProviderRegistry([DeepLProvider(self.transport)]),
        )

        self.assertEqual("locked", unavailable_service.get_connection(connection["connectionId"])["status"])
        unavailable_service.delete_connection(connection["connectionId"])
        self.assertEqual([], unavailable_service.list_connections())


if __name__ == "__main__":
    unittest.main()