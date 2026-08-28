"""Registry for integration provider adapters."""

from __future__ import annotations

from .base import IntegrationProvider


class ProviderRegistry:
    def __init__(self, providers: list[IntegrationProvider] | None = None):
        self._providers: dict[str, IntegrationProvider] = {}
        for provider in providers or []:
            self.register(provider)

    def register(self, provider: IntegrationProvider) -> None:
        provider_id = provider.descriptor.provider_id
        if provider_id in self._providers:
            raise ValueError(f"Provider '{provider_id}' is already registered.")
        self._providers[provider_id] = provider

    def get(self, provider_id: str) -> IntegrationProvider | None:
        return self._providers.get(provider_id)

    def list(self) -> list[IntegrationProvider]:
        return list(self._providers.values())
