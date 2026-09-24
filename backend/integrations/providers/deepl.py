"""DeepL connection validation without translation behavior."""

from __future__ import annotations

import json
import logging
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..base import CredentialField, ConnectionTestResult, GlossaryDefinition, GlossaryLimitError, GlossarySummary, IntegrationProvider, ProviderDescriptor, QuotaExceededError, TranslationRequest, TranslationResult


def _decode_error_message(body: bytes) -> str | None:
    if not body:
        return None
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
        return None
    message = payload.get("message") if isinstance(payload, dict) else None
    return message if isinstance(message, str) and message.strip() else None


class HttpTransport(Protocol):
    def get(self, url: str, headers: Mapping[str, str], timeout: float) -> tuple[int, bytes]: ...

    def post(self, url: str, headers: Mapping[str, str], body: bytes, timeout: float) -> tuple[int, bytes]: ...

    def delete(self, url: str, headers: Mapping[str, str], timeout: float) -> tuple[int, bytes]: ...


class UrllibHttpTransport:
    def get(self, url: str, headers: Mapping[str, str], timeout: float) -> tuple[int, bytes]:
        request = Request(url, headers=dict(headers), method="GET")
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.status, response.read()
        except HTTPError as error:
            return error.code, b""
        except (URLError, TimeoutError, OSError) as error:
            raise ConnectionError("The provider could not be reached.") from error

    def post(self, url: str, headers: Mapping[str, str], body: bytes, timeout: float) -> tuple[int, bytes]:
        request = Request(url, headers=dict(headers), data=body, method="POST")
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.status, response.read()
        except HTTPError as error:
            return error.code, b""
        except (URLError, TimeoutError, OSError) as error:
            raise ConnectionError("The provider could not be reached.") from error

    def delete(self, url: str, headers: Mapping[str, str], timeout: float) -> tuple[int, bytes]:
        request = Request(url, headers=dict(headers), method="DELETE")
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.status, response.read()
        except HTTPError as error:
            return error.code, b""
        except (URLError, TimeoutError, OSError) as error:
            raise ConnectionError("The provider could not be reached.") from error


