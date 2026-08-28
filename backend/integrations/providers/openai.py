"""OpenAI connection validation without analysis or translation behavior."""

from __future__ import annotations

import json
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..base import CredentialField, ConnectionTestResult, IntegrationProvider, ProviderDescriptor, TranslationRequest, TranslationResult


class HttpTransport(Protocol):
    def post(self, url: str, headers: Mapping[str, str], body: bytes, timeout: float) -> tuple[int, bytes]: ...


class UrllibHttpTransport:
    def post(self, url: str, headers: Mapping[str, str], body: bytes, timeout: float) -> tuple[int, bytes]:
        request = Request(url, headers=dict(headers), data=body, method="POST")
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.status, response.read()
        except HTTPError as error:
            return error.code, b""
        except (URLError, TimeoutError, OSError) as error:
            raise ConnectionError("The provider could not be reached.") from error


class OpenAIProvider(IntegrationProvider):
    RESPONSES_API_URL = "https://api.openai.com/v1/responses"
    VERIFICATION_MODEL = "gpt-4.1-nano"

    def __init__(self, transport: HttpTransport | None = None):
        self._transport = transport or UrllibHttpTransport()

    @property
    def descriptor(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            provider_id="openai",
            display_name="OpenAI / GPT",
            description="Перевірка доступу до OpenAI Responses API.",
            credential_fields=(
                CredentialField(
                    name="apiKey",
                    label="API key",
                    placeholder="Введіть OpenAI API key",
                ),
            ),
        )

    def validate_credentials(self, credentials: Mapping[str, Any]) -> dict[str, str]:
        api_key = credentials.get("apiKey")
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("OpenAI API key is required.")
        return {"apiKey": api_key.strip()}

    def test_connection(self, credentials: Mapping[str, str]) -> ConnectionTestResult:
        request_body = json.dumps({
            "model": self.VERIFICATION_MODEL,
            "input": "Reply with OK.",
            "max_output_tokens": 16,
        }).encode("utf-8")
        try:
            status, body = self._transport.post(
                self.RESPONSES_API_URL,
                {
                    "Authorization": f"Bearer {credentials['apiKey']}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                request_body,
                timeout=20.0,
            )
        except ConnectionError:
            return ConnectionTestResult("error", "unreachable", "Не вдалося з’єднатися з OpenAI.")

        if status == 200:
            try:
                payload = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return ConnectionTestResult("error", "invalid_response", "OpenAI повернув некоректну відповідь.")
            if not isinstance(payload, dict) or not isinstance(payload.get("id"), str):
                return ConnectionTestResult("error", "invalid_response", "OpenAI повернув некоректну відповідь.")
            return ConnectionTestResult(
                "connected",
                "ok",
                "З’єднання з OpenAI встановлено.",
                {"model": payload.get("model", self.VERIFICATION_MODEL)},
            )
        if status in {401, 403}:
            return ConnectionTestResult("error", "authentication_failed", "OpenAI відхилив API key.")
        if status == 429:
            return ConnectionTestResult("error", "rate_limited", "OpenAI тимчасово обмежив кількість запитів або вичерпано квоту.")
        return ConnectionTestResult("error", "provider_error", "OpenAI не зміг перевірити з’єднання.")

    def translate(self, credentials: Mapping[str, str], request: TranslationRequest) -> TranslationResult:
        raise ValueError("OpenAI не підключено до Translation Workspace.")