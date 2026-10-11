import json
import os
import unittest
from unittest import mock
from urllib.parse import parse_qs, urlparse

from backend.integrations.base import TranslationRequest
from backend.integrations.providers.claude import ClaudeProvider
from backend.integrations.providers.gemini import GeminiProvider
from backend.integrations.providers.openai import OpenAIProvider

CHUNK = '<chunk><p id="p-1">Переклад</p></chunk>'


class MockTransport:
    """Answers POST/GET from queued (status, payload) pairs and records every call."""

    def __init__(self, *responses, error=None):
        self.responses = list(responses)
        self.error = error
        self.calls = []

    def _answer(self, call):
        self.calls.append(call)
        if self.error:
            raise self.error
        status, payload = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        return status, json.dumps(payload).encode("utf-8")

    def post(self, url, headers, body, timeout):
        return self._answer({"method": "POST", "url": url, "headers": headers, "body": json.loads(body), "timeout": timeout})

    def get(self, url, headers, timeout):
        return self._answer({"method": "GET", "url": url, "headers": headers, "timeout": timeout})


def translate(provider, **fields):
    request = TranslationRequest(
        text=fields.pop("text", "context + <chunk/>"),
        target_language="UK",
        instructions=fields.pop("instructions", "System rules"),
        **fields,
    )
    return provider.translate({"apiKey": "test-secret"}, request)


def openai_payload(text=CHUNK, **extra):
    return {
        "id": "resp_1",
        "model": "gpt-4.1-nano-2025-04-14",
        "status": "completed",
        "output": [
            {"type": "reasoning", "summary": []},
            {"type": "message", "content": [{"type": "output_text", "text": text}]},
        ],
        "usage": {"input_tokens": 1200, "output_tokens": 80, "input_tokens_details": {"cached_tokens": 1000}},
        **extra,
    }


def gemini_payload(text=CHUNK, finish="STOP", **extra):
    return {
        "candidates": [{
            "content": {"parts": [{"text": "thinking about it", "thought": True}, {"text": text}]},
            "finishReason": finish,
        }],
        "usageMetadata": {
            "promptTokenCount": 1500,
            "cachedContentTokenCount": 1024,
            "candidatesTokenCount": 70,
            "thoughtsTokenCount": 30,
        },
        "modelVersion": "gemini-3.1-flash-lite",
        **extra,
    }


class OpenAITranslateTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ, {}, clear=False)
        patcher.start()
        os.environ.pop(OpenAIProvider.TRANSLATION_MODEL_ENV, None)
        self.addCleanup(patcher.stop)

    def test_request_uses_responses_api_with_instructions_and_default_model(self):
        transport = MockTransport((200, openai_payload()))

        result = translate(OpenAIProvider(transport))

        call = transport.calls[0]
        self.assertEqual(OpenAIProvider.RESPONSES_API_URL, call["url"])
        self.assertEqual("Bearer test-secret", call["headers"]["Authorization"])
        self.assertEqual(OpenAIProvider.VERIFICATION_MODEL, call["body"]["model"])
        self.assertEqual("System rules", call["body"]["instructions"])
        self.assertEqual("context + <chunk/>", call["body"]["input"])
        self.assertLess(call["timeout"], 100)
        self.assertEqual(CHUNK, result.text)
        self.assertEqual("gpt-4.1-nano-2025-04-14", result.model)
        # input_tokens excludes the cached part, as for Claude.
        self.assertEqual(
            {"input_tokens": 200, "output_tokens": 80, "cache_read_input_tokens": 1000, "cache_creation_input_tokens": 0},
            result.usage,
        )

    def test_model_comes_from_request_then_env(self):
        transport = MockTransport((200, openai_payload()))
        translate(OpenAIProvider(transport), model="gpt-x-project")
        self.assertEqual("gpt-x-project", transport.calls[0]["body"]["model"])

        with mock.patch.dict(os.environ, {OpenAIProvider.TRANSLATION_MODEL_ENV: "gpt-x-env"}):
            translate(OpenAIProvider(transport))
        self.assertEqual("gpt-x-env", transport.calls[1]["body"]["model"])

    def test_markdown_fence_is_stripped(self):
        transport = MockTransport((200, openai_payload(f"```xml\n{CHUNK}\n```")))
        self.assertEqual(CHUNK, translate(OpenAIProvider(transport)).text)

    def test_refusal_incomplete_and_empty_replies_are_errors(self):
        cases = {
            "відмовився": openai_payload(output=[{"type": "message", "content": [{"type": "refusal", "refusal": "I can't help"}]}]),
            "max_output_tokens": openai_payload(status="incomplete", incomplete_details={"reason": "max_output_tokens"}),
            "content_filter": openai_payload(status="incomplete", incomplete_details={"reason": "content_filter"}),
            "порожній переклад": openai_payload(text="   "),
        }
        for expected, payload in cases.items():
            with self.subTest(expected=expected):
                with self.assertRaises(ValueError) as context:
                    translate(OpenAIProvider(MockTransport((200, payload))))
                self.assertIn(expected, str(context.exception))

    def test_http_errors_carry_the_provider_message_without_the_key(self):
        for status, expected in {401: "API key", 429: "обмежив", 503: "перевантажений", 400: "HTTP 400"}.items():
            with self.subTest(status=status):
                transport = MockTransport((status, {"error": {"message": "model gpt-x does not exist"}}))
                with self.assertRaises(ValueError) as context:
                    translate(OpenAIProvider(transport))
                self.assertIn(expected, str(context.exception))
                self.assertIn("does not exist", str(context.exception))
                self.assertNotIn("test-secret", str(context.exception))

    def test_network_failure_is_reported(self):
        with self.assertRaises(ValueError) as context:
            translate(OpenAIProvider(MockTransport(error=ConnectionError("test-secret"))))
        self.assertNotIn("test-secret", str(context.exception))


class GeminiTranslateTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ, {}, clear=False)
        patcher.start()
        os.environ.pop(GeminiProvider.TRANSLATION_MODEL_ENV, None)
        self.addCleanup(patcher.stop)

    def test_request_uses_system_instruction_and_keeps_key_out_of_url(self):
        transport = MockTransport((200, gemini_payload()))

        result = translate(GeminiProvider(transport), model="models/gemini-custom")

        call = transport.calls[0]
        self.assertEqual(GeminiProvider.GENERATE_CONTENT_URL_TEMPLATE.format(model="gemini-custom"), call["url"])
        self.assertNotIn("test-secret", call["url"])
        self.assertEqual("test-secret", call["headers"]["x-goog-api-key"])
        self.assertEqual({"parts": [{"text": "System rules"}]}, call["body"]["systemInstruction"])
        self.assertEqual([{"role": "user", "parts": [{"text": "context + <chunk/>"}]}], call["body"]["contents"])
        # Thought parts are reasoning, not the translation.
        self.assertEqual(CHUNK, result.text)
        self.assertEqual("gemini-3.1-flash-lite", result.model)
        self.assertEqual(
            {"input_tokens": 476, "output_tokens": 100, "cache_read_input_tokens": 1024, "cache_creation_input_tokens": 0},
            result.usage,
        )

    def test_default_model_is_the_analysis_model(self):
        transport = MockTransport((200, gemini_payload()))
        translate(GeminiProvider(transport))
        self.assertIn(f"/models/{GeminiProvider.VERIFICATION_MODEL}:generateContent", transport.calls[0]["url"])

    def test_safety_blocks_truncation_and_empty_replies_are_errors(self):
        cases = {
            "фільтр контенту (PROHIBITED_CONTENT)": {"promptFeedback": {"blockReason": "PROHIBITED_CONTENT"}},
            "SAFETY": gemini_payload(finish="SAFETY"),
            "RECITATION": gemini_payload(finish="RECITATION"),
            "maxOutputTokens": gemini_payload(finish="MAX_TOKENS"),
            "не повернув жодної відповіді": {"candidates": []},
            "порожній переклад": gemini_payload(text=""),
        }
        for expected, payload in cases.items():
            with self.subTest(expected=expected):
                with self.assertRaises(ValueError) as context:
                    translate(GeminiProvider(MockTransport((200, payload))))
                self.assertIn(expected, str(context.exception))

    def test_reply_without_chunk_is_passed_on_for_the_strict_check(self):
        transport = MockTransport((200, gemini_payload("Ось переклад без XML")))
        self.assertEqual("Ось переклад без XML", translate(GeminiProvider(transport)).text)


class ModelListTests(unittest.TestCase):
    def test_claude_lists_all_pages(self):
        transport = MockTransport(
            (200, {"data": [{"id": "claude-a", "display_name": "Claude A"}], "has_more": True, "last_id": "claude-a"}),
            (200, {"data": [{"id": "claude-b", "display_name": "Claude B"}], "has_more": False, "last_id": "claude-b"}),
        )

        models = ClaudeProvider(transport).list_models({"apiKey": "test-secret"})

        self.assertEqual([{"id": "claude-a", "displayName": "Claude A"}, {"id": "claude-b", "displayName": "Claude B"}], models)
        self.assertEqual("test-secret", transport.calls[0]["headers"]["x-api-key"])
        self.assertEqual(["claude-a"], parse_qs(urlparse(transport.calls[1]["url"]).query)["after_id"])
        self.assertTrue(all(call["method"] == "GET" for call in transport.calls))

    def test_openai_keeps_only_text_generation_models(self):
        ids = [
            "gpt-4.1-nano", "gpt-x", "o3-mini", "chatgpt-x", "text-embedding-3-large", "whisper-1", "tts-1",
            "dall-e-3", "gpt-image-1", "gpt-4o-realtime-preview", "gpt-4o-audio-preview", "omni-moderation-latest",
            "gpt-4o-transcribe", "babbage-002", "gpt-3.5-turbo-instruct",
        ]
        transport = MockTransport((200, {"object": "list", "data": [{"id": model_id, "object": "model"} for model_id in ids]}))

        models = OpenAIProvider(transport).list_models({"apiKey": "test-secret"})

        self.assertEqual(["chatgpt-x", "gpt-4.1-nano", "gpt-x", "o3-mini"], [model["id"] for model in models])
        self.assertEqual("Bearer test-secret", transport.calls[0]["headers"]["Authorization"])

    def test_gemini_keeps_generate_content_text_models_across_pages(self):
        transport = MockTransport(
            (200, {
                "models": [
                    {"name": "models/gemini-3.1-flash-lite", "displayName": "Gemini Flash-Lite", "supportedGenerationMethods": ["generateContent", "countTokens"]},
                    {"name": "models/text-embedding-004", "supportedGenerationMethods": ["embedContent"]},
                    {"name": "models/gemini-x-image", "supportedGenerationMethods": ["generateContent"]},
                ],
                "nextPageToken": "page-2",
            }),
            (200, {"models": [
                {"name": "models/gemini-y", "displayName": "Gemini Y", "supportedActions": ["generateContent"]},
                {"name": "models/gemini-y-tts", "supportedActions": ["generateContent"]},
                {"name": "models/aqa", "supportedActions": ["generateAnswer"]},
            ]}),
        )

        models = GeminiProvider(transport).list_models({"apiKey": "test-secret"})

        self.assertEqual(
            [{"id": "gemini-3.1-flash-lite", "displayName": "Gemini Flash-Lite"}, {"id": "gemini-y", "displayName": "Gemini Y"}],
            models,
        )
        self.assertNotIn("test-secret", transport.calls[0]["url"])
        self.assertEqual(["page-2"], parse_qs(urlparse(transport.calls[1]["url"]).query)["pageToken"])

    def test_failed_listing_is_a_readable_error(self):
        for provider_class in (ClaudeProvider, OpenAIProvider, GeminiProvider):
            with self.subTest(provider=provider_class.__name__):
                transport = MockTransport((401, {"error": {"message": "invalid x-api-key"}}))
                with self.assertRaises(ValueError) as context:
                    provider_class(transport).list_models({"apiKey": "test-secret"})
                self.assertIn("API key", str(context.exception))
                self.assertNotIn("test-secret", str(context.exception))

                with self.assertRaises(ValueError):
                    provider_class(MockTransport(error=ConnectionError("down"))).list_models({"apiKey": "test-secret"})


if __name__ == "__main__":
    unittest.main()