class DeepLProvider(IntegrationProvider):
    FREE_API_URL = "https://api-free.deepl.com/v2/usage"
    PRO_API_URL = "https://api.deepl.com/v2/usage"
    FREE_TRANSLATE_URL = "https://api-free.deepl.com/v2/translate"
    PRO_TRANSLATE_URL = "https://api.deepl.com/v2/translate"
    FREE_GLOSSARIES_URL = "https://api-free.deepl.com/v2/glossaries"
    PRO_GLOSSARIES_URL = "https://api.deepl.com/v2/glossaries"

    def __init__(self, transport: HttpTransport | None = None):
        self._transport = transport or UrllibHttpTransport()

    @property
    def descriptor(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            provider_id="deepl",
            display_name="DeepL",
            description="Перевірка доступу до DeepL API та поточного ліміту символів.",
            credential_fields=(
                CredentialField(
                    name="apiKey",
                    label="API key",
                    placeholder="Введіть ключ DeepL API",
                ),
            ),
        )

    def validate_credentials(self, credentials: Mapping[str, Any]) -> dict[str, str]:
        api_key = credentials.get("apiKey")
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("DeepL API key is required.")
        return {"apiKey": api_key.strip()}

    def test_connection(self, credentials: Mapping[str, str]) -> ConnectionTestResult:
        api_key = credentials["apiKey"]
        account_type = "free" if api_key.endswith(":fx") else "pro"
        url = self.FREE_API_URL if account_type == "free" else self.PRO_API_URL
        try:
            status, body = self._transport.get(
                url,
                {"Authorization": f"DeepL-Auth-Key {api_key}", "Accept": "application/json"},
                timeout=10.0,
            )
        except ConnectionError:
            return ConnectionTestResult("error", "unreachable", "Не вдалося з’єднатися з DeepL.")

        if status == 200:
            try:
                payload = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return ConnectionTestResult("error", "invalid_response", "DeepL повернув некоректну відповідь.")
            metadata = {
                "accountType": account_type,
                "characterCount": payload.get("character_count"),
                "characterLimit": payload.get("character_limit"),
            }
            return ConnectionTestResult("connected", "ok", "З’єднання з DeepL встановлено.", metadata)
        if status in {401, 403}:
            return ConnectionTestResult("error", "authentication_failed", "DeepL відхилив API key.")
        if status == 429:
            return ConnectionTestResult("error", "rate_limited", "DeepL тимчасово обмежив кількість запитів.")
        return ConnectionTestResult("error", "provider_error", "DeepL не зміг перевірити з’єднання.")

    def translate(self, credentials: Mapping[str, str], request: TranslationRequest) -> TranslationResult:
        api_key = credentials["apiKey"]
        url = self.FREE_TRANSLATE_URL if api_key.endswith(":fx") else self.PRO_TRANSLATE_URL
        body_fields = {
            "text": request.text,
            "target_lang": request.target_language,
            "preserve_formatting": "1",
        }
        if request.source_language:
            body_fields["source_lang"] = request.source_language
        if request.tag_handling:
            body_fields["tag_handling"] = request.tag_handling
        if request.tag_handling_version:
            body_fields["tag_handling_version"] = request.tag_handling_version
        if request.context:
            body_fields["context"] = request.context
        if request.glossary_id:
            body_fields["glossary_id"] = request.glossary_id
        if request.model_type:
            body_fields["model_type"] = request.model_type
        body = urlencode(body_fields).encode("utf-8")
        print(
            "[DEEPL DEBUG]",
            f"tag_handling={body_fields.get('tag_handling')!r}",
            f"tag_handling_version={body_fields.get('tag_handling_version')!r}",
            f"model_type={body_fields.get('model_type')!r}",
            f"glossary_id={body_fields.get('glossary_id')!r}",
            f"context_present={'context' in body_fields}",
            f"context={body_fields.get('context')!r}",
        )
        print("[DEEPL DEBUG]", f"source={body_fields['text']!r}")
        print("[DEEPL DEBUG]", f"context={body_fields.get('context')!r}")
        try:
            status, response_body = self._transport.post(
                url,
                {
                    "Authorization": f"DeepL-Auth-Key {api_key}",
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body,
                timeout=20.0,
            )
        except ConnectionError as error:
            logging.error("DeepL translate request could not reach the API: %s", error)
            raise ValueError("Не вдалося з’єднатися з DeepL.") from error

        if status != 200:
            # Body never contains the API key (that's only in our outgoing request headers),
            # so logging it whole is safe and gives the actual reason a generic status hides.
            logging.error("DeepL translate request failed: status=%s body=%r", status, response_body[:1000])
            message = _decode_error_message(response_body)
            detail = f" {message}" if message else ""
            if status in {401, 403}:
                raise ValueError(f"DeepL відхилив API key.{detail}")
            if status == 429:
                raise ValueError(f"DeepL тимчасово обмежив кількість запитів.{detail}")
            if status == 456:
                raise QuotaExceededError(f"DeepL вичерпав ліміт символів для цього підключення.{detail}")
            raise ValueError(f"DeepL не зміг виконати переклад (HTTP {status}).{detail}")
        try:
            payload = json.loads(response_body.decode("utf-8"))
            translation = payload["translations"][0]
            translated_text = translation["text"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError) as error:
            logging.error("DeepL translate returned an unparsable payload: %r", response_body[:1000])
            raise ValueError("DeepL повернув некоректну відповідь.") from error
        if not isinstance(translated_text, str):
            raise ValueError("DeepL повернув некоректну відповідь.")
        print("[DEEPL DEBUG]", f"result={translated_text!r}")
        return TranslationResult(
            text=translated_text,
            detected_source_language=translation.get("detected_source_language"),
        )

    def create_glossary(self, credentials: Mapping[str, str], glossary: GlossaryDefinition) -> str:
        api_key = credentials["apiKey"]
        url = self.FREE_GLOSSARIES_URL if api_key.endswith(":fx") else self.PRO_GLOSSARIES_URL
        entries = "\n".join(f"{source}\t{target}" for source, target in glossary.entries)
        body = urlencode({
            "name": glossary.name,
            "source_lang": glossary.source_language,
            "target_lang": glossary.target_language,
            "entries": entries,
            "entries_format": "tsv",
        }).encode("utf-8")
        try:
            status, response_body = self._transport.post(
                url,
                {
                    "Authorization": f"DeepL-Auth-Key {api_key}",
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body,
                timeout=20.0,
            )
        except ConnectionError as error:
            raise ValueError("Не вдалося синхронізувати глосарій з DeepL.") from error
        if status == 456:
            message = _decode_error_message(response_body)
            if message:
                raise GlossaryLimitError(f"DeepL відхилив синхронізацію глосарію: {message}.")
            raise GlossaryLimitError("DeepL досяг ліміту глосаріїв.")
        if status != 201:
            raise ValueError("DeepL не зміг створити глосарій.")
        try:
            glossary_id = json.loads(response_body.decode("utf-8"))["glossary_id"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as error:
            raise ValueError("DeepL повернув некоректну відповідь для глосарію.") from error
        if not isinstance(glossary_id, str) or not glossary_id:
            raise ValueError("DeepL повернув некоректну відповідь для глосарію.")
        return glossary_id

    def list_glossaries(self, credentials: Mapping[str, str]) -> list[GlossarySummary]:
        api_key = credentials["apiKey"]
        url = self.FREE_GLOSSARIES_URL if api_key.endswith(":fx") else self.PRO_GLOSSARIES_URL
        try:
            status, body = self._transport.get(
                url,
                {"Authorization": f"DeepL-Auth-Key {api_key}", "Accept": "application/json"},
                timeout=20.0,
            )
        except ConnectionError as error:
            raise ValueError("Не вдалося отримати список глосаріїв DeepL.") from error
        if status != 200:
            raise ValueError("DeepL не зміг повернути список глосаріїв.")
        try:
            payload = json.loads(body.decode("utf-8"))
            entries = payload["glossaries"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as error:
            raise ValueError("DeepL повернув некоректну відповідь для списку глосаріїв.") from error
        summaries = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            glossary_id = entry.get("glossary_id")
            source_language = entry.get("source_lang")
            target_language = entry.get("target_lang")
            if not glossary_id or not source_language or not target_language:
                continue
            summaries.append(GlossarySummary(glossary_id, source_language.upper(), target_language.upper()))
        return summaries

    def delete_glossary(self, credentials: Mapping[str, str], glossary_id: str) -> None:
        api_key = credentials["apiKey"]
        base_url = self.FREE_GLOSSARIES_URL if api_key.endswith(":fx") else self.PRO_GLOSSARIES_URL
        try:
            status, _ = self._transport.delete(
                f"{base_url}/{glossary_id}",
                {"Authorization": f"DeepL-Auth-Key {api_key}"},
                timeout=20.0,
            )
        except ConnectionError as error:
            raise ValueError("Не вдалося синхронізувати глосарій з DeepL.") from error
        if status not in {204, 404}:
            raise ValueError("DeepL не зміг замінити попередній глосарій.")
