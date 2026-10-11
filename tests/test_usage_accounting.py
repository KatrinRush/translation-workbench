"""Token/cost accounting (translation_usage, model_prices), reasoning levels, batch settings."""
import contextlib
import io
import json
import re
import sqlite3
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet

from backend import server
from backend.chat_service import ChatService
from backend.integrations.base import ConnectionTestResult, IntegrationProvider, ProviderDescriptor, TranslationRequest
from backend.integrations.credentials import CredentialVault
from backend.integrations.llm_translation import LlmTranslationProvider
from backend.integrations.providers.claude import ClaudeProvider
from backend.integrations.providers.gemini import GeminiProvider
from backend.integrations.providers.grok import GrokProvider
from backend.integrations.providers.openai import OpenAIProvider
from backend.integrations.registry import ProviderRegistry
from backend.qa.service import QaService
from backend.storage import Storage
from backend.translations.service import TranslationService, TranslationServiceError
from backend.usage import DEFAULT_MODEL_PRICES, capture_usage, find_price, report_usage, row_cost, summarize

CREDENTIALS = {"apiKey": "k"}
USAGE = {"input_tokens": 1000, "output_tokens": 500, "cache_read_input_tokens": 2000, "cache_creation_input_tokens": 100}


def chunk_reply(message, text="Переклад"):
    root = ET.fromstring(re.search(r"<chunk>.*</chunk>", message, re.S).group(0))
    for element in root.findall("p"):
        for child in list(element):
            element.remove(child)
        element.text = text
    return ET.tostring(root, encoding="unicode")


class ScriptedClaudeTransport:
    """Mock Claude HTTP. Each call takes the next scripted step: a dict {status, text|builder,
    stop_reason, usage, model}; the last step repeats."""

    def __init__(self, *steps):
        self.steps = list(steps)
        self.bodies = []

    def post(self, url, headers, body, timeout):
        payload = json.loads(body)
        self.bodies.append(payload)
        step = self.steps.pop(0) if len(self.steps) > 1 else self.steps[0]
        if step.get("status", 200) != 200:
            return step["status"], json.dumps({"error": {"message": step.get("message", "boom")}}).encode()
        message = payload["messages"][0]["content"]
        text = step["builder"](message) if "builder" in step else chunk_reply(message)
        reply = {"model": step.get("model", "claude-sonnet-5-5"), "stop_reason": step.get("stop_reason", "end_turn"),
                 "content": [{"type": "text", "text": text}], "usage": step.get("usage", USAGE)}
        return 200, json.dumps(reply, ensure_ascii=False).encode("utf-8")


class Fixture(unittest.TestCase):
    PARAGRAPHS = ["Razak fled Justice’s court."]

    def setUp(self):
        LlmTranslationProvider._REJECTED_REASONING.clear()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "workbench.sqlite3"
        self.storage = Storage(self.database_path)
        self.vault = CredentialVault(Fernet(Fernet.generate_key()))
        connection = self.storage.create_integration_connection("claude", "Claude", self.vault.encrypt({"apiKey": "k"}))
        self.storage.update_integration_connection_status(connection["connectionId"], "connected", "ok", "ok", {})
        self.connection = connection
        self.project_id = self.storage.create_project({
            "title": "Cost", "status": "translation",
            "aiConfiguration": {"translationConnectionId": connection["connectionId"]},
        })["projectId"]
        self.storage.save_book_structure(
            self.project_id, "book.epub", "application/epub+zip", b"book",
            {"chapters": [{"title": "CHAPTER 38", "elements": [{"type": "paragraph", "text": text} for text in self.PARAGRAPHS]}]},
        )
        chapter = self.storage.get_book_structure(self.project_id)["chapters"][0]
        self.chapter_id = chapter["chapterId"]
        self.ids = [element["paragraphId"] for element in chapter["elements"]]

    def tearDown(self):
        self.temporary_directory.cleanup()

    def service(self, transport):
        return TranslationService(self.storage, self.vault, ProviderRegistry([ClaudeProvider(transport)]))

    def translate(self, transport, batch_index=0):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = self.service(transport).translate_chapter(self.project_id, self.chapter_id, {"batchIndex": batch_index})
        return result, output.getvalue()

    def usage_rows(self):
        return self.storage.list_translation_usage(self.project_id)


