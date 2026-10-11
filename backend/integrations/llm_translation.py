"""Shared plumbing for LLM translation providers (Claude, OpenAI, Gemini).

Each provider only describes its own wire format — how to build the HTTP request
for one translation batch, how to read text/usage out of the reply, and how to
list its models. Model selection, transport, HTTP error mapping, chunk extraction
and empty-reply handling live here so the three providers cannot drift apart.
"""

from __future__ import annotations

from abc import abstractmethod
import json
import logging
import os
import re
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .base import IntegrationProvider, TranslationRequest, TranslationResult


class HttpTransport(Protocol):
    def post(self, url: str, headers: Mapping[str, str], body: bytes, timeout: float) -> tuple[int, bytes]: ...

    def get(self, url: str, headers: Mapping[str, str], timeout: float) -> tuple[int, bytes]: ...


class UrllibHttpTransport:
    """urllib transport that keeps the error body: every provider explains a rejected
    request in it ({"error": {"message": ...}}), and HTTPError hands it out only once."""

    def post(self, url: str, headers: Mapping[str, str], body: bytes, timeout: float) -> tuple[int, bytes]:
        return self._send(Request(url, headers=dict(headers), data=body, method="POST"), timeout)

    def get(self, url: str, headers: Mapping[str, str], timeout: float) -> tuple[int, bytes]:
        return self._send(Request(url, headers=dict(headers), method="GET"), timeout)

    @staticmethod
    def _send(request: Request, timeout: float) -> tuple[int, bytes]:
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.status, response.read()
        except HTTPError as error:
            try:
                return error.code, error.read()
            except OSError:
                return error.code, b""
        except (URLError, TimeoutError, OSError) as error:
            raise ConnectionError("The provider could not be reached.") from error


def decode_error_message(body: bytes) -> str | None:
    """{"error": {"message": ...}} — the shape Anthropic, OpenAI and Gemini all use."""
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, AttributeError):
        return None
    error = payload.get("error") if isinstance(payload, dict) else None
    message = error.get("message") if isinstance(error, dict) else None
    return message if isinstance(message, str) and message.strip() else None


def extract_chunk(text: str) -> str:
    """Cut the <chunk>…</chunk> element out of the reply, dropping a markdown fence or
    stray prose around it. Anything without a complete chunk element is returned as is,
    so the caller's strict XML/ID check rejects it instead of us guessing."""
    start = text.find("<chunk")
    end = text.rfind("</chunk>")
    if start == -1 or end == -1 or end < start:
        return text.strip()
    return text[start:end + len("</chunk>")]


def normalized_usage(input_tokens: Any = 0, output_tokens: Any = 0, cache_read: Any = 0, cache_write: Any = 0) -> dict[str, int]:
    """One usage shape for every provider (Anthropic's names). input_tokens never
    includes cache reads, so cost = input + output + cache read/write priced apart."""
    def number(value: Any) -> int:
        return value if isinstance(value, int) and value > 0 else 0

    return {
        "input_tokens": number(input_tokens),
        "output_tokens": number(output_tokens),
        "cache_creation_input_tokens": number(cache_write),
        "cache_read_input_tokens": number(cache_read),
    }


