import json
import unittest

from backend.integrations.providers.openai import OpenAIProvider


class FakeTransport:
    def __init__(self, status=200, payload=None, error=None):
        self.status = status
        self.payload = payload if payload is not None else {"id": "resp_test", "model": "gpt-4.1-nano"}
        self.error = error
        self.calls = []

    def post(self, url, headers, body, timeout):
        self.calls.append({"url": url, "headers": headers, "body": body, "timeout": timeout})
        if self.error:
            raise self.error
        return self.status, json.dumps(self.payload).encode("utf-8")


class OpenAIProviderTests(unittest.TestCase):
    def test_verification_uses_responses_api_and_bearer_auth(self):
        transport = FakeTransport()
        provider = OpenAIProvider(transport)

        result = provider.test_connection({"apiKey": "test-secret"})

        self.assertEqual("connected", result.status)
        call = transport.calls[0]
        self.assertEqual(OpenAIProvider.RESPONSES_API_URL, call["url"])
        self.assertEqual("Bearer test-secret", call["headers"]["Authorization"])
        self.assertEqual("application/json", call["headers"]["Content-Type"])
        payload = json.loads(call["body"])
        self.assertEqual(OpenAIProvider.VERIFICATION_MODEL, payload["model"])
        self.assertEqual("Reply with OK.", payload["input"])
        self.assertNotIn("test-secret", call["body"].decode("utf-8"))

    def test_authentication_failure_is_sanitized(self):
        result = OpenAIProvider(FakeTransport(status=401)).test_connection({"apiKey": "secret-key"})

        self.assertEqual("authentication_failed", result.code)
        self.assertNotIn("secret-key", result.message)

    def test_network_failure_is_sanitized(self):
        result = OpenAIProvider(FakeTransport(error=ConnectionError("secret-key"))).test_connection(
            {"apiKey": "secret-key"}
        )

        self.assertEqual("unreachable", result.code)
        self.assertNotIn("secret-key", result.message)

    def test_invalid_success_payload_is_rejected(self):
        result = OpenAIProvider(FakeTransport(payload={})).test_connection({"apiKey": "secret-key"})

        self.assertEqual("invalid_response", result.code)


if __name__ == "__main__":
    unittest.main()