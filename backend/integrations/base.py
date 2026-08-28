"""Contracts shared by all external integration providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class CredentialField:
    name: str
    label: str
    secret: bool = True
    required: bool = True
    placeholder: str = ""


@dataclass(frozen=True)
class ProviderDescriptor:
    provider_id: str
    display_name: str
    description: str
    credential_fields: tuple[CredentialField, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "providerId": self.provider_id,
            "displayName": self.display_name,
            "description": self.description,
            "credentialFields": [asdict(item) for item in self.credential_fields],
        }


@dataclass(frozen=True)
class ConnectionTestResult:
    status: str
    code: str
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TranslationRequest:
    text: str
    target_language: str
    source_language: str | None = None
    tag_handling: str | None = None
    context: str | None = None
    glossary_id: str | None = None


@dataclass(frozen=True)
class GlossaryDefinition:
    name: str
    source_language: str
    target_language: str
    entries: tuple[tuple[str, str], ...]


class GlossaryLimitError(ValueError):
    """Provider refused to create a glossary because the account limit is reached."""


@dataclass(frozen=True)
class TranslationResult:
    text: str
    detected_source_language: str | None = None


class IntegrationProvider(ABC):
    @property
    @abstractmethod
    def descriptor(self) -> ProviderDescriptor:
        raise NotImplementedError

    @abstractmethod
    def validate_credentials(self, credentials: Mapping[str, Any]) -> dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    def test_connection(self, credentials: Mapping[str, str]) -> ConnectionTestResult:
        raise NotImplementedError

    @abstractmethod
    def translate(self, credentials: Mapping[str, str], request: TranslationRequest) -> TranslationResult:
        raise NotImplementedError

    def create_glossary(self, credentials: Mapping[str, str], glossary: GlossaryDefinition) -> str:
        raise ValueError("Provider does not support glossaries.")

    def delete_glossary(self, credentials: Mapping[str, str], glossary_id: str) -> None:
        raise ValueError("Provider does not support glossaries.")