class LlmTranslationProvider(IntegrationProvider):
    PROVIDER_LABEL = "LLM"
    DEFAULT_TRANSLATION_MODEL = ""
    TRANSLATION_MODEL_ENV = ""
    # One batch is one browser request behind Cloudflare, which answers 524 after ~100 s;
    # give up first so the user sees a real error instead of a proxy timeout page.
    TRANSLATION_TIMEOUT_SECONDS = 90.0
    TRANSLATION_MAX_TOKENS = 16000
    OVERLOADED_STATUSES = frozenset({503})
    MODEL_LIST_TIMEOUT_SECONDS = 20.0
    _transport: HttpTransport

    @classmethod
    def translation_model(cls, requested: str | None = None) -> str:
        """Project setting first, then the server-wide env override, then the default."""
        for candidate in (requested, os.environ.get(cls.TRANSLATION_MODEL_ENV) if cls.TRANSLATION_MODEL_ENV else None):
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        return cls.DEFAULT_TRANSLATION_MODEL

    @abstractmethod
    def _translation_http_request(
        self, credentials: Mapping[str, str], request: TranslationRequest, model: str
    ) -> tuple[str, dict[str, str], dict[str, Any]]:
        """(url, headers, JSON body) for one batch; `request.instructions` is the system
        prompt shared by every batch, `request.text` the batch's user message."""

    @abstractmethod
    def _parse_translation(self, payload: Any, model: str) -> tuple[str, dict[str, int], str]:
        """(text, usage, served model); raises ValueError for refusals, safety blocks and
        truncated replies so the batch fails without saving."""

    def translate(self, credentials: Mapping[str, str], request: TranslationRequest) -> TranslationResult:
        label = self.PROVIDER_LABEL
        model = self.translation_model(request.model)
        url, headers, body = self._translation_http_request(credentials, request, model)
        try:
            status, response_body = self._transport.post(
                url,
                headers,
                json.dumps(body, ensure_ascii=False).encode("utf-8"),
                timeout=self.TRANSLATION_TIMEOUT_SECONDS,
            )
        except ConnectionError as error:
            logging.error("%s translate request could not reach the API: %s", label, error)
            raise ValueError(f"Не вдалося з’єднатися з {label} (або запит перевищив час очікування).") from error

        if status != 200:
            logging.error("%s translate request failed: status=%s body=%r", label, status, response_body[:1000])
            raise self._http_error(status, decode_error_message(response_body), "виконати переклад")

        try:
            payload = json.loads(response_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f"{label} повернув некоректну відповідь.") from error
        text, usage, served_model = self._parse_translation(payload, model)
        if not text.strip():
            raise ValueError(f"{label} повернув порожній переклад.")
        return TranslationResult(text=extract_chunk(text), model=served_model, usage=usage)

    def _http_error(self, status: int, message: str | None, action: str) -> ValueError:
        label = self.PROVIDER_LABEL
        detail = f" {message}" if message else ""
        if status in {401, 403}:
            return ValueError(f"{label} відхилив API key.{detail}")
        if status == 429:
            return ValueError(f"{label} тимчасово обмежив кількість запитів або вичерпано квоту.{detail}")
        if status in self.OVERLOADED_STATUSES:
            return ValueError(f"{label} перевантажений, спробуйте пізніше.{detail}")
        return ValueError(f"{label} не зміг {action} (HTTP {status}).{detail}")

    # --- model catalogue -----------------------------------------------------------

    # Substrings of model IDs that never do plain text generation (embeddings, speech,
    # images, video, realtime audio, moderation). Matched case-insensitively.
    NON_TEXT_MODEL_MARKERS: tuple[str, ...] = ()

    @abstractmethod
    def _fetch_models(self, credentials: Mapping[str, str]) -> list[dict[str, Any]]:
        """Raw catalogue as [{"id", "displayName", ...provider fields}] across all pages."""

    @abstractmethod
    def _is_text_model(self, model: Mapping[str, Any]) -> bool:
        """Whether the model can be used for text generation through this provider's API."""

    def list_models(self, credentials: Mapping[str, str]) -> list[dict[str, str]]:
        """Text-generation models visible to these credentials, sorted by ID."""
        models = [model for model in self._fetch_models(credentials) if self._is_text_model(model)]
        unique = {model["id"]: {"id": model["id"], "displayName": model.get("displayName") or model["id"]} for model in models}
        return sorted(unique.values(), key=lambda item: item["id"])

    def _has_non_text_marker(self, model_id: str) -> bool:
        lowered = model_id.lower()
        return any(re.search(rf"(^|[-_./]){re.escape(marker)}", lowered) for marker in self.NON_TEXT_MODEL_MARKERS)

    def _get_json(self, url: str, headers: Mapping[str, str]) -> Any:
        try:
            status, body = self._transport.get(url, headers, timeout=self.MODEL_LIST_TIMEOUT_SECONDS)
        except ConnectionError as error:
            raise ValueError(f"Не вдалося з’єднатися з {self.PROVIDER_LABEL}, щоб отримати список моделей.") from error
        if status != 200:
            logging.error("%s model list request failed: status=%s body=%r", self.PROVIDER_LABEL, status, body[:1000])
            raise self._http_error(status, decode_error_message(body), "повернути список моделей")
        try:
            return json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f"{self.PROVIDER_LABEL} повернув некоректний список моделей.") from error


__all__ = [
    "HttpTransport",
    "LlmTranslationProvider",
    "UrllibHttpTransport",
    "decode_error_message",
    "extract_chunk",
    "normalized_usage",
]
