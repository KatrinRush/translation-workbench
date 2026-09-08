"""Application service for the project-level AI chat."""

from __future__ import annotations

from typing import Any

from .integrations.credentials import CredentialVault, CredentialVaultError
from .integrations.registry import ProviderRegistry


class ChatServiceError(RuntimeError):
    def __init__(self, message: str, http_status: int = 400, code: str = "chat_error"):
        super().__init__(message)
        self.http_status = http_status
        self.code = code


class ChatService:
    def __init__(self, storage, vault: CredentialVault, registry: ProviderRegistry):
        self._storage = storage
        self._vault = vault
        self._registry = registry

    def get_messages(self, project_id: str) -> list[dict[str, Any]]:
        if self._storage.get_project(project_id) is None:
            raise ChatServiceError("Project not found.", 404, "not_found")
        return self._storage.get_chat_messages(project_id)

    def clear_messages(self, project_id: str) -> None:
        if self._storage.get_project(project_id) is None:
            raise ChatServiceError("Project not found.", 404, "not_found")
        self._storage.clear_chat_messages(project_id)

    def send_message(self, project_id: str, message: str, provider_id: str) -> dict[str, Any]:
        if self._storage.get_project(project_id) is None:
            raise ChatServiceError("Project not found.", 404, "not_found")
        if not isinstance(message, str) or not message.strip():
            raise ChatServiceError("Message text is required.", 400, "chat_invalid")
        if not isinstance(provider_id, str) or not provider_id.strip():
            raise ChatServiceError("Choose an AI provider.", 400, "chat_invalid")

        user_message = self._storage.add_chat_message(project_id, "user", message)
        history = self._storage.get_chat_messages(project_id)
        prompt = self._build_prompt(history)

        provider, credentials = self._provider_credentials(provider_id)
        try:
            reply = provider.analyze(credentials, prompt)
        except AttributeError as error:
            raise ChatServiceError("This provider cannot analyze chat messages.", 400, "chat_provider_unsupported") from error

        assistant_message = self._storage.add_chat_message(project_id, "assistant", reply, provider_id)
        return {"userMessage": user_message, "assistantMessage": assistant_message}

    @staticmethod
    def _build_prompt(history: list[dict[str, Any]]) -> str:
        lines = []
        for item in history:
            speaker = "Асистент" if item["role"] == "assistant" else "Користувач"
            lines.append(f"{speaker}: {item['content']}")
        return "\n".join(lines)

    def _provider_credentials(self, provider_id: str):
        provider = self._registry.get(provider_id)
        if provider is None or provider_id == "deepl":
            raise ChatServiceError("This provider cannot analyze chat messages.", 400, "chat_provider_unsupported")

        connections = self._storage.list_integration_connections()
        connection = next((
            item for item in connections
            if item["providerId"] == provider_id and item["enabled"] and item["testStatus"] == "connected"
        ), None)
        if connection is None:
            raise ChatServiceError(
                "Налаштуйте та перевірте підключення для обраного провайдера у Connections.",
                409,
                "connection_required",
            )

        if not self._vault.available:
            raise ChatServiceError("Credential storage is unavailable.", 503, "credential_storage_unavailable")
        record = self._storage.get_integration_connection_record(connection["connectionId"])
        try:
            credentials = self._vault.decrypt(record["credentialsCiphertext"])
        except (CredentialVaultError, TypeError) as error:
            raise ChatServiceError("Stored credentials are unavailable.", 503, "credentials_locked") from error
        return provider, credentials
