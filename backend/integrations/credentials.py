"""Authenticated encryption for integration credentials."""

from __future__ import annotations

import json
import os
from typing import Any, Mapping

from cryptography.fernet import Fernet, InvalidToken


class CredentialVaultError(RuntimeError):
    """Raised when credentials cannot be safely encrypted or decrypted."""


class CredentialVault:
    def __init__(self, cipher: Fernet | None, unavailable_reason: str | None = None):
        self._cipher = cipher
        self.unavailable_reason = unavailable_reason

    @classmethod
    def from_environment(cls) -> "CredentialVault":
        key = os.environ.get("WORKBENCH_CREDENTIALS_KEY", "").strip()
        if not key:
            return cls(None, "WORKBENCH_CREDENTIALS_KEY is not configured.")
        try:
            return cls(Fernet(key.encode("ascii")))
        except (ValueError, UnicodeEncodeError):
            return cls(None, "WORKBENCH_CREDENTIALS_KEY is invalid.")

    @property
    def available(self) -> bool:
        return self._cipher is not None

    def encrypt(self, credentials: Mapping[str, str]) -> bytes:
        if self._cipher is None:
            raise CredentialVaultError("Credential storage is unavailable.")
        payload = json.dumps(dict(credentials), ensure_ascii=True, separators=(",", ":")).encode("utf-8")
        return self._cipher.encrypt(payload)

    def decrypt(self, ciphertext: bytes) -> dict[str, Any]:
        if self._cipher is None:
            raise CredentialVaultError("Credential storage is unavailable.")
        try:
            payload = self._cipher.decrypt(ciphertext)
            value = json.loads(payload.decode("utf-8"))
        except (InvalidToken, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CredentialVaultError("Stored credentials cannot be decrypted.") from error
        if not isinstance(value, dict):
            raise CredentialVaultError("Stored credentials are invalid.")
        return value