class PricingTests(unittest.TestCase):
    PRICES = {
        "gpt-5.5": {"inputPerMTok": 5, "outputPerMTok": 30, "cacheReadPerMTok": None, "cacheWritePerMTok": None},
        "claude-sonnet-5-5": {"inputPerMTok": 2, "outputPerMTok": 10, "cacheReadPerMTok": 0.2, "cacheWritePerMTok": 2.5},
        "half": {"inputPerMTok": 1, "outputPerMTok": None, "cacheReadPerMTok": None, "cacheWritePerMTok": None},
    }

    def test_exact_name_or_a_trailing_date_only(self):
        self.assertIs(self.PRICES["gpt-5.5"], find_price("gpt-5.5", self.PRICES))
        self.assertIs(self.PRICES["gpt-5.5"], find_price("gpt-5.5-2026-03-01", self.PRICES))
        self.assertIs(self.PRICES["claude-sonnet-5-5"], find_price("claude-sonnet-5-5-20260115", self.PRICES))
        self.assertIs(self.PRICES["gpt-5.5"], find_price("models/gpt-5.5", self.PRICES))

    def test_other_suffixes_are_not_prefix_matches(self):
        for model in ("gpt-5.5-pro", "gpt-5.5-mini", "gpt-5.5-pro-2026-03-01", "gpt-5", "gpt-5.5x", "gpt-5.5-preview", "", None):
            with self.subTest(model=model):
                self.assertIsNone(find_price(model, self.PRICES))

    def test_cost_from_all_four_prices(self):
        row = {"inputTokens": 1000, "outputTokens": 500, "cacheReadTokens": 2000, "cacheWriteTokens": 100}
        cost, estimated = row_cost(row, self.PRICES["claude-sonnet-5-5"])
        self.assertAlmostEqual((1000 * 2 + 500 * 10 + 2000 * 0.2 + 100 * 2.5) / 1e6, cost)
        self.assertFalse(estimated)

    def test_cache_without_its_own_price_is_priced_as_input_and_marked_an_estimate(self):
        row = {"inputTokens": 1000, "outputTokens": 100, "cacheReadTokens": 4000, "cacheWriteTokens": 0}
        cost, estimated = row_cost(row, self.PRICES["gpt-5.5"])
        self.assertAlmostEqual((1000 * 5 + 100 * 30 + 4000 * 5) / 1e6, cost)
        self.assertTrue(estimated)
        _cost, estimated = row_cost({"inputTokens": 10, "outputTokens": 1}, self.PRICES["gpt-5.5"])
        self.assertFalse(estimated)  # nothing came from the cache: an exact figure

    def test_a_missing_price_means_no_cost(self):
        row = {"inputTokens": 10, "outputTokens": 10}
        self.assertEqual((None, False), row_cost(row, None))
        self.assertEqual((None, False), row_cost(row, self.PRICES["half"]))
        self.assertEqual((0.00001, False), row_cost({"inputTokens": 10}, self.PRICES["half"]))  # output price not needed

    def test_summary_flags_unpriced_models(self):
        rows = [
            {"model": "gpt-5.5", "inputTokens": 1_000_000, "outputTokens": 0},
            {"model": "mystery-model", "inputTokens": 5, "outputTokens": 5},
        ]
        total = summarize(rows, self.PRICES)
        self.assertEqual(5.0, total["costUsd"])
        self.assertTrue(total["unpriced"])
        only_unknown = summarize(rows[1:], self.PRICES)
        self.assertIsNone(only_unknown["costUsd"])


