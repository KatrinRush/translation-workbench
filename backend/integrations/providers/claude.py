"""Anthropic Claude: connection validation, chapter analysis and literary translation."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..base import CredentialField, ConnectionTestResult, IntegrationProvider, ProviderDescriptor, TranslationRequest, TranslationResult


def _decode_error_message(body: bytes) -> str | None:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
        return None
    error = payload.get("error") if isinstance(payload, dict) else None
    message = error.get("message") if isinstance(error, dict) else None
    return message if isinstance(message, str) and message.strip() else None


def _extract_chunk(text: str) -> str:
    """Cut the <chunk>…</chunk> element out of the reply, dropping a markdown fence or
    stray prose around it. Anything without a complete chunk element is returned as is,
    so the caller's strict XML/ID check rejects it instead of us guessing."""
    start = text.find("<chunk")
    end = text.rfind("</chunk>")
    if start == -1 or end == -1 or end < start:
        return text.strip()
    return text[start:end + len("</chunk>")]


class HttpTransport(Protocol):
    def post(self, url: str, headers: Mapping[str, str], body: bytes, timeout: float) -> tuple[int, bytes]: ...


class UrllibHttpTransport:
    def post(self, url: str, headers: Mapping[str, str], body: bytes, timeout: float) -> tuple[int, bytes]:
        request = Request(url, headers=dict(headers), data=body, method="POST")
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.status, response.read()
        except HTTPError as error:
            # The error body carries Anthropic's {"error": {"message": ...}}; read it once
            # here or nobody downstream can say why the request was rejected.
            try:
                return error.code, error.read()
            except OSError:
                return error.code, b""
        except (URLError, TimeoutError, OSError) as error:
            raise ConnectionError("The provider could not be reached.") from error


