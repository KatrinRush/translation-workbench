import json
import os
import unittest
from unittest import mock

from backend.integrations.base import TranslationRequest
from backend.integrations.providers.claude import ClaudeProvider


class FakeTransport:
    def __init__(self, status=200, payload=None, error=None):
        self.status = status
        self.payload = payload if payload is not None else {"id": "msg_test", "model": "claude-haiku-4-5-20251001"}
        self.error = error
        self.calls = []

    def post(self, url, headers, body, timeout):
        self.calls.append({"url": url, "headers": headers, "body": body, "timeout": timeout})
        if self.error:
            raise self.error
        return self.status, json.dumps(self.payload).encode("utf-8")


class ClaudeProviderTests(unittest.TestCase):
    def test_verification_uses_messages_api_and_api_key_header(self):
        transport = FakeTransport()
        provider = ClaudeProvider(transport)

        result = provider.test_connection({"apiKey": "test-secret"})

        self.assertEqual("connected", result.status)
        call = transport.calls[0]
        self.assertEqual(ClaudeProvider.MESSAGES_API_URL, call["url"])
        self.assertEqual("test-secret", call["headers"]["x-api-key"])
        self.assertEqual(ClaudeProvider.ANTHROPIC_VERSION, call["headers"]["anthropic-version"])
        payload = json.loads(call["body"])
        self.assertEqual(ClaudeProvider.VERIFICATION_MODEL, payload["model"])
        self.assertEqual("Reply with OK.", payload["messages"][0]["content"])
        self.assertNotIn("test-secret", call["body"].decode("utf-8"))

    def test_authentication_failure_is_sanitized(self):
        result = ClaudeProvider(FakeTransport(status=401)).test_connection({"apiKey": "secret-key"})

        self.assertEqual("authentication_failed", result.code)
        self.assertNotIn("secret-key", result.message)

    def test_rate_limit_is_reported(self):
        result = ClaudeProvider(FakeTransport(status=429)).test_connection({"apiKey": "secret-key"})

        self.assertEqual("rate_limited", result.code)
        self.assertNotIn("secret-key", result.message)

    def test_network_failure_is_sanitized(self):
        result = ClaudeProvider(FakeTransport(error=ConnectionError("secret-key"))).test_connection(
            {"apiKey": "secret-key"}
        )

        self.assertEqual("unreachable", result.code)
        self.assertNotIn("secret-key", result.message)

    def test_invalid_success_payload_is_rejected(self):
        result = ClaudeProvider(FakeTransport(payload={})).test_connection({"apiKey": "secret-key"})

        self.assertEqual("invalid_response", result.code)

    def test_analysis_uses_prompt_and_returns_text(self):
        transport = FakeTransport(payload={"content": [{"type": "text", "text": "Structured analysis"}]})

        result = ClaudeProvider(transport).analyze({"apiKey": "test-secret"}, "Analyze this chapter.")

        self.assertEqual("Structured analysis", result)
        payload = json.loads(transport.calls[0]["body"])
        self.assertEqual("Analyze this chapter.", payload["messages"][0]["content"])
        self.assertNotIn("test-secret", transport.calls[0]["body"].decode("utf-8"))

    def test_analysis_requests_a_generous_max_tokens_budget(self):
        transport = FakeTransport(payload={"content": [{"type": "text", "text": "Structured analysis"}]})

        ClaudeProvider(transport).analyze({"apiKey": "test-secret"}, "Analyze this chapter.")

        payload = json.loads(transport.calls[0]["body"])
        self.assertGreaterEqual(payload["max_tokens"], 4000)

    def test_analysis_raises_clear_error_when_truncated_by_max_tokens(self):
        transport = FakeTransport(payload={
            "content": [{"type": "text", "text": "Draft notes with no JSON marker yet"}],
            "stop_reason": "max_tokens",
        })

        with self.assertRaises(ValueError) as context:
            ClaudeProvider(transport).analyze({"apiKey": "test-secret"}, "Analyze this chapter.")

        self.assertIn("max_tokens", str(context.exception))


    # --- translate() -------------------------------------------------------------

    CHUNK = '<chunk><p id="p-1">Переклад</p></chunk>'

    def _translation_payload(self, text=None, **extra):
        return {
            "id": "msg_test",
            "model": "claude-sonnet-5-5",
            "stop_reason": "end_turn",
            "content": [{"type": "thinking", "thinking": ""}, {"type": "text", "text": text or self.CHUNK}],
            "usage": {"input_tokens": 10, "output_tokens": 5, "cache_creation_input_tokens": 700, "cache_read_input_tokens": 0},
            **extra,
        }

    def _translate(self, transport, **request_fields):
        request = TranslationRequest(
            text=request_fields.pop("text", "context + <chunk/>"),
            target_language="UK",
            instructions=request_fields.pop("instructions", "System rules"),
            **request_fields,
        )
        return ClaudeProvider(transport).translate({"apiKey": "test-secret"}, request)

    def test_translate_sends_cached_system_prompt_and_user_message(self):
        transport = FakeTransport(payload=self._translation_payload())

        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(ClaudeProvider.TRANSLATION_MODEL_ENV, None)
            result = self._translate(transport)

        call = transport.calls[0]
        payload = json.loads(call["body"])
        self.assertEqual("claude-sonnet-5-5", payload["model"])
        self.assertEqual([{"type": "text", "text": "System rules", "cache_control": {"type": "ephemeral"}}], payload["system"])
        self.assertEqual([{"role": "user", "content": "context + <chunk/>"}], payload["messages"])
        self.assertEqual({"effort": ClaudeProvider.TRANSLATION_EFFORT}, payload["output_config"])
        self.assertEqual("default", payload["fallbacks"])
        self.assertEqual(ClaudeProvider.FALLBACK_BETA, call["headers"]["anthropic-beta"])
        self.assertEqual("test-secret", call["headers"]["x-api-key"])
        self.assertNotIn("test-secret", call["body"].decode("utf-8"))
        self.assertLess(call["timeout"], 100)
        self.assertEqual(self.CHUNK, result.text)
        self.assertEqual("claude-sonnet-5-5", result.model)
        self.assertEqual(
            {"input_tokens": 10, "output_tokens": 5, "cache_creation_input_tokens": 700, "cache_read_input_tokens": 0},
            result.usage,
        )

    def test_translation_model_is_configurable(self):
        with mock.patch.dict(os.environ, {ClaudeProvider.TRANSLATION_MODEL_ENV: "claude-opus-5-5"}):
            transport = FakeTransport(payload=self._translation_payload())
            self._translate(transport)
            self.assertEqual("claude-opus-5-5", json.loads(transport.calls[0]["body"])["model"])

            transport = FakeTransport(payload=self._translation_payload())
            self._translate(transport, model="claude-haiku-4-5")
            payload = json.loads(transport.calls[0]["body"])
            self.assertEqual("claude-haiku-4-5", payload["model"])
            # Older models reject effort and server-side fallbacks, so neither is sent.
            self.assertNotIn("output_config", payload)
            self.assertNotIn("fallbacks", payload)
            self.assertNotIn("anthropic-beta", transport.calls[0]["headers"])

    def test_translate_strips_markdown_fence_and_prose_around_the_chunk(self):
        transport = FakeTransport(payload=self._translation_payload(f"Ось переклад:\n```xml\n{self.CHUNK}\n```"))

        self.assertEqual(self.CHUNK, self._translate(transport).text)

    def test_translate_returns_reply_without_chunk_unchanged_for_the_strict_check(self):
        transport = FakeTransport(payload=self._translation_payload("Іди, сказав він."))

        self.assertEqual("Іди, сказав він.", self._translate(transport).text)

    def test_translate_refusal_is_an_error(self):
        transport = FakeTransport(payload=self._translation_payload(
            "", stop_reason="refusal", stop_details={"type": "refusal", "category": "cyber"},
        ))

        with self.assertRaises(ValueError) as context:
            self._translate(transport)

        self.assertIn("відмовився", str(context.exception))
        self.assertIn("cyber", str(context.exception))

    def test_translate_truncated_by_max_tokens_is_an_error(self):
        transport = FakeTransport(payload=self._translation_payload(stop_reason="max_tokens"))

        with self.assertRaises(ValueError) as context:
            self._translate(transport)

        self.assertIn("max_tokens", str(context.exception))

    def test_translate_http_errors_are_sanitized_and_explained(self):
        cases = {
            401: "API key",
            429: "обмежив",
            529: "перевантажений",
            400: "HTTP 400",
        }
        for status, expected in cases.items():
            with self.subTest(status=status):
                transport = FakeTransport(status=status, payload={"error": {"message": "model: unknown model"}})
                with self.assertRaises(ValueError) as context:
                    self._translate(transport)
                self.assertIn(expected, str(context.exception))
                self.assertIn("unknown model", str(context.exception))
                self.assertNotIn("test-secret", str(context.exception))

    def test_translate_network_failure_is_sanitized(self):
        with self.assertRaises(ValueError) as context:
            self._translate(FakeTransport(error=ConnectionError("test-secret")))

        self.assertNotIn("test-secret", str(context.exception))

if __name__ == "__main__":
    unittest.main()
