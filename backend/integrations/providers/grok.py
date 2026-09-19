"""xAI Grok connection validation without translation behavior.

Grok's API is compatible with the OpenAI Chat Completions format
(chat.completions.create), not the newer Responses API that
integrations/providers/openai.py talks to — so the request/response
shapes here intentionally differ from that file despite the similar
provider structure.
"""

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


class GrokProvider(IntegrationProvider):
    BASE_URL = "https://api.x.ai/v1"
    CHAT_COMPLETIONS_URL = f"{BASE_URL}/chat/completions"
    VERIFICATION_MODEL = "grok-4.3"

    def __init__(self, transport: HttpTransport | None = None):
        self._transport = transport or UrllibHttpTransport()

    @property
    def descriptor(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            provider_id="grok",
            display_name="Grok (xAI)",
            description="Перевірка доступу до Grok (xAI) Chat Completions API.",
            credential_fields=(
                CredentialField(
                    name="apiKey",
                    label="API key",
                    placeholder="Введіть Grok (xAI) API key",
                ),
            ),
        )

    def validate_credentials(self, credentials: Mapping[str, Any]) -> dict[str, str]:
        api_key = credentials.get("apiKey")
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("Grok API key is required.")
        return {"apiKey": api_key.strip()}

    def test_connection(self, credentials: Mapping[str, str]) -> ConnectionTestResult:
        request_body = json.dumps({
            "model": self.VERIFICATION_MODEL,
            "messages": [{"role": "user", "content": "Reply with OK."}],
            "max_tokens": 16,
        }).encode("utf-8")
        try:
            status, body = self._transport.post(
                self.CHAT_COMPLETIONS_URL,
                {
                    "Authorization": f"Bearer {credentials['apiKey']}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                request_body,
                timeout=20.0,
            )
        except ConnectionError:
            return ConnectionTestResult("error", "unreachable", "Не вдалося з’єднатися з Grok.")

        if status == 200:
            try:
                payload = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return ConnectionTestResult("error", "invalid_response", "Grok повернув некоректну відповідь.")
            if not isinstance(payload, dict) or not isinstance(payload.get("id"), str):
                return ConnectionTestResult("error", "invalid_response", "Grok повернув некоректну відповідь.")
            return ConnectionTestResult(
                "connected",
                "ok",
                "З’єднання з Grok встановлено.",
                {"model": payload.get("model", self.VERIFICATION_MODEL)},
            )
        if status in {401, 403}:
            return ConnectionTestResult("error", "authentication_failed", "Grok відхилив API key.")
        if status == 429:
            return ConnectionTestResult("error", "rate_limited", "Grok тимчасово обмежив кількість запитів або вичерпано квоту.")
        return ConnectionTestResult("error", "provider_error", "Grok не зміг перевірити з’єднання.")

    def translate(self, credentials: Mapping[str, str], request: TranslationRequest) -> TranslationResult:
        raise ValueError("Grok не підключено до Translation Workspace.")

    def analyze(self, credentials: Mapping[str, str], prompt: str) -> str:
        body = json.dumps({
            "model": self.VERIFICATION_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4000,
        }).encode("utf-8")
        try:
            status, response_body = self._transport.post(
                self.CHAT_COMPLETIONS_URL,
                {
                    "Authorization": f"Bearer {credentials['apiKey']}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                body,
                timeout=60.0,
            )
        except ConnectionError as error:
            raise ValueError("Не вдалося з’єднатися з Grok.") from error
        if status in {401, 403}:
            raise ValueError("Grok відхилив API key.")
        if status == 429:
            raise ValueError("Grok тимчасово обмежив кількість запитів або вичерпано квоту.")
        if status != 200:
            raise ValueError("Grok не зміг виконати аналіз.")
        try:
            payload = json.loads(response_body.decode("utf-8"))
            choice = payload["choices"][0]
            text = choice["message"]["content"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError) as error:
            raise ValueError("Grok повернув некоректну відповідь.") from error
        if isinstance(choice, dict) and choice.get("finish_reason") == "length":
            raise ValueError("Grok обірвав відповідь, бо вичерпано ліміт max_tokens (текст неповний).")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Grok повернув порожній результат аналізу.")
        return text.strip()