class MigrationTests(Fixture):
    def test_tables_exist_and_initial_prices_are_seeded(self):
        prices = self.storage.list_model_prices()
        self.assertEqual({"claude-sonnet-5-5", "gpt-5.5", "gemini-3.6-flash"}, set(prices))
        self.assertEqual((2, 10, 0.2, 2.5), tuple(prices["claude-sonnet-5-5"][key] for key in ("inputPerMTok", "outputPerMTok", "cacheReadPerMTok", "cacheWritePerMTok")))
        self.assertEqual((5, 30, None, None), tuple(prices["gpt-5.5"][key] for key in ("inputPerMTok", "outputPerMTok", "cacheReadPerMTok", "cacheWritePerMTok")))
        self.assertEqual((1.5, 7.5), (prices["gemini-3.6-flash"]["inputPerMTok"], prices["gemini-3.6-flash"]["outputPerMTok"]))
        self.assertEqual(set(DEFAULT_MODEL_PRICES), set(prices))

    def test_running_the_migration_again_is_idempotent_and_keeps_edits_and_usage(self):
        self.storage.save_model_prices([{"model": "gpt-5.5", "inputPerMTok": 4, "outputPerMTok": None}])
        self.storage.record_translation_usage(self.project_id, self.chapter_id, "claude", "m", "translate", USAGE)
        for _ in range(3):
            Storage(self.database_path)
        prices = self.storage.list_model_prices()
        self.assertEqual(3, len(prices))
        self.assertEqual((4, None), (prices["gpt-5.5"]["inputPerMTok"], prices["gpt-5.5"]["outputPerMTok"]))
        self.assertEqual(1, len(self.usage_rows()))

    def test_upgrading_a_database_without_the_tables_adds_them(self):
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("DROP TABLE translation_usage")
            connection.execute("DROP TABLE model_prices")
        storage = Storage(self.database_path)
        self.assertEqual(3, len(storage.list_model_prices()))
        self.assertEqual([], storage.list_translation_usage(self.project_id))
        self.assertEqual(1, len(self.storage.list_integration_connections()))  # nothing else touched

    def test_unknown_kinds_are_rejected_by_the_table(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.storage.record_translation_usage(self.project_id, None, "claude", "m", "bogus", USAGE)

    def test_usage_is_stored_apart_from_variants(self):
        self.translate(ScriptedClaudeTransport({}))
        self.assertEqual(1, len(self.usage_rows()))
        self.assertEqual(["claude"], [v["engine"] for v in self.storage.get_paragraph(self.ids[0])["translationVariants"]])


class TranslationUsageTests(Fixture):
    def test_every_batch_call_is_recorded_with_its_tokens(self):
        result, log = self.translate(ScriptedClaudeTransport({}))
        row, = self.usage_rows()
        self.assertEqual(("claude", "claude-sonnet-5-5", "translate", self.chapter_id), (row["engine"], row["model"], row["kind"], row["chapterId"]))
        self.assertEqual((1000, 500, 2000, 100), (row["inputTokens"], row["outputTokens"], row["cacheReadTokens"], row["cacheWriteTokens"]))
        summary = result["usageSummary"]
        self.assertAlmostEqual((1000 * 2 + 500 * 10 + 2000 * 0.2 + 100 * 2.5) / 1e6, summary["costUsd"])
        self.assertEqual((1, 3600), (summary["calls"], summary["tokens"]))
        self.assertFalse(summary["unpriced"])
        self.assertIn('"kind": "translate"', log)
        self.assertIn('"promptTokens": 3100', log)
        self.assertIn('"systemPromptChars"', log)

    def test_failed_batch_is_billed_and_recorded_but_saves_no_variant(self):
        transport = ScriptedClaudeTransport({"stop_reason": "max_tokens", "usage": {"input_tokens": 700, "output_tokens": 16000}})
        with self.assertRaises(TranslationServiceError):
            self.translate(transport)
        row, = self.usage_rows()
        self.assertEqual((700, 16000, "translate"), (row["inputTokens"], row["outputTokens"], row["kind"]))
        self.assertEqual([], self.storage.get_paragraph(self.ids[0])["translationVariants"])

    def test_unusable_xml_attempts_are_recorded_the_second_one_as_retry(self):
        transport = ScriptedClaudeTransport(
            {"builder": lambda message: "not xml at all", "usage": {"input_tokens": 10, "output_tokens": 5}},
            {"usage": {"input_tokens": 20, "output_tokens": 6}},
        )
        result, _log = self.translate(transport)
        self.assertEqual([("translate", 10), ("retry", 20)], [(row["kind"], row["inputTokens"]) for row in self.usage_rows()])
        self.assertEqual(2, result["usageSummary"]["calls"])

    def test_glossary_retry_is_recorded_as_retry(self):
        entry = self.storage.create_glossary_entry({"source": "Razak", "target": "Разак"})
        self.storage.update_project(self.project_id, {"projectGlossaryEntryIds": [entry["glossaryEntryId"]]})
        transport = ScriptedClaudeTransport(
            {"builder": lambda message: chunk_reply(message, "Рейзак утік."), "usage": {"input_tokens": 100, "output_tokens": 10}},
            {"builder": lambda message: chunk_reply(message, "Разак утік."), "usage": {"input_tokens": 120, "output_tokens": 11}},
        )
        result, log = self.translate(transport)
        self.assertEqual([("translate", 100), ("retry", 120)], [(row["kind"], row["inputTokens"]) for row in self.usage_rows()])
        self.assertEqual(2, len(transport.bodies))
        self.assertEqual([], self.storage.get_paragraph(self.ids[0])["translationVariants"][0]["warnings"])
        self.assertEqual(2, result["usageSummary"]["calls"])

    def test_a_call_that_failed_without_a_reply_writes_no_row(self):
        for status in (500, 429, 503):
            with self.subTest(status=status), self.assertRaises(TranslationServiceError):
                self.translate(ScriptedClaudeTransport({"status": status}))
        self.assertEqual([], self.usage_rows())

    def test_paragraph_button_is_recorded_too(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            data = self.service(ScriptedClaudeTransport({})).translate_paragraph(self.ids[0], {})
        self.assertEqual(1, len(self.usage_rows()))
        self.assertEqual(1, data["usageSummary"]["calls"])


class ReportApiTests(Fixture):
    class Handler:
        def __init__(self, payload=None):
            self.payload = payload

        def read_json(self):
            return self.payload

    def api(self, method, path, payload=None):
        with patch.object(server, "storage", self.storage):
            return server.WorkbenchHandler.handle_api(self.Handler(payload), method, path)

    def test_project_report_groups_by_model_chapter_and_kind_without_book_text(self):
        self.translate(ScriptedClaudeTransport({}))
        self.storage.record_translation_usage(self.project_id, self.chapter_id, "claude", "mystery-model", "qa", {"input_tokens": 50, "output_tokens": 5})
        self.storage.record_translation_usage(self.project_id, None, "openai", "gpt-5.5", "chat", {"input_tokens": 1_000_000})
        status, report = self.api("GET", f"/api/projects/{self.project_id}/usage")
        self.assertEqual(200, status)
        self.assertEqual({("claude", "claude-sonnet-5-5"), ("claude", "mystery-model"), ("openai", "gpt-5.5")},
                         {(item["engine"], item["model"]) for item in report["byModel"]})
        mystery = next(item for item in report["byModel"] if item["model"] == "mystery-model")
        self.assertIsNone(mystery["costUsd"])
        self.assertEqual(["mystery-model"], report["unpricedModels"])
        chapter = next(item for item in report["byChapter"] if item["chapterId"] == self.chapter_id)
        self.assertEqual((1, "CHAPTER 38"), (chapter["chapterIndex"], chapter["title"]))
        self.assertEqual(["chat", "qa", "translate"], [item["kind"] for item in report["byKind"]])
        self.assertAlmostEqual(0.00765 + 5.0, report["total"]["costUsd"])
        self.assertTrue(report["total"]["unpriced"])
        self.assertEqual(3, report["total"]["calls"])
        dump = json.dumps(report, ensure_ascii=False)
        for text in self.PARAGRAPHS + ["Переклад"]:
            self.assertNotIn(text, dump)

    def test_unknown_project(self):
        self.assertEqual(404, self.api("GET", "/api/projects/nope/usage")[0])

    def test_prices_can_be_listed_edited_added_and_cleared(self):
        status, body = self.api("GET", "/api/model-prices")
        self.assertEqual(200, status)
        self.assertEqual(3, len(body["prices"]))
        status, body = self.api("PUT", "/api/model-prices", {"prices": [
            {"model": "gpt-5.5", "inputPerMTok": 4.5, "outputPerMTok": 28, "cacheReadPerMTok": 0.5, "cacheWritePerMTok": None},
            {"model": " custom-model ", "inputPerMTok": 1, "outputPerMTok": 2},
            {"model": "gemini-3.6-flash", "inputPerMTok": None, "outputPerMTok": None},
        ]})
        self.assertEqual(200, status)
        prices = {item["model"]: item for item in body["prices"]}
        self.assertEqual((4.5, 28, 0.5), (prices["gpt-5.5"]["inputPerMTok"], prices["gpt-5.5"]["outputPerMTok"], prices["gpt-5.5"]["cacheReadPerMTok"]))
        self.assertEqual((1, 2), (prices["custom-model"]["inputPerMTok"], prices["custom-model"]["outputPerMTok"]))
        self.assertNotIn("gemini-3.6-flash", prices)  # all four prices cleared: the row is deleted
        # the cost follows the current table: the tokens are stored, the money is computed
        self.storage.record_translation_usage(self.project_id, None, "openai", "gpt-5.5", "chat", {"input_tokens": 1_000_000})
        self.assertAlmostEqual(4.5, self.api("GET", f"/api/projects/{self.project_id}/usage")[1]["total"]["costUsd"])
        self.api("PUT", "/api/model-prices", {"prices": [{"model": "gpt-5.5", "inputPerMTok": 1, "outputPerMTok": 1}]})
        self.assertAlmostEqual(1.0, self.api("GET", f"/api/projects/{self.project_id}/usage")[1]["total"]["costUsd"])

    def test_bad_prices_are_rejected(self):
        for payload in ({}, {"prices": []}, {"prices": [{"inputPerMTok": 1}]}, {"prices": [{"model": "x", "inputPerMTok": -1}]},
                        {"prices": [{"model": "x", "inputPerMTok": "5"}]}, {"prices": [{"model": "x", "inputPerMTok": True}]},
                        {"prices": [{"model": "x" * 101}]}):
            with self.subTest(payload=payload):
                self.assertEqual(400, self.api("PUT", "/api/model-prices", payload)[0])


# ---- usage from analyze(): QA, analysis and chat, all four providers ---------------------------


class JsonTransport:
    def __init__(self, payload):
        self.payload = payload

    def post(self, url, headers, body, timeout):
        return 200, json.dumps(self.payload).encode("utf-8")

    def get(self, url, headers, timeout):
        raise AssertionError("not used")


ANALYZE_REPLIES = {
    "claude": (lambda t: ClaudeProvider(t), {"model": "claude-haiku-4-5-20251001", "stop_reason": "end_turn", "content": [{"type": "text", "text": "ok"}],
                                           "usage": {"input_tokens": 100, "output_tokens": 50, "cache_read_input_tokens": 30, "cache_creation_input_tokens": 5}}),
    "openai": (lambda t: OpenAIProvider(t), {"model": "gpt-4.1-nano", "status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": "ok"}]}],
                                           "usage": {"input_tokens": 130, "output_tokens": 50, "input_tokens_details": {"cached_tokens": 30}}}),
    "gemini": (lambda t: GeminiProvider(t), {"modelVersion": "gemini-3.1-flash-lite", "candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "ok"}]}}],
                                           "usageMetadata": {"promptTokenCount": 130, "cachedContentTokenCount": 30, "candidatesTokenCount": 20, "thoughtsTokenCount": 30}}),
    "grok": (lambda t: GrokProvider(t), {"model": "grok-4.3", "choices": [{"finish_reason": "stop", "message": {"content": "ok"}}],
                                       "usage": {"prompt_tokens": 130, "completion_tokens": 50, "prompt_tokens_details": {"cached_tokens": 30}}}),
}


