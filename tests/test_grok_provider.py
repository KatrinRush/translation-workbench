import json
import unittest

from backend.integrations.base import TranslationRequest
from backend.integrations.providers.grok import GrokProvider


class FakeTransport:
    def __init__(self, status=200, payload=None, error=None):
        self.status = status
        self.payload = payload if payload is not None else {"id": "chatcmpl-test", "model": "grok-4.3"}
        self.error = error
        self.calls = []

    def post(self, url, headers, body, timeout):
        self.calls.append({"url": url, "headers": headers, "body": body, "timeout": timeout})
        if self.error:
            raise self.error
        return self.status, json.dumps(self.payload).encode("utf-8")


def chat_completion_payload(text, finish_reason="stop", **extra):
    """Build a body shaped like the real OpenAI-compatible Chat Completions API,
    which is what Grok actually speaks (unlike the newer Responses API)."""
    return {
        "id": "chatcmpl-test",
        "model": GrokProvider.VERIFICATION_MODEL,
        "choices": [
            {"message": {"role": "assistant", "content": text}, "finish_reason": finish_reason},
        ],
        **extra,
    }


class GrokProviderTests(unittest.TestCase):
    def test_validate_credentials_rejects_missing_or_blank_key(self):
        with self.assertRaises(ValueError):
            GrokProvider().validate_credentials({})
        with self.assertRaises(ValueError):
            GrokProvider().validate_credentials({"apiKey": "   "})

    def test_validate_credentials_strips_whitespace(self):
        result = GrokProvider().validate_credentials({"apiKey": "  xai-secret  "})
        self.assertEqual({"apiKey": "xai-secret"}, result)

    def test_verification_uses_chat_completions_api_and_bearer_auth(self):
        transport = FakeTransport()
        provider = GrokProvider(transport)

        result = provider.test_connection({"apiKey": "test-secret"})

        self.assertEqual("connected", result.status)
        call = transport.calls[0]
        self.assertEqual(GrokProvider.CHAT_COMPLETIONS_URL, call["url"])
        self.assertEqual("Bearer test-secret", call["headers"]["Authorization"])
        self.assertEqual("application/json", call["headers"]["Content-Type"])
        payload = json.loads(call["body"])
        self.assertEqual(GrokProvider.VERIFICATION_MODEL, payload["model"])
        self.assertEqual("Reply with OK.", payload["messages"][0]["content"])
        self.assertNotIn("test-secret", call["body"].decode("utf-8"))

    def test_authentication_failure_is_sanitized(self):
        result = GrokProvider(FakeTransport(status=401)).test_connection({"apiKey": "secret-key"})

        self.assertEqual("authentication_failed", result.code)
        self.assertNotIn("secret-key", result.message)

    def test_rate_limited_is_reported_distinctly(self):
        result = GrokProvider(FakeTransport(status=429)).test_connection({"apiKey": "secret-key"})

        self.assertEqual("rate_limited", result.code)

    def test_network_failure_is_sanitized(self):
        result = GrokProvider(FakeTransport(error=ConnectionError("secret-key"))).test_connection(
            {"apiKey": "secret-key"}
        )

        self.assertEqual("unreachable", result.code)
        self.assertNotIn("secret-key", result.message)

    def test_invalid_success_payload_is_rejected(self):
        result = GrokProvider(FakeTransport(payload={})).test_connection({"apiKey": "secret-key"})

        self.assertEqual("invalid_response", result.code)

    def test_analysis_uses_prompt_and_returns_message_content(self):
        transport = FakeTransport(payload=chat_completion_payload("Structured analysis"))

        result = GrokProvider(transport).analyze({"apiKey": "test-secret"}, "Analyze this chapter.")

        self.assertEqual("Structured analysis", result)
        payload = json.loads(transport.calls[0]["body"])
        self.assertEqual("Analyze this chapter.", payload["messages"][0]["content"])
        self.assertNotIn("test-secret", transport.calls[0]["body"].decode("utf-8"))

    def test_analysis_authentication_failure_is_sanitized(self):
        transport = FakeTransport(status=401)

        with self.assertRaises(ValueError) as context:
            GrokProvider(transport).analyze({"apiKey": "secret-key"}, "Analyze this chapter.")

        self.assertNotIn("secret-key", str(context.exception))

    def test_analysis_raises_clear_error_when_truncated_by_max_tokens(self):
        transport = FakeTransport(payload=chat_completion_payload("Draft notes cut off", finish_reason="length"))

        with self.assertRaises(ValueError) as context:
            GrokProvider(transport).analyze({"apiKey": "test-secret"}, "Analyze this chapter.")

        self.assertIn("max_tokens", str(context.exception))

    def test_analysis_raises_clear_error_on_missing_choices(self):
        transport = FakeTransport(payload={"choices": []})

        with self.assertRaises(ValueError) as context:
            GrokProvider(transport).analyze({"apiKey": "test-secret"}, "Analyze this chapter.")

        self.assertIn("некоректну відповідь", str(context.exception))

    def test_analysis_raises_clear_error_on_empty_text(self):
        transport = FakeTransport(payload=chat_completion_payload(""))

        with self.assertRaises(ValueError) as context:
            GrokProvider(transport).analyze({"apiKey": "test-secret"}, "Analyze this chapter.")

        self.assertIn("порожній результат", str(context.exception))

    def test_translate_is_not_implemented(self):
        with self.assertRaises(ValueError):
            GrokProvider().translate(
                {"apiKey": "test-secret"},
                TranslationRequest(text="Hello", target_language="UK"),
            )


if __name__ == "__main__":
    unittest.main()
