import json
import unittest

from backend.integrations.providers.gemini import GeminiProvider


class FakeTransport:
    def __init__(self, status=200, payload=None, error=None):
        self.status = status
        self.payload = payload if payload is not None else {"candidates": [{"content": {"parts": [{"text": "OK"}]}}]}
        self.error = error
        self.calls = []

    def post(self, url, headers, body, timeout):
        self.calls.append({"url": url, "headers": headers, "body": body, "timeout": timeout})
        if self.error:
            raise self.error
        return self.status, json.dumps(self.payload).encode("utf-8")


class GeminiProviderTests(unittest.TestCase):
    def test_verification_uses_generate_content_api_and_header_auth(self):
        transport = FakeTransport()
        provider = GeminiProvider(transport)

        result = provider.test_connection({"apiKey": "test-secret"})

        self.assertEqual("connected", result.status)
        call = transport.calls[0]
        self.assertEqual(
            GeminiProvider.GENERATE_CONTENT_URL_TEMPLATE.format(model=GeminiProvider.VERIFICATION_MODEL),
            call["url"],
        )
        self.assertEqual("test-secret", call["headers"]["x-goog-api-key"])
        self.assertNotIn("test-secret", call["url"])
        payload = json.loads(call["body"])
        self.assertEqual("Reply with OK.", payload["contents"][0]["parts"][0]["text"])
        self.assertNotIn("test-secret", call["body"].decode("utf-8"))

    def test_authentication_failure_is_sanitized(self):
        result = GeminiProvider(FakeTransport(status=400)).test_connection({"apiKey": "secret-key"})

        self.assertEqual("authentication_failed", result.code)
        self.assertNotIn("secret-key", result.message)

    def test_rate_limit_is_reported(self):
        result = GeminiProvider(FakeTransport(status=429)).test_connection({"apiKey": "secret-key"})

        self.assertEqual("rate_limited", result.code)
        self.assertNotIn("secret-key", result.message)

    def test_network_failure_is_sanitized(self):
        result = GeminiProvider(FakeTransport(error=ConnectionError("secret-key"))).test_connection(
            {"apiKey": "secret-key"}
        )

        self.assertEqual("unreachable", result.code)
        self.assertNotIn("secret-key", result.message)

    def test_invalid_success_payload_is_rejected(self):
        result = GeminiProvider(FakeTransport(payload={})).test_connection({"apiKey": "secret-key"})

        self.assertEqual("invalid_response", result.code)

    def test_analysis_uses_prompt_and_returns_text(self):
        transport = FakeTransport(payload={"candidates": [{"content": {"parts": [{"text": "Structured analysis"}]}}]})

        result = GeminiProvider(transport).analyze({"apiKey": "test-secret"}, "Analyze this chapter.")

        self.assertEqual("Structured analysis", result)
        payload = json.loads(transport.calls[0]["body"])
        self.assertEqual("Analyze this chapter.", payload["contents"][0]["parts"][0]["text"])
        self.assertNotIn("test-secret", transport.calls[0]["body"].decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
