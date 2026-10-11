"""Application service for provider-agnostic connections."""

from __future__ import annotations

import time
from typing import Any, Callable

from .credentials import CredentialVault, CredentialVaultError
from .registry import ProviderRegistry


class IntegrationServiceError(RuntimeError):
    def __init__(self, message: str, http_status: int = 400, code: str = "integration_error"):
        super().__init__(message)
        self.http_status = http_status
        self.code = code


class IntegrationService:
    # Model catalogues change rarely; a short cache spares the provider a request every
    # time the translation settings dialog opens or the search box changes.
    MODEL_LIST_TTL_SECONDS = 600

    def __init__(self, storage, vault: CredentialVault, registry: ProviderRegistry, clock: Callable[[], float] = time.monotonic):
        self._storage = storage
        self._vault = vault
        self._registry = registry
        self._clock = clock
        self._model_cache: dict[str, tuple[float, list[dict[str, str]]]] = {}

    def list_providers(self) -> dict[str, Any]:
        return {
            "credentialStorage": {
                "available": self._vault.available,
                "reason": None if self._vault.available else self._vault.unavailable_reason,
            },
            "providers": [
                {
                    **provider.descriptor.to_dict(),
                    # Lets the UI name the model a translation will use without hardcoding IDs.
                    "defaultTranslationModel": provider.translation_model() if hasattr(provider, "translation_model") else None,
                }
                for provider in self._registry.list()
            ],
        }

    def list_connections(self) -> list[dict[str, Any]]:
        return [self._decorate_connection(item) for item in self._storage.list_integration_connections()]

    def get_connection(self, connection_id: str) -> dict[str, Any]:
        connection = self._storage.get_integration_connection(connection_id)
        if not connection:
            raise IntegrationServiceError("Connection not found.", 404, "not_found")
        return self._decorate_connection(connection)

    def create_connection(self, data: dict[str, Any]) -> dict[str, Any]:
        self._require_vault()
        provider = self._provider(str(data.get("providerId", "")))
        credentials = self._credentials(provider, data.get("credentials"))
        display_name = str(data.get("displayName") or provider.descriptor.display_name).strip()
        if not display_name:
            raise IntegrationServiceError("Connection name is required.")
        ciphertext = self._vault.encrypt(credentials)
        return self._decorate_connection(
            self._storage.create_integration_connection(provider.descriptor.provider_id, display_name, ciphertext)
        )

    def update_connection(self, connection_id: str, data: dict[str, Any]) -> dict[str, Any]:
        existing = self._storage.get_integration_connection(connection_id)
        if not existing:
            raise IntegrationServiceError("Connection not found.", 404, "not_found")
        provider = self._provider(existing["providerId"])
        display_name = str(data.get("displayName", existing["displayName"])).strip()
        if not display_name:
            raise IntegrationServiceError("Connection name is required.")
        ciphertext = None
        if "credentials" in data:
            self._require_vault()
            ciphertext = self._vault.encrypt(self._credentials(provider, data["credentials"]))
        updated = self._storage.update_integration_connection(
            connection_id,
            display_name,
            bool(data.get("enabled", existing["enabled"])),
            ciphertext,
        )
        self._model_cache.pop(connection_id, None)
        return self._decorate_connection(updated)

    def delete_connection(self, connection_id: str) -> None:
        self._model_cache.pop(connection_id, None)
        if not self._storage.delete_integration_connection(connection_id):
            raise IntegrationServiceError("Connection not found.", 404, "not_found")

    def list_models(self, connection_id: str, query: str | None = None, refresh: bool = False) -> dict[str, Any]:
        """Text-generation models available through a stored connection. The credentials are
        decrypted here and never leave the server; the browser only sees model IDs."""
        record = self._storage.get_integration_connection_record(connection_id)
        if not record:
            raise IntegrationServiceError("Підключення не знайдено. Налаштуйте його в Connections.", 404, "not_found")
        provider = self._provider(record["providerId"])
        if not hasattr(provider, "list_models"):
            raise IntegrationServiceError("Цей провайдер не має переліку моделей.", 400, "models_unsupported")
        cached = self._model_cache.get(connection_id)
        now = self._clock()
        from_cache = bool(cached and cached[0] > now and not refresh)
        if from_cache:
            models = cached[1]
        else:
            self._require_vault()
            try:
                credentials = self._vault.decrypt(record["credentialsCiphertext"])
            except CredentialVaultError as error:
                raise IntegrationServiceError("Stored credentials are unavailable.", 503, "credentials_locked") from error
            try:
                models = provider.list_models(credentials)
            except ValueError as error:
                raise IntegrationServiceError(
                    f"Не вдалося отримати список моделей: {error}", 502, "models_unavailable"
                ) from error
            self._model_cache[connection_id] = (now + self.MODEL_LIST_TTL_SECONDS, models)
        needle = (query or "").strip().casefold()
        if needle:
            models = [item for item in models if needle in item["id"].casefold() or needle in item["displayName"].casefold()]
        return {
            "connectionId": connection_id,
            "providerId": record["providerId"],
            "cached": from_cache,
            "models": models,
        }

    def test_connection(self, connection_id: str) -> dict[str, Any]:
        self._require_vault()
        record = self._storage.get_integration_connection_record(connection_id)
        if not record:
            raise IntegrationServiceError("Connection not found.", 404, "not_found")
        provider = self._provider(record["providerId"])
        try:
            credentials = self._vault.decrypt(record["credentialsCiphertext"])
        except CredentialVaultError as error:
            raise IntegrationServiceError(
                "Stored credentials are unavailable.", 503, "credentials_locked"
            ) from error
        result = provider.test_connection(credentials)
        updated = self._storage.update_integration_connection_status(
            connection_id,
            result.status,
            result.code,
            result.message,
            result.metadata,
        )
        return self._decorate_connection(updated)

    def get_status(self, connection_id: str) -> dict[str, Any]:
        connection = self.get_connection(connection_id)
        return {
            "connectionId": connection["connectionId"],
            "status": connection["status"],
            "statusCode": connection["statusCode"],
            "statusMessage": connection["statusMessage"],
            "providerMetadata": connection["providerMetadata"],
            "lastTestedAt": connection["lastTestedAt"],
        }

    def _decorate_connection(self, connection: dict[str, Any]) -> dict[str, Any]:
        result = dict(connection)
        test_status = result.pop("testStatus")
        result["status"] = "locked" if not self._vault.available else test_status
        result.pop("credentialsCiphertext", None)
        return result

    def _provider(self, provider_id: str):
        provider = self._registry.get(provider_id)
        if provider is None:
            raise IntegrationServiceError("Unsupported integration provider.", 400, "unsupported_provider")
        return provider

    @staticmethod
    def _credentials(provider, value: Any) -> dict[str, str]:
        if not isinstance(value, dict):
            raise IntegrationServiceError("Credentials are required.")
        try:
            return provider.validate_credentials(value)
        except ValueError as error:
            raise IntegrationServiceError(str(error)) from error

    def _require_vault(self) -> None:
        if not self._vault.available:
            raise IntegrationServiceError(
                "Credential storage is unavailable.", 503, "credential_storage_unavailable"
            )