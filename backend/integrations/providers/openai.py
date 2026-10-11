"""OpenAI: connection validation, chapter analysis and literary translation (Responses API)."""

from __future__ import annotations

import json
from typing import Any, Mapping

from ..base import CredentialField, ConnectionTestResult, ProviderDescriptor, TranslationRequest
from ...usage import report_usage
from ..llm_translation import HttpTransport, LlmTranslationProvider, UrllibHttpTransport, normalized_usage


class OpenAIProvider(LlmTranslationProvider):
    PROVIDER_LABEL = "OpenAI"
    RESPONSES_API_URL = "https://api.openai.com/v1/responses"
    MODELS_API_URL = "https://api.openai.com/v1/models"
    VERIFICATION_MODEL = "gpt-4.1-nano"
    # Default = the model analyze() already uses; projects pick another in translation settings.
    DEFAULT_TRANSLATION_MODEL = VERIFICATION_MODEL
    TRANSLATION_MODEL_ENV = "OPENAI_TRANSLATION_MODEL"
    # /v1/models has no capability flags, so non-chat models are excluded by name.
    _TEXT_MODEL_PREFIXES = ("gpt-", "chatgpt-", "o1", "o3", "o4")
    NON_TEXT_MODEL_MARKERS = (
        "embedding", "whisper", "tts", "dall-e", "image", "audio", "realtime",
        "transcribe", "moderation", "search", "sora", "computer-use", "instruct",
    )

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

    def _headers(self, credentials: Mapping[str, str]) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {credentials['apiKey']}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _translation_http_request(self, credentials: Mapping[str, str], request: TranslationRequest, model: str):
        # OpenAI caches an identical prompt prefix automatically, so the shared system
        # prompt goes first, unchanged between batches, as `instructions`.
        body: dict[str, Any] = {
            "model": model,
            "input": request.text,
            "max_output_tokens": self.TRANSLATION_MAX_TOKENS,
        }
        if request.instructions:
            body["instructions"] = request.instructions
        if request.reasoning and self._reasoning_applies(model):
            body["reasoning"] = {"effort": self._REASONING_EFFORT.get(request.reasoning, request.reasoning)}
        return self.RESPONSES_API_URL, self._headers(credentials), body

    # Responses API `reasoning.effort`. gpt-5.5 takes none/low/medium/high/xhigh; "minimal" is
    # the lowest setting we offer, so it is sent as "none". A model that rejects a value is
    # retried once with "low" (see LlmTranslationProvider.translate).
    _REASONING_EFFORT = {"minimal": "none", "low": "low", "medium": "medium"}
    _REASONING_MODEL_PREFIXES = ("gpt-5", "o1", "o3", "o4")

    def _reasoning_applies(self, model: str) -> bool:
        return model.lower().startswith(self._REASONING_MODEL_PREFIXES)

    def _usage_from_payload(self, payload: Any, model: str):
        if not isinstance(payload, dict):
            return model, None
        raw_usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
        details = raw_usage.get("input_tokens_details") if isinstance(raw_usage.get("input_tokens_details"), dict) else {}
        cached = details.get("cached_tokens") if isinstance(details.get("cached_tokens"), int) else 0
        total_input = raw_usage.get("input_tokens") if isinstance(raw_usage.get("input_tokens"), int) else 0
        usage = normalized_usage(total_input - cached, raw_usage.get("output_tokens"), cached)
        return (payload.get("model") if isinstance(payload.get("model"), str) else model), usage

    def _parse_translation(self, payload: Any, model: str):
        if not isinstance(payload, dict):
            raise ValueError("OpenAI повернув некоректну відповідь.")
        status = payload.get("status")
        if status == "incomplete":
            reason = (payload.get("incomplete_details") or {}).get("reason")
            if reason == "max_output_tokens":
                raise ValueError("OpenAI обірвав переклад, бо вичерпано ліміт max_output_tokens (текст неповний).")
            raise ValueError(f"OpenAI не завершив переклад ({reason or 'incomplete'}), ймовірно через фільтр контенту.")
        if status == "failed":
            message = (payload.get("error") or {}).get("message") if isinstance(payload.get("error"), dict) else None
            raise ValueError(f"OpenAI не зміг виконати переклад.{' ' + message if message else ''}")
        refusal = self._extract_refusal(payload)
        if refusal is not None:
            raise ValueError(f"OpenAI відмовився перекладати цей фрагмент.{' ' + refusal if refusal else ''}")
        raw_usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
        details = raw_usage.get("input_tokens_details") if isinstance(raw_usage.get("input_tokens_details"), dict) else {}
        cached = details.get("cached_tokens") if isinstance(details.get("cached_tokens"), int) else 0
        total_input = raw_usage.get("input_tokens") if isinstance(raw_usage.get("input_tokens"), int) else 0
        usage = normalized_usage(total_input - cached, raw_usage.get("output_tokens"), cached)
        served_model = payload.get("model") if isinstance(payload.get("model"), str) else model
        return self._extract_output_text(payload), usage, served_model

    @staticmethod
    def _extract_refusal(payload: dict[str, Any]) -> str | None:
        """Text of a "refusal" content block, or None when the model did not refuse."""
        for item in payload.get("output") or []:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            for block in item.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "refusal":
                    refusal = block.get("refusal")
                    return refusal.strip() if isinstance(refusal, str) else ""
        return None

    def _fetch_models(self, credentials: Mapping[str, str]) -> list[dict[str, Any]]:
        payload = self._get_json(self.MODELS_API_URL, self._headers(credentials))
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list):
            raise ValueError("OpenAI повернув некоректний список моделей.")
        return [
            {"id": item["id"], "displayName": item["id"]}
            for item in data
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ]

    def _is_text_model(self, model: Mapping[str, Any]) -> bool:
        model_id = model["id"].lower()
        return model_id.startswith(self._TEXT_MODEL_PREFIXES) and not self._has_non_text_marker(model_id)

    @staticmethod
    def _extract_output_text(payload: dict[str, Any]) -> str:
        """Pull the assistant's text out of a raw Responses API JSON body.

        The official OpenAI SDKs expose a convenience top-level "output_text"
        string, but that field is synthesized client-side by the SDK — it is
        not part of the actual HTTP response, which instead nests the text
        inside output[].content[].text. Since this provider talks to the API
        directly over urllib (no SDK), it has to walk that structure itself;
        payload.get("output_text") is always None here.
        """
        fallback = payload.get("output_text")
        if isinstance(fallback, str) and fallback.strip():
            return fallback
        output = payload.get("output")
        if not isinstance(output, list):
            return ""
        parts = []
        for item in output:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            for block in item.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "output_text":
                    text = block.get("text")
                    if isinstance(text, str):
                        parts.append(text)
        return "".join(parts)

    def analyze(self, credentials: Mapping[str, str], prompt: str) -> str:
        body = json.dumps({
            "model": self.VERIFICATION_MODEL,
            "input": prompt,
            "max_output_tokens": 4000,
        }).encode("utf-8")
        try:
            status, response_body = self._transport.post(
                self.RESPONSES_API_URL,
                {
                    "Authorization": f"Bearer {credentials['apiKey']}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                body,
                timeout=60.0,
            )
        except ConnectionError as error:
            raise ValueError("Не вдалося з’єднатися з OpenAI.") from error
        if status in {401, 403}:
            raise ValueError("OpenAI відхилив API key.")
        if status == 429:
            raise ValueError("OpenAI тимчасово обмежив кількість запитів або вичерпано квоту.")
        if status != 200:
            raise ValueError("OpenAI не зміг виконати аналіз.")
        try:
            payload = json.loads(response_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("OpenAI повернув некоректну відповідь.") from error
        billed_model, billed_usage = self._usage_from_payload(payload, self.VERIFICATION_MODEL)
        report_usage(billed_model, billed_usage)
        if isinstance(payload, dict) and payload.get("status") == "incomplete":
            reason = (payload.get("incomplete_details") or {}).get("reason")
            if reason == "max_output_tokens":
                raise ValueError("OpenAI обірвав відповідь, бо вичерпано ліміт max_output_tokens (текст неповний).")
        text = self._extract_output_text(payload) if isinstance(payload, dict) else ""
        if not text.strip():
            raise ValueError("OpenAI повернув порожній результат аналізу.")
        return text.strip()