import json
import unittest

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


if __name__ == "__main__":
    unittest.main()