class AnalyzeUsageTests(unittest.TestCase):
    def test_every_provider_reports_usage_under_capture_and_still_returns_just_text(self):
        for provider_id, (make, payload) in ANALYZE_REPLIES.items():
            with self.subTest(provider=provider_id):
                provider = make(JsonTransport(payload))
                self.assertEqual("ok", provider.analyze(CREDENTIALS, "prompt"))  # unchanged without a recorder
                seen = []
                with capture_usage(lambda model, usage: seen.append((model, dict(usage)))):
                    self.assertEqual("ok", provider.analyze(CREDENTIALS, "prompt"))
                model, usage = seen[0]
                self.assertEqual(1, len(seen))
                self.assertEqual((100, 50, 30), (usage["input_tokens"], usage["output_tokens"], usage["cache_read_input_tokens"]))
                self.assertTrue(model)

    def test_a_truncated_analysis_was_billed_too(self):
        payload = dict(ANALYZE_REPLIES["claude"][1], stop_reason="max_tokens")
        seen = []
        with capture_usage(lambda model, usage: seen.append(usage)), self.assertRaises(ValueError):
            ClaudeProvider(JsonTransport(payload)).analyze(CREDENTIALS, "prompt")
        self.assertEqual(1, len(seen))

    def test_report_usage_outside_a_capture_is_a_noop(self):
        report_usage("m", {"input_tokens": 1})


