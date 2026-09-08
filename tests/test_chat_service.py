import tempfile
import unittest
from pathlib import Path

from cryptography.fernet import Fernet

from backend.chat_service import ChatService, ChatServiceError
from backend.integrations.base import ConnectionTestResult, ProviderDescriptor
from backend.integrations.credentials import CredentialVault
from backend.integrations.registry import ProviderRegistry
from backend.storage import Storage


class FakeAnalyzingProvider:
    def __init__(self, provider_id="claude", reply="Відповідь асистента."):
        self.descriptor = ProviderDescriptor(
            provider_id=provider_id,
            display_name=provider_id,
            description="",
            credential_fields=(),
        )
        self.reply = reply
        self.calls = []

    def test_connection(self, credentials):
        return ConnectionTestResult(status="connected", code=None, message=None, metadata={})

    def analyze(self, credentials, prompt):
        self.calls.append(prompt)
        return self.reply


class ChatServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")
        self.vault = CredentialVault(Fernet(Fernet.generate_key()))
        self.provider = FakeAnalyzingProvider()
        self.registry = ProviderRegistry([self.provider])
        self.service = ChatService(self.storage, self.vault, self.registry)
        self.project = self.storage.create_project({
            "title": "Chat Project",
            "authorId": None,
            "seriesId": None,
            "status": "analysis",
            "analysisResult": None,
            "projectRuleIds": [],
            "projectGlossaryEntryIds": [],
            "inheritedRules": [],
            "inheritedGlossary": [],
        })
        self.project_id = self.project["projectId"]

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _connect_provider(self, provider_id="claude"):
        connection = self.storage.create_integration_connection(
            provider_id, "Test connection", self.vault.encrypt({"apiKey": "secret"})
        )
        self.storage.update_integration_connection_status(
            connection["connectionId"], "connected", None, None, {}
        )
        return connection

    def test_add_and_get_chat_messages_are_ordered_by_created_at(self):
        self.storage.add_chat_message(self.project_id, "user", "Привіт")
        self.storage.add_chat_message(self.project_id, "assistant", "Вітаю", "claude")

        messages = self.storage.get_chat_messages(self.project_id)

        self.assertEqual(2, len(messages))
        self.assertEqual("user", messages[0]["role"])
        self.assertEqual("Привіт", messages[0]["content"])
        self.assertIsNone(messages[0]["providerId"])
        self.assertEqual("assistant", messages[1]["role"])
        self.assertEqual("claude", messages[1]["providerId"])

    def test_clear_chat_messages_removes_project_history(self):
        self.storage.add_chat_message(self.project_id, "user", "Привіт")

        self.storage.clear_chat_messages(self.project_id)

        self.assertEqual([], self.storage.get_chat_messages(self.project_id))

    def test_send_message_without_connection_raises_clear_error(self):
        with self.assertRaises(ChatServiceError) as context:
            self.service.send_message(self.project_id, "Привіт", "claude")

        self.assertEqual(409, context.exception.http_status)
        self.assertEqual("connection_required", context.exception.code)

    def test_send_message_with_deepl_provider_raises_clear_error(self):
        with self.assertRaises(ChatServiceError) as context:
            self.service.send_message(self.project_id, "Привіт", "deepl")

        self.assertEqual(400, context.exception.http_status)
        self.assertEqual("chat_provider_unsupported", context.exception.code)

    def test_send_message_persists_user_and_assistant_messages(self):
        self._connect_provider("claude")

        result = self.service.send_message(self.project_id, "Привіт", "claude")

        self.assertEqual("user", result["userMessage"]["role"])
        self.assertEqual("Привіт", result["userMessage"]["content"])
        self.assertEqual("assistant", result["assistantMessage"]["role"])
        self.assertEqual("Відповідь асистента.", result["assistantMessage"]["content"])
        self.assertEqual("claude", result["assistantMessage"]["providerId"])
        self.assertEqual(2, len(self.storage.get_chat_messages(self.project_id)))

    def test_send_message_builds_prompt_from_history(self):
        self._connect_provider("claude")
        self.storage.add_chat_message(self.project_id, "user", "Перше питання")
        self.storage.add_chat_message(self.project_id, "assistant", "Перша відповідь", "claude")

        self.service.send_message(self.project_id, "Друге питання", "claude")

        prompt = self.provider.calls[-1]
        self.assertEqual(
            "Користувач: Перше питання\nАсистент: Перша відповідь\nКористувач: Друге питання",
            prompt,
        )

    def test_get_messages_for_unknown_project_raises_not_found(self):
        with self.assertRaises(ChatServiceError) as context:
            self.service.get_messages("missing-project")

        self.assertEqual(404, context.exception.http_status)


if __name__ == "__main__":
    unittest.main()
