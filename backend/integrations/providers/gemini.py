"""Google Gemini: connection validation, chapter analysis and literary translation."""

from __future__ import annotations

import json
from typing import Any, Mapping
from urllib.parse import quote, urlencode

from ..base import CredentialField, ConnectionTestResult, ProviderDescriptor, TranslationRequest
from ..llm_translation import HttpTransport, LlmTranslationProvider, UrllibHttpTransport, normalized_usage


class GeminiProvider(LlmTranslationProvider):
    PROVIDER_LABEL = "Gemini"
    VERIFICATION_MODEL = "gemini-3.1-flash-lite"
    GENERATE_CONTENT_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    MODELS_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    # Default = the model analyze() already uses; projects pick another in translation settings.
    DEFAULT_TRANSLATION_MODEL = VERIFICATION_MODEL
    TRANSLATION_MODEL_ENV = "GEMINI_TRANSLATION_MODEL"
    # Models that list generateContent but produce images, speech or live audio.
    NON_TEXT_MODEL_MARKERS = ("embedding", "aqa", "imagen", "veo", "tts", "image", "audio", "live", "robotics")

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

    @staticmethod
    def _headers(credentials: Mapping[str, str]) -> dict[str, str]:
        # Header auth keeps the key out of the URL, unlike the documented "?key=" query param.
        return {"x-goog-api-key": credentials["apiKey"], "Accept": "application/json", "Content-Type": "application/json"}

    @staticmethod
    def _model_path(model: str) -> str:
        """Model IDs from models.list come as "models/<id>"; the URL template adds that prefix itself."""
        return quote(model.removeprefix("models/"), safe="-._")

    def _translation_http_request(self, credentials: Mapping[str, str], request: TranslationRequest, model: str):
        # Gemini caches a repeated prompt prefix implicitly; the system instruction is
        # identical for every batch of a project, the batch text follows it.
        body: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": request.text}]}],
            "generationConfig": {"maxOutputTokens": self.TRANSLATION_MAX_TOKENS},
        }
        if request.instructions:
            body["systemInstruction"] = {"parts": [{"text": request.instructions}]}
        url = self.GENERATE_CONTENT_URL_TEMPLATE.format(model=self._model_path(model))
        return url, self._headers(credentials), body

    def _parse_translation(self, payload: Any, model: str):
        if not isinstance(payload, dict):
            raise ValueError("Gemini повернув некоректну відповідь.")
        block_reason = (payload.get("promptFeedback") or {}).get("blockReason") if isinstance(payload.get("promptFeedback"), dict) else None
        if block_reason:
            raise ValueError(f"Gemini заблокував запит через фільтр контенту ({block_reason}).")
        candidates = payload.get("candidates")
        if not isinstance(candidates, list) or not candidates or not isinstance(candidates[0], dict):
            raise ValueError("Gemini не повернув жодної відповіді — ймовірно, заблоковано фільтром контенту.")
        candidate = candidates[0]
        finish_reason = candidate.get("finishReason")
        if finish_reason == "MAX_TOKENS":
            raise ValueError("Gemini обірвав переклад, бо вичерпано ліміт maxOutputTokens (текст неповний).")
        if finish_reason not in (None, "STOP"):
            raise ValueError(f"Gemini заблокував або обірвав переклад ({finish_reason}), ймовірно через фільтр контенту.")
        parts = (candidate.get("content") or {}).get("parts") if isinstance(candidate.get("content"), dict) else None
        # Thought summaries (part.thought == true) are reasoning, not the translation.
        text = "".join(
            part["text"] for part in parts or []
            if isinstance(part, dict) and isinstance(part.get("text"), str) and not part.get("thought")
        )
        meta = payload.get("usageMetadata") if isinstance(payload.get("usageMetadata"), dict) else {}

        def count(key: str) -> int:
            value = meta.get(key)
            return value if isinstance(value, int) else 0

        cached = count("cachedContentTokenCount")
        # Thinking tokens are billed as output.
        usage = normalized_usage(count("promptTokenCount") - cached, count("candidatesTokenCount") + count("thoughtsTokenCount"), cached)
        served_model = payload.get("modelVersion") if isinstance(payload.get("modelVersion"), str) else model
        return text, usage, served_model

    def _fetch_models(self, credentials: Mapping[str, str]) -> list[dict[str, Any]]:
        """models.list, paginated with pageToken/nextPageToken."""
        models: list[dict[str, Any]] = []
        page_token = None
        for _page in range(20):
            query = {"pageSize": 1000, **({"pageToken": page_token} if page_token else {})}
            payload = self._get_json(f"{self.MODELS_API_URL}?{urlencode(query)}", self._headers(credentials))
            data = payload.get("models") if isinstance(payload, dict) else None
            if not isinstance(data, list):
                raise ValueError("Gemini повернув некоректний список моделей.")
            for item in data:
                if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                    continue
                # The docs show both field names for the supported methods; accept either.
                methods = item.get("supportedGenerationMethods") or item.get("supportedActions")
                models.append({
                    "id": item["name"].removeprefix("models/"),
                    "displayName": item.get("displayName") or item["name"].removeprefix("models/"),
                    "methods": methods if isinstance(methods, list) else None,
                })
            page_token = payload.get("nextPageToken")
            if not page_token:
                break
        return models

    def _is_text_model(self, model: Mapping[str, Any]) -> bool:
        methods = model.get("methods")
        if methods is not None and "generateContent" not in methods:
            return False
        return not self._has_non_text_marker(model["id"])

    def analyze(self, credentials: Mapping[str, str], prompt: str) -> str:
        body = json.dumps({"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": 4000}}).encode("utf-8")
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
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("Gemini повернув некоректну відповідь.") from error

        block_reason = None
        if isinstance(payload, dict):
            block_reason = (payload.get("promptFeedback") or {}).get("blockReason")
        if block_reason:
            raise ValueError(f"Gemini заблокував запит через фільтр контенту ({block_reason}).")

        candidates = payload.get("candidates") if isinstance(payload, dict) else None
        if not candidates:
            raise ValueError("Gemini не повернув жодної відповіді — ймовірно, заблоковано фільтром контенту.")

        finish_reason = candidates[0].get("finishReason") if isinstance(candidates[0], dict) else None
        if finish_reason == "MAX_TOKENS":
            raise ValueError("Gemini обірвав відповідь, бо вичерпано ліміт maxOutputTokens (текст неповний).")
        if finish_reason not in (None, "STOP"):
            raise ValueError(f"Gemini заблокував або обірвав відповідь ({finish_reason}), ймовірно через фільтр контенту.")

        try:
            text = candidates[0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as error:
            raise ValueError("Gemini повернув некоректну відповідь.") from error
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Gemini повернув порожній результат аналізу.")
        return text.strip()
