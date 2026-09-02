"""Google Gemini connection validation without analysis or translation behavior."""

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


class GeminiProvider(IntegrationProvider):
    VERIFICATION_MODEL = "gemini-3.1-flash-lite"
    GENERATE_CONTENT_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, transport: HttpTransport | None = None):
        self._transport = transport or UrllibHttpTransport()

    @property
    def descriptor(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            provider_id="gemini",
            display_name="Google Gemini",
            description="Перевірка доступу до Gemini API.",
            credential_fields=(
                CredentialField(
                    name="apiKey",
                    label="API key",
                    placeholder="Введіть Gemini API key",
                ),
            ),
        )

    def validate_credentials(self, credentials: Mapping[str, Any]) -> dict[str, str]:
        api_key = credentials.get("apiKey")
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("Gemini API key is required.")
        return {"apiKey": api_key.strip()}

    def test_connection(self, credentials: Mapping[str, str]) -> ConnectionTestResult:
        request_body = json.dumps({
            "contents": [{"parts": [{"text": "Reply with OK."}]}],
            "generationConfig": {"maxOutputTokens": 16},
        }).encode("utf-8")
        url = self.GENERATE_CONTENT_URL_TEMPLATE.format(model=self.VERIFICATION_MODEL)
        try:
            status, body = self._transport.post(
                url,
                {
                    # Header auth keeps the key out of the URL, unlike the documented "?key=" query param.
                    "x-goog-api-key": credentials["apiKey"],
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                request_body,
                timeout=20.0,
            )
        except ConnectionError:
            return ConnectionTestResult("error", "unreachable", "Не вдалося з’єднатися з Gemini.")

        if status == 200:
            try:
                payload = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return ConnectionTestResult("error", "invalid_response", "Gemini повернув некоректну відповідь.")
            if not isinstance(payload, dict) or not isinstance(payload.get("candidates"), list):
                return ConnectionTestResult("error", "invalid_response", "Gemini повернув некоректну відповідь.")
            return ConnectionTestResult(
                "connected",
                "ok",
                "З’єднання з Gemini встановлено.",
                {"model": self.VERIFICATION_MODEL},
            )
        if status in {400, 401, 403}:
            return ConnectionTestResult("error", "authentication_failed", "Gemini відхилив API key.")
        if status == 429:
            return ConnectionTestResult("error", "rate_limited", "Gemini тимчасово обмежив кількість запитів або вичерпано квоту.")
        return ConnectionTestResult("error", "provider_error", "Gemini не зміг перевірити з’єднання.")

    def translate(self, credentials: Mapping[str, str], request: TranslationRequest) -> TranslationResult:
        raise ValueError("Gemini не підключено до Translation Workspace.")

    def analyze(self, credentials: Mapping[str, str], prompt: str) -> str:
        body = json.dumps({"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": 2000}}).encode("utf-8")
        url = self.GENERATE_CONTENT_URL_TEMPLATE.format(model=self.VERIFICATION_MODEL)
        try:
            status, response_body = self._transport.post(
                url,
                {"x-goog-api-key": credentials["apiKey"], "Accept": "application/json", "Content-Type": "application/json"},
                body,
                timeout=60.0,
            )
        except ConnectionError as error:
            raise ValueError("Не вдалося з’єднатися з Gemini.") from error
        if status in {400, 401, 403}:
            raise ValueError("Gemini відхилив API key.")
        if status == 429:
            raise ValueError("Gemini тимчасово обмежив кількість запитів або вичерпано квоту.")
        if status != 200:
            raise ValueError("Gemini не зміг виконати аналіз.")
        try:
            payload = json.loads(response_body.decode("utf-8"))
            text = payload["candidates"][0]["content"]["parts"][0]["text"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError) as error:
            raise ValueError("Gemini повернув некоректну відповідь.") from error
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Gemini повернув порожній результат аналізу.")
        return text.strip()
