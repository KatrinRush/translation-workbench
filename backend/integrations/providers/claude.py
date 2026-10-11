"""Anthropic Claude: connection validation, chapter analysis and literary translation."""

from __future__ import annotations

import json
from typing import Any, Mapping
from urllib.parse import urlencode

from ..base import CredentialField, ConnectionTestResult, ProviderDescriptor, TranslationRequest
from ...usage import report_usage
from ..llm_translation import HttpTransport, LlmTranslationProvider, UrllibHttpTransport, normalized_usage


class ClaudeProvider(LlmTranslationProvider):
    PROVIDER_LABEL = "Claude"
    MESSAGES_API_URL = "https://api.anthropic.com/v1/messages"
    MODELS_API_URL = "https://api.anthropic.com/v1/models"
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
    OVERLOADED_STATUSES = frozenset({529})

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

    def _translation_http_request(self, credentials: Mapping[str, str], request: TranslationRequest, model: str):
        """`request.text` is the whole user message (context + XML chunk); `request.instructions`
        is the system prompt, identical for every batch of a chapter and therefore cached."""
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
        headers = self._headers(credentials)
        if model in self._FALLBACK_MODELS:
            body_fields["fallbacks"] = "default"
            headers["anthropic-beta"] = self.FALLBACK_BETA
        return self.MESSAGES_API_URL, headers, body_fields

    def _headers(self, credentials: Mapping[str, str]) -> dict[str, str]:
        return {
            "x-api-key": credentials["apiKey"],
            "anthropic-version": self.ANTHROPIC_VERSION,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _usage_from_payload(self, payload: Any, model: str):
        raw_usage = payload.get("usage") if isinstance(payload, dict) and isinstance(payload.get("usage"), dict) else {}
        usage = normalized_usage(
            raw_usage.get("input_tokens"),
            raw_usage.get("output_tokens"),
            raw_usage.get("cache_read_input_tokens"),
            raw_usage.get("cache_creation_input_tokens"),
        )
        served = payload.get("model") if isinstance(payload, dict) and isinstance(payload.get("model"), str) else model
        return served, usage

    def _parse_translation(self, payload: Any, model: str):
        try:
            blocks = payload["content"]
            stop_reason = payload.get("stop_reason")
        except (KeyError, TypeError, AttributeError) as error:
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
        raw_usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
        usage = normalized_usage(
            raw_usage.get("input_tokens"),
            raw_usage.get("output_tokens"),
            raw_usage.get("cache_read_input_tokens"),
            raw_usage.get("cache_creation_input_tokens"),
        )
        served_model = payload.get("model") if isinstance(payload.get("model"), str) else model
        return text, usage, served_model

    def _fetch_models(self, credentials: Mapping[str, str]) -> list[dict[str, Any]]:
        """GET /v1/models, paginated with after_id/has_more."""
        models: list[dict[str, Any]] = []
        after_id = None
        for _page in range(20):
            query = {"limit": 1000, **({"after_id": after_id} if after_id else {})}
            payload = self._get_json(f"{self.MODELS_API_URL}?{urlencode(query)}", self._headers(credentials))
            data = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(data, list):
                raise ValueError("Claude повернув некоректний список моделей.")
            models.extend(
                {"id": item["id"], "displayName": item.get("display_name") or item["id"]}
                for item in data
                if isinstance(item, dict) and isinstance(item.get("id"), str)
            )
            if not payload.get("has_more") or not payload.get("last_id"):
                break
            after_id = payload["last_id"]
        return models

    def _is_text_model(self, model: Mapping[str, Any]) -> bool:
        # Every model the Messages API lists generates text.
        return True

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
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("Claude повернув некоректну відповідь.") from error
        billed_model, billed_usage = self._usage_from_payload(payload, self.VERIFICATION_MODEL)
        report_usage(billed_model, billed_usage)  # billed even if the reply is then rejected
        try:
            text = payload["content"][0]["text"]
        except (KeyError, IndexError, TypeError) as error:
            raise ValueError("Claude повернув некоректну відповідь.") from error
        if isinstance(payload, dict) and payload.get("stop_reason") == "max_tokens":
            raise ValueError("Claude обірвав відповідь, бо вичерпано ліміт max_tokens (текст неповний).")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Claude повернув порожній результат аналізу.")
        return text.strip()
