from contextlib import redirect_stdout
import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs

from backend.integrations.base import GlossaryDefinition, QuotaExceededError, TranslationRequest
from backend.integrations.providers.deepl import DeepLProvider, UrllibHttpTransport


class FakeTransport:
    def __init__(self, status=200, payload=None, error=None):
        self.status = status
        self.payload = payload or {}
        self.error = error
        self.calls = []

    def get(self, url, headers, timeout):
        self.calls.append({"url": url, "headers": headers, "timeout": timeout})
        if self.error:
            raise self.error
        return self.status, json.dumps(self.payload).encode("utf-8")

    def post(self, url, headers, body, timeout):
        self.calls.append({"url": url, "headers": headers, "body": body, "timeout": timeout})
        if self.error:
            raise self.error
        return self.status, json.dumps(self.payload).encode("utf-8")

    def delete(self, url, headers, timeout):
        self.calls.append({"url": url, "headers": headers, "timeout": timeout, "method": "DELETE"})
        if self.error:
            raise self.error
        return self.status, b""


class DeepLProviderTests(unittest.TestCase):
    def test_free_key_uses_free_usage_endpoint(self):
        transport = FakeTransport(payload={"character_count": 12, "character_limit": 500000})
        provider = DeepLProvider(transport)

        result = provider.test_connection({"apiKey": "test-key:fx"})

        self.assertEqual("connected", result.status)
        self.assertEqual("free", result.metadata["accountType"])
        self.assertEqual(DeepLProvider.FREE_API_URL, transport.calls[0]["url"])
        self.assertEqual("DeepL-Auth-Key test-key:fx", transport.calls[0]["headers"]["Authorization"])

    def test_pro_key_uses_pro_usage_endpoint(self):
        transport = FakeTransport(payload={"character_count": 0, "character_limit": 1000})
        provider = DeepLProvider(transport)

        result = provider.test_connection({"apiKey": "test-key"})

        self.assertEqual("connected", result.status)
        self.assertEqual(DeepLProvider.PRO_API_URL, transport.calls[0]["url"])

    def test_authentication_failure_is_sanitized(self):
        result = DeepLProvider(FakeTransport(status=403)).test_connection({"apiKey": "secret-key"})

        self.assertEqual("authentication_failed", result.code)
        self.assertNotIn("secret-key", result.message)

    def test_network_failure_is_sanitized(self):
        result = DeepLProvider(FakeTransport(error=ConnectionError("secret-key"))).test_connection(
            {"apiKey": "secret-key"}
        )

        self.assertEqual("unreachable", result.code)
        self.assertNotIn("secret-key", result.message)

    def test_translation_rules_are_sent_as_context_not_source_text(self):
        transport = FakeTransport(payload={
            "translations": [{"text": "Переклад", "detected_source_language": "EN"}],
        })

        DeepLProvider(transport).translate(
            {"apiKey": "test-key:fx"},
            TranslationRequest(
                text="Original paragraph",
                target_language="UK",
                tag_handling="xml",
                tag_handling_version="v2",
                context="Use an informal tone.",
            ),
        )

        body = parse_qs(transport.calls[0]["body"].decode("utf-8"))
        self.assertEqual(["Original paragraph"], body["text"])
        self.assertEqual(["xml"], body["tag_handling"])
        self.assertEqual(["v2"], body["tag_handling_version"])
        self.assertEqual(["Use an informal tone."], body["context"])

    def test_glossary_is_created_as_tsv_and_used_by_translation(self):
        transport = FakeTransport(status=201, payload={"glossary_id": "glossary-1"})
        provider = DeepLProvider(transport)

        glossary_id = provider.create_glossary(
            {"apiKey": "test-key:fx"},
            GlossaryDefinition("Book glossary", "EN", "UK", (("dominant", "домінант"), ("submissive", "сабмісив"))),
        )

        create_body = parse_qs(transport.calls[0]["body"].decode("utf-8"))
        self.assertEqual("glossary-1", glossary_id)
        self.assertEqual(["dominant\tдомінант\nsubmissive\tсабмісив"], create_body["entries"])
        transport.status = 200
        transport.payload = {"translations": [{"text": "домінант", "detected_source_language": "EN"}]}
        provider.translate(
            {"apiKey": "test-key:fx"},
            TranslationRequest("dominant", "UK", source_language="EN", glossary_id=glossary_id),
        )
        translate_body = parse_qs(transport.calls[1]["body"].decode("utf-8"))
        self.assertEqual(["EN"], translate_body["source_lang"])
        self.assertEqual(["glossary-1"], translate_body["glossary_id"])


