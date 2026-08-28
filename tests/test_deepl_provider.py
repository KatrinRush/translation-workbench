import json
import unittest
from urllib.parse import parse_qs

from backend.integrations.base import GlossaryDefinition, TranslationRequest
from backend.integrations.providers.deepl import DeepLProvider


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
            TranslationRequest(text="Original paragraph", target_language="UK", context="Use an informal tone."),
        )

        body = parse_qs(transport.calls[0]["body"].decode("utf-8"))
        self.assertEqual(["Original paragraph"], body["text"])
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


if __name__ == "__main__":
    unittest.main()