class ClaudeProvider(IntegrationProvider):
    MESSAGES_API_URL = "https://api.anthropic.com/v1/messages"
    ANTHROPIC_VERSION = "2023-06-01"
    VERIFICATION_MODEL = "claude-haiku-4-5-20251001"
    DEFAULT_TRANSLATION_MODEL = "claude-sonnet-5-5"
    TRANSLATION_MODEL_ENV = "CLAUDE_TRANSLATION_MODEL"
    # One batch is one browser request behind Cloudflare, which answers 524 after ~100 s;
    # give up first so the user sees a real error instead of a proxy timeout page.
    TRANSLATION_TIMEOUT_SECONDS = 90.0
    TRANSLATION_MAX_TOKENS = 16000
    # Effort is only accepted by the 5.x generation; "medium" keeps adaptive thinking
    # short enough for a batch to finish well inside the timeout above.
    TRANSLATION_EFFORT = "medium"
    _EFFORT_MODEL_PREFIXES = ("claude-opus-5", "claude-sonnet-5", "claude-haiku-5", "claude-fable-5")
    # Models that accept server-side refusal fallbacks ("default" routing by refusal category).
    _FALLBACK_MODELS = {"claude-sonnet-5-5", "claude-opus-5-5", "claude-opus-5", "claude-fable-5-1"}
    FALLBACK_BETA = "server-side-fallback-2026-07-01"

    def __init__(self, transport: HttpTransport | None = None):
        self._transport = transport or UrllibHttpTransport()

    @property
    def descriptor(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            provider_id="claude",
            display_name="Anthropic Claude",
            description="Перевірка доступу до Claude Messages API.",
            credential_fields=(
                CredentialField(
                    name="apiKey",
                    label="API key",
                    placeholder="Введіть Claude API key",
                ),
            ),
        )

    def validate_credentials(self, credentials: Mapping[str, Any]) -> dict[str, str]:
        api_key = credentials.get("apiKey")
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("Claude API key is required.")
        return {"apiKey": api_key.strip()}

    def test_connection(self, credentials: Mapping[str, str]) -> ConnectionTestResult:
        request_body = json.dumps({
            "model": self.VERIFICATION_MODEL,
            "max_tokens": 16,
            "messages": [{"role": "user", "content": "Reply with OK."}],
        }).encode("utf-8")
        try:
            status, body = self._transport.post(
                self.MESSAGES_API_URL,
                {
                    "x-api-key": credentials["apiKey"],
                    "anthropic-version": self.ANTHROPIC_VERSION,
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                request_body,
                timeout=20.0,
            )
        except ConnectionError:
            return ConnectionTestResult("error", "unreachable", "Не вдалося з’єднатися з Claude.")

        if status == 200:
            try:
                payload = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return ConnectionTestResult("error", "invalid_response", "Claude повернув некоректну відповідь.")
            if not isinstance(payload, dict) or not isinstance(payload.get("id"), str):
                return ConnectionTestResult("error", "invalid_response", "Claude повернув некоректну відповідь.")
            return ConnectionTestResult(
                "connected",
                "ok",
                "З’єднання з Claude встановлено.",
                {"model": payload.get("model", self.VERIFICATION_MODEL)},
            )
        if status in {401, 403}:
            return ConnectionTestResult("error", "authentication_failed", "Claude відхилив API key.")
        if status == 429:
            return ConnectionTestResult("error", "rate_limited", "Claude тимчасово обмежив кількість запитів або вичерпано квоту.")
        return ConnectionTestResult("error", "provider_error", "Claude не зміг перевірити з’єднання.")

    @classmethod
    def translation_model(cls, requested: str | None = None) -> str:
        """Project setting first, then the server-wide env override, then the default."""
        for candidate in (requested, os.environ.get(cls.TRANSLATION_MODEL_ENV)):
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        return cls.DEFAULT_TRANSLATION_MODEL

    def translate(self, credentials: Mapping[str, str], request: TranslationRequest) -> TranslationResult:
        """`request.text` is the whole user message (context + XML chunk); `request.instructions`
        is the system prompt, identical for every batch of a chapter and therefore cached."""
        model = self.translation_model(request.model)
        body_fields: dict[str, Any] = {
            "model": model,
            "max_tokens": self.TRANSLATION_MAX_TOKENS,
            "messages": [{"role": "user", "content": request.text}],
        }
        if request.instructions:
            body_fields["system"] = [{
                "type": "text",
                "text": request.instructions,
                "cache_control": {"type": "ephemeral"},
            }]
        if model.startswith(self._EFFORT_MODEL_PREFIXES):
            body_fields["output_config"] = {"effort": self.TRANSLATION_EFFORT}
        headers = {
            "x-api-key": credentials["apiKey"],
            "anthropic-version": self.ANTHROPIC_VERSION,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if model in self._FALLBACK_MODELS:
            body_fields["fallbacks"] = "default"
            headers["anthropic-beta"] = self.FALLBACK_BETA
        try:
            status, response_body = self._transport.post(
                self.MESSAGES_API_URL,
                headers,
                json.dumps(body_fields, ensure_ascii=False).encode("utf-8"),
                timeout=self.TRANSLATION_TIMEOUT_SECONDS,
            )
        except ConnectionError as error:
            logging.error("Claude translate request could not reach the API: %s", error)
            raise ValueError("Не вдалося з’єднатися з Claude (або запит перевищив час очікування).") from error

        if status != 200:
            logging.error("Claude translate request failed: status=%s body=%r", status, response_body[:1000])
            message = _decode_error_message(response_body)
            detail = f" {message}" if message else ""
            if status in {401, 403}:
                raise ValueError(f"Claude відхилив API key.{detail}")
            if status == 429:
                raise ValueError(f"Claude тимчасово обмежив кількість запитів або вичерпано квоту.{detail}")
            if status == 529:
                raise ValueError(f"Claude перевантажений, спробуйте пізніше.{detail}")
            raise ValueError(f"Claude не зміг виконати переклад (HTTP {status}).{detail}")

        try:
            payload = json.loads(response_body.decode("utf-8"))
            blocks = payload["content"]
            stop_reason = payload.get("stop_reason")
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, AttributeError) as error:
            raise ValueError("Claude повернув некоректну відповідь.") from error
        if stop_reason == "refusal":
            details = payload.get("stop_details") or {}
            category = details.get("category") if isinstance(details, dict) else None
            suffix = f" (категорія: {category})" if category else ""
            raise ValueError(f"Claude відмовився перекладати цей фрагмент{suffix}.")
        if stop_reason == "max_tokens":
            raise ValueError("Claude обірвав переклад, бо вичерпано ліміт max_tokens (текст неповний).")
        if not isinstance(blocks, list):
            raise ValueError("Claude повернув некоректну відповідь.")
        text = "".join(
            block.get("text", "") for block in blocks
            if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str)
        )
        if not text.strip():
            raise ValueError("Claude повернув порожній переклад.")
        raw_usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
        usage = {
            key: raw_usage.get(key) or 0
            for key in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
        }
        served_model = payload.get("model") if isinstance(payload.get("model"), str) else model
        return TranslationResult(text=_extract_chunk(text), model=served_model, usage=usage)

    def analyze(self, credentials: Mapping[str, str], prompt: str) -> str:
        body = json.dumps({
            "model": self.VERIFICATION_MODEL,
            "max_tokens": 4000,  # margin above the draft-analysis + JSON budget so batches don't get truncated mid-response
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")
        try:
            status, response_body = self._transport.post(
                self.MESSAGES_API_URL,
                {
                    "x-api-key": credentials["apiKey"],
                    "anthropic-version": self.ANTHROPIC_VERSION,
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                body,
                timeout=60.0,
            )
        except ConnectionError as error:
            raise ValueError("Не вдалося з’єднатися з Claude.") from error
        if status in {401, 403}:
            raise ValueError("Claude відхилив API key.")
        if status == 429:
            raise ValueError("Claude тимчасово обмежив кількість запитів або вичерпано квоту.")
        if status != 200:
            raise ValueError("Claude не зміг виконати аналіз.")
        try:
            payload = json.loads(response_body.decode("utf-8"))
            text = payload["content"][0]["text"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError) as error:
            raise ValueError("Claude повернув некоректну відповідь.") from error
        if isinstance(payload, dict) and payload.get("stop_reason") == "max_tokens":
            raise ValueError("Claude обірвав відповідь, бо вичерпано ліміт max_tokens (текст неповний).")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Claude повернув порожній результат аналізу.")
        return text.strip()