class DeepLTranslationDebugLoggingTests(unittest.TestCase):
    def _translate_and_capture(self, request, payload):
        provider = DeepLProvider(FakeTransport(payload=payload))
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            provider.translate({"apiKey": "test-key:fx"}, request)
        return buffer.getvalue()

    def test_logs_source_context_and_result(self):
        output = self._translate_and_capture(
            TranslationRequest(
                text="Woland smiled.",
                target_language="UK",
                source_language="EN",
                context="Woland jumps down from a roof beam.",
            ),
            {"translations": [{"text": "Воланд усміхнувся.", "detected_source_language": "EN"}]},
        )

        self.assertIn("[DEEPL DEBUG] source='Woland smiled.'", output)
        self.assertIn("[DEEPL DEBUG] context='Woland jumps down from a roof beam.'", output)
        self.assertIn("[DEEPL DEBUG] result='Воланд усміхнувся.'", output)

    def test_debug_logging_never_contains_the_api_key(self):
        output = self._translate_and_capture(
            TranslationRequest(text="Original", target_language="UK"),
            {"translations": [{"text": "Оригінал"}]},
        )

        self.assertNotIn("test-key:fx", output)
        self.assertNotIn("DeepL-Auth-Key", output)

    def test_translate_raises_quota_exceeded_on_456(self):
        transport = FakeTransport(status=456)
        provider = DeepLProvider(transport)

        with redirect_stdout(io.StringIO()):
            with self.assertRaises(QuotaExceededError):
                provider.translate(
                    {"apiKey": "test-key:fx"},
                    TranslationRequest(text="Original", target_language="UK"),
                )

    def test_translate_failure_includes_status_and_is_logged(self):
        transport = FakeTransport(status=502)
        provider = DeepLProvider(transport)

        with redirect_stdout(io.StringIO()):
            with self.assertLogs(level="ERROR") as logs:
                with self.assertRaises(ValueError) as error:
                    provider.translate(
                        {"apiKey": "secret-key:fx"},
                        TranslationRequest(text="Original", target_language="UK"),
                    )

        self.assertIn("502", str(error.exception))
        self.assertTrue(any("502" in message for message in logs.output))
        self.assertNotIn("secret-key", "\n".join(logs.output))

    def test_translate_failure_surfaces_deepl_error_message(self):
        transport = FakeTransport(status=400, payload={"message": "target_lang is not supported."})
        provider = DeepLProvider(transport)

        with redirect_stdout(io.StringIO()):
            with self.assertRaises(ValueError) as error:
                provider.translate(
                    {"apiKey": "test-key:fx"},
                    TranslationRequest(text="Original", target_language="UK"),
                )

        self.assertIn("target_lang is not supported.", str(error.exception))


class UrllibHttpTransportTests(unittest.TestCase):
    """urlopen raises HTTPError for any non-2xx status instead of returning it, and
    HTTPError's body can only be read once — via error.read(). Discarding it (as
    `except HTTPError as error: return error.code, b""` used to) means DeepL's own
    error message is gone by the time translate() or our error logging tries to
    read it, even though nothing about the *request* was wrong."""

    def _http_error(self, code, body):
        return HTTPError(
            url="https://api.deepl.com/v2/translate",
            code=code,
            msg="Bad Request",
            hdrs=None,
            fp=io.BytesIO(body),
        )

    def test_post_surfaces_the_real_error_body(self):
        transport = UrllibHttpTransport()
        error_body = b'{"message": "target_lang is not supported."}'
        with patch("backend.integrations.providers.deepl.urlopen", side_effect=self._http_error(400, error_body)):
            status, body = transport.post(
                "https://api.deepl.com/v2/translate", {}, b"text=hi", timeout=1.0,
            )

        self.assertEqual(400, status)
        self.assertEqual(error_body, body)

    def test_get_surfaces_the_real_error_body(self):
        transport = UrllibHttpTransport()
        error_body = b'{"message": "Authorization failed."}'
        with patch("backend.integrations.providers.deepl.urlopen", side_effect=self._http_error(403, error_body)):
            status, body = transport.get("https://api.deepl.com/v2/usage", {}, timeout=1.0)

        self.assertEqual(403, status)
        self.assertEqual(error_body, body)

    def test_delete_surfaces_the_real_error_body(self):
        transport = UrllibHttpTransport()
        error_body = b'{"message": "Glossary not found."}'
        with patch("backend.integrations.providers.deepl.urlopen", side_effect=self._http_error(404, error_body)):
            status, body = transport.delete("https://api.deepl.com/v2/glossaries/x", {}, timeout=1.0)

        self.assertEqual(404, status)
        self.assertEqual(error_body, body)

    def test_translate_through_the_real_transport_surfaces_deepl_message_on_400(self):
        transport = UrllibHttpTransport()
        error_body = b'{"message": "target_lang is not supported."}'
        provider = DeepLProvider(transport)
        with patch("backend.integrations.providers.deepl.urlopen", side_effect=self._http_error(400, error_body)):
            with redirect_stdout(io.StringIO()):
                with self.assertRaises(ValueError) as error:
                    provider.translate(
                        {"apiKey": "test-key:fx"},
                        TranslationRequest(text="Original", target_language="UK"),
                    )

        self.assertIn("target_lang is not supported.", str(error.exception))


if __name__ == "__main__":
    unittest.main()