class BilledProvider(IntegrationProvider):
    """analyze() reports tokens like the real providers do."""

    def __init__(self, provider_id="claude", reply="===JSON===\n[]"):
        self.provider_id, self.reply = provider_id, reply

    @property
    def descriptor(self):
        return ProviderDescriptor(self.provider_id, self.provider_id, "", ())

    def validate_credentials(self, credentials):
        return dict(credentials)

    def test_connection(self, credentials):
        return ConnectionTestResult("connected", "ok", "ok")

    def translate(self, credentials, request):
        raise AssertionError("translate() should not be called")

    def analyze(self, credentials, prompt):
        report_usage("claude-sonnet-5-5", {"input_tokens": 100, "output_tokens": 10, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0})
        return self.reply


class AnalyzeServicesTests(Fixture):
    PARAGRAPHS = ["One.", "Two."]

    def setUp(self):
        super().setUp()
        for paragraph_id in self.ids:
            self.storage.update_paragraph(paragraph_id, "Переклад", False)
        self.registry = ProviderRegistry([BilledProvider()])
        self.storage.update_project(self.project_id, {"aiConfiguration": {"analysisConnectionIds": [self.connection["connectionId"]]}})

    def test_ai_qa_chapter_analysis_and_chat_are_recorded_with_their_kind(self):
        QaService(self.storage, self.vault, self.registry).check_chapter_translation_quality(
            self.project_id, self.chapter_id, [self.connection["connectionId"]], batch_index=0)
        TranslationService(self.storage, self.vault, self.registry).analyze_chapter(
            self.project_id, self.chapter_id, {"connectionIds": [self.connection["connectionId"]], "categories": ["Тон"]})
        ChatService(self.storage, self.vault, self.registry).send_message(self.project_id, "Привіт", "claude")
        rows = self.usage_rows()
        self.assertEqual(["qa", "analysis", "chat"], [row["kind"] for row in rows])
        self.assertEqual([self.chapter_id, self.chapter_id, None], [row["chapterId"] for row in rows])
        self.assertTrue(all(row["engine"] == "claude" and row["inputTokens"] == 100 for row in rows))

    def test_a_qa_batch_that_fails_to_parse_still_records_each_attempt(self):
        service = QaService(self.storage, self.vault, ProviderRegistry([BilledProvider(reply="no json here")]))
        service.check_chapter_translation_quality(self.project_id, self.chapter_id, [self.connection["connectionId"]], batch_index=0)
        self.assertEqual(["qa"] * service._QUALITY_BATCH_ATTEMPTS, [row["kind"] for row in self.usage_rows()])


# ---- reasoning level -----------------------------------------------------------------------------


class CaptureTransport:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.bodies = []

    def post(self, url, headers, body, timeout):
        self.bodies.append(json.loads(body))
        reply = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        return reply if isinstance(reply, tuple) else (200, json.dumps(reply).encode("utf-8"))


CHUNK = '<chunk><p id="p-1">Hello</p></chunk>'
OPENAI_OK = {"model": "gpt-5.5", "status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": CHUNK}]}],
             "usage": {"input_tokens": 10, "output_tokens": 5}}
GEMINI_OK = {"modelVersion": "gemini-3.6-flash", "candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": CHUNK}]}}],
             "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5, "thoughtsTokenCount": 7}}
CLAUDE_OK = {"model": "claude-sonnet-5-5", "stop_reason": "end_turn", "content": [{"type": "text", "text": CHUNK}], "usage": USAGE}


def reject(message):
    return 400, json.dumps({"error": {"message": message}}).encode("utf-8")


class ReasoningTests(unittest.TestCase):
    def setUp(self):
        LlmTranslationProvider._REJECTED_REASONING.clear()

    def run_openai(self, transport, model="gpt-5.5", level="minimal"):
        return OpenAIProvider(transport).translate(CREDENTIALS, TranslationRequest(text=CHUNK, target_language="UK", model=model, reasoning=level))

    def run_gemini(self, transport, model="gemini-3.6-flash", level="medium"):
        return GeminiProvider(transport).translate(CREDENTIALS, TranslationRequest(text=CHUNK, target_language="UK", model=model, reasoning=level))

    def test_openai_sends_reasoning_effort(self):
        for level, effort in (("minimal", "none"), ("low", "low"), ("medium", "medium")):
            transport = CaptureTransport(OPENAI_OK)
            result = self.run_openai(transport, level=level)
            self.assertEqual({"effort": effort}, transport.bodies[0]["reasoning"])
            self.assertEqual({"requested": level, "used": level, "fellBack": False}, result.reasoning)

    def test_gemini_3_sends_thinking_level_and_counts_thoughts_as_output(self):
        for level in ("minimal", "low", "medium"):
            transport = CaptureTransport(GEMINI_OK)
            result = self.run_gemini(transport, level=level)
            config = transport.bodies[0]["generationConfig"]
            self.assertEqual({"thinkingLevel": level}, config["thinkingConfig"])
            self.assertNotIn("thinkingBudget", config["thinkingConfig"])
            self.assertEqual(12, result.usage["output_tokens"])

    def test_models_without_the_setting_get_nothing(self):
        transport = CaptureTransport(GEMINI_OK)
        result = self.run_gemini(transport, model="gemini-2.5-flash")
        self.assertNotIn("thinkingConfig", transport.bodies[0]["generationConfig"])
        self.assertEqual({"requested": "medium", "used": None, "fellBack": False}, result.reasoning)
        transport = CaptureTransport(OPENAI_OK)
        self.run_openai(transport, model="gpt-4.1-nano")
        self.assertNotIn("reasoning", transport.bodies[0])
        transport = CaptureTransport(CLAUDE_OK)
        result = ClaudeProvider(transport).translate(CREDENTIALS, TranslationRequest(text=CHUNK, target_language="UK"))
        self.assertNotIn("reasoning", transport.bodies[0])
        self.assertIsNone(result.reasoning)

    def test_a_rejected_level_falls_back_to_low_once_and_is_remembered(self):
        transport = CaptureTransport(reject("Unsupported value: 'none' is not supported with reasoning.effort for this model."), OPENAI_OK)
        with self.assertLogs(level="WARNING"):
            result = self.run_openai(transport)
        self.assertEqual([{"effort": "none"}, {"effort": "low"}], [body["reasoning"] for body in transport.bodies])
        self.assertEqual({"requested": "minimal", "used": "low", "fellBack": True}, result.reasoning)
        # the next batch of this model goes straight to "low": no request wasted on the rejected level
        again = CaptureTransport(OPENAI_OK)
        result = self.run_openai(again)
        self.assertEqual([{"effort": "low"}], [body["reasoning"] for body in again.bodies])
        self.assertTrue(result.reasoning["fellBack"])
        # another model, or another level of the same model, is tried as asked
        other = CaptureTransport(OPENAI_OK)
        self.run_openai(other, model="gpt-5.4")
        self.assertEqual({"effort": "none"}, other.bodies[0]["reasoning"])
        medium = CaptureTransport(OPENAI_OK)
        self.run_openai(medium, level="medium")
        self.assertEqual({"effort": "medium"}, medium.bodies[0]["reasoning"])

    def test_gemini_fallback_too(self):
        transport = CaptureTransport(reject("thinking_level minimal is not supported for this model"), GEMINI_OK)
        with self.assertLogs(level="WARNING"):
            result = self.run_gemini(transport, level="minimal")
        self.assertEqual(["minimal", "low"], [body["generationConfig"]["thinkingConfig"]["thinkingLevel"] for body in transport.bodies])
        self.assertTrue(result.reasoning["fellBack"])

    def test_unrelated_400_and_a_rejected_low_are_not_retried(self):
        transport = CaptureTransport(reject("Your prompt was flagged."))
        with self.assertRaises(ValueError):
            self.run_openai(transport)
        self.assertEqual(1, len(transport.bodies))
        transport = CaptureTransport(reject("unsupported reasoning effort"))
        with self.assertRaises(ValueError):
            self.run_openai(transport, level="low")
        self.assertEqual(1, len(transport.bodies))
        self.assertEqual(set(), LlmTranslationProvider._REJECTED_REASONING)

    def test_billed_tokens_of_the_retry_only(self):
        seen = []
        transport = CaptureTransport(reject("reasoning.effort none unsupported"), OPENAI_OK)
        with capture_usage(lambda model, usage: seen.append(usage)), self.assertLogs(level="WARNING"):
            self.run_openai(transport)
        self.assertEqual(1, len(seen))  # the rejected request returned no usage: nothing to bill


class ReasoningSettingsTests(Fixture):
    def configure(self, **configuration):
        self.storage.update_project(self.project_id, {"aiConfiguration": configuration})
        return self.storage.get_project(self.project_id)

    def test_default_is_low_for_gpt_and_gemini_and_none_for_claude(self):
        project = self.configure()
        self.assertEqual(("low", "low", None), tuple(TranslationService.reasoning_level(project, p) for p in ("openai", "gemini", "claude")))

    def test_project_setting_and_invalid_values(self):
        project = self.configure(translationReasoning={"openai": "minimal", "gemini": "medium"})
        self.assertEqual(("minimal", "medium"), (TranslationService.reasoning_level(project, "openai"), TranslationService.reasoning_level(project, "gemini")))
        project = self.configure(translationReasoning={"openai": "extreme"})
        self.assertEqual("low", TranslationService.reasoning_level(project, "openai"))

    def test_the_chosen_level_reaches_the_request_and_the_log(self):
        openai_connection = self.storage.create_integration_connection("openai", "GPT", self.vault.encrypt({"apiKey": "k"}))
        self.storage.update_integration_connection_status(openai_connection["connectionId"], "connected", "ok", "ok", {})
        self.configure(translationConnectionId=openai_connection["connectionId"], translationModels={"openai": "gpt-5.5"},
                       translationReasoning={"openai": "medium"})
        transport = CaptureTransport(dict(OPENAI_OK, output=[{"type": "message", "content": [{"type": "output_text", "text": "x"}]}]))

        def reply(url, headers, body, timeout):
            payload = json.loads(body)
            transport.bodies.append(payload)
            text = chunk_reply(payload["input"])
            return 200, json.dumps(dict(OPENAI_OK, output=[{"type": "message", "content": [{"type": "output_text", "text": text}]}])).encode("utf-8")

        transport.post = reply
        service = TranslationService(self.storage, self.vault, ProviderRegistry([OpenAIProvider(transport)]))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = service.translate_chapter(self.project_id, self.chapter_id, {"batchIndex": 0})
        self.assertEqual({"effort": "medium"}, transport.bodies[0]["reasoning"])
        self.assertEqual({"requested": "medium", "used": "medium", "fellBack": False}, result["reasoning"])
        self.assertIn('"reasoning": "medium"', output.getvalue())  # [OPENAI PROMPT]
        self.assertIn('"reasoning": {"requested": "medium", "used": "medium", "fellBack": false}', output.getvalue())  # [OPENAI USAGE]


# ---- batch size ----------------------------------------------------------------------------------


class BatchSettingsTests(Fixture):
    PARAGRAPHS = [f"Paragraph number {index}." for index in range(5)]

    def configure(self, **batch):
        self.storage.update_project(self.project_id, {"aiConfiguration": {
            "translationConnectionId": self.connection["connectionId"], "translationBatch": batch}})

    def test_defaults_are_as_before(self):
        self.assertEqual((1500, 8), TranslationService.batch_limits(self.storage.get_project(self.project_id)))
        self.assertEqual((1500, 8), TranslationService.batch_limits(None))

    def test_values_are_clamped_to_the_allowed_ranges(self):
        for configured, expected in (
            ({"maxChars": 100, "maxParagraphs": 0}, (500, 1)),
            ({"maxChars": 99999, "maxParagraphs": 99}, (6000, 20)),
            ({"maxChars": 2500}, (2500, 8)),
            ({"maxChars": "x", "maxParagraphs": True}, (1500, 8)),
        ):
            with self.subTest(configured=configured):
                self.configure(**configured)
                self.assertEqual(expected, TranslationService.batch_limits(self.storage.get_project(self.project_id)))

    def test_the_project_setting_changes_how_a_chapter_is_split(self):
        self.configure(maxParagraphs=2)
        result, _log = self.translate(ScriptedClaudeTransport({}))
        self.assertEqual(3, result["totalBatches"])
        self.assertEqual(2, len(result["sourceParagraphIds"]))
        self.configure(maxParagraphs=20, maxChars=500)
        result, _log = self.translate(ScriptedClaudeTransport({}))
        self.assertEqual(1, result["totalBatches"])
        self.assertEqual(5, len(result["sourceParagraphIds"]))

    def test_chars_limit_splits_long_paragraphs(self):
        batches = TranslationService._llm_batches([("a", "x" * 400), ("b", "x" * 400), ("c", "x" * 400)], 800, 8)
        self.assertEqual([["a", "b"], ["c"]], batches)
        self.assertEqual([["a", "b", "c"]], TranslationService._llm_batches([("a", "x" * 400), ("b", "x" * 400), ("c", "x" * 400)]))

    def test_validation_of_the_project_settings(self):
        def check(**configuration):
            return server.validate_project_ai_configuration({"aiConfiguration": configuration}, [])

        self.assertIsNone(check(translationBatch={"maxChars": 500, "maxParagraphs": 20}, translationReasoning={"openai": "minimal", "gemini": "medium"}))
        for batch in ({"maxChars": 499}, {"maxChars": 6001}, {"maxParagraphs": 0}, {"maxParagraphs": 21}, {"maxChars": "9"}, {"maxChars": 1.5},
                      {"maxChars": True}, {"other": 1}, "x"):
            with self.subTest(batch=batch):
                self.assertIsNotNone(check(translationBatch=batch))
        for reasoning in ({"claude": "low"}, {"openai": "high"}, {"gemini": None}, "low"):
            with self.subTest(reasoning=reasoning):
                self.assertIsNotNone(check(translationReasoning=reasoning))


if __name__ == "__main__":
    unittest.main()
