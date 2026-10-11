"""Translation queue: plan, estimate, budget, pause/resume/stop, failed chapters, restart, undo. Mock transport only."""
import json
import re
import sqlite3
import tempfile
import threading
import time
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet

from backend import server
from backend.integrations.credentials import CredentialVault
from backend.integrations.providers.claude import ClaudeProvider
from backend.integrations.registry import ProviderRegistry
from backend.queue_service import QueueError, QueueWorker, TranslationQueueService
from backend.storage import Storage
from backend.translations.service import TranslationService

USAGE = {"input_tokens": 1000, "output_tokens": 500, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}
CALL_COST = (1000 * 2 + 500 * 10) / 1_000_000  # claude-sonnet-5-5 at 2 / 10 $ per 1M


def chunk_reply(message, text="Переклад"):
    root = ET.fromstring(re.search(r"<chunk>.*</chunk>", message, re.S).group(0))
    for element in root.findall("p"):
        for child in list(element):
            element.remove(child)
        element.text = f"{text} {element.attrib['id'][-6:]}"
    return ET.tostring(root, encoding="unicode")


class QueueTransport:
    """Mock Claude HTTP. `behavior(call_number, message)` may return ("http", status) or ("truncate",)."""

    def __init__(self, behavior=None):
        self.calls = []
        self.behavior = behavior or (lambda number, message: None)

    def post(self, url, headers, body, timeout):
        payload = json.loads(body)
        message = payload["messages"][0]["content"]
        self.calls.append({"model": payload["model"], "message": message})
        action = self.behavior(len(self.calls), re.search(r"<chunk>.*</chunk>", message, re.S).group(0))
        if action and action[0] == "http":
            return action[1], json.dumps({"error": {"message": "boom"}}).encode()
        stop = "max_tokens" if action and action[0] == "truncate" else "end_turn"
        reply = {"model": payload["model"], "stop_reason": stop, "content": [{"type": "text", "text": chunk_reply(message)}], "usage": USAGE}
        return 200, json.dumps(reply, ensure_ascii=False).encode("utf-8")


class QueueFixture(unittest.TestCase):
    """Chapter 1: p0 has a translation, p1 is proofread, p2 and p3 are untranslated.
    Chapter 2: two untranslated paragraphs ("Ch2"). Chapter 3 is «Не експортувати». Chapter 4: three paragraphs.
    One paragraph per batch (translationBatch.maxParagraphs = 1), so every paragraph is a batch."""

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "workbench.sqlite3"
        self.storage = Storage(self.database_path)
        self.vault = CredentialVault(Fernet(Fernet.generate_key()))
        self.connection = self.storage.create_integration_connection("claude", "Claude", self.vault.encrypt({"apiKey": "k"}))
        self.storage.update_integration_connection_status(self.connection["connectionId"], "connected", "ok", "ok", {})
        self.project_id = self.storage.create_project({
            "title": "Queue", "status": "translation",
            "aiConfiguration": {"translationConnectionId": self.connection["connectionId"], "translationBatch": {"maxParagraphs": 1}},
        })["projectId"]
        self.storage.save_book_structure(
            self.project_id, "b.epub", "application/epub+zip", b"b",
            {"chapters": [
                {"title": "One", "elements": [{"type": "paragraph", "text": f"Ch1 paragraph {i} of the first chapter."} for i in range(4)]},
                {"title": "Two", "elements": [{"type": "paragraph", "text": f"Ch2 paragraph {i} of the second chapter."} for i in range(2)]},
                {"title": "Three", "elements": [{"type": "paragraph", "text": "Ch3 never exported."}]},
                {"title": "Four", "elements": [{"type": "paragraph", "text": f"Ch4 paragraph {i} of the last chapter."} for i in range(3)]},
            ]},
        )
        chapters = self.storage.get_book_structure(self.project_id)["chapters"]
        self.chapter_ids = [chapter["chapterId"] for chapter in chapters]
        self.ids = [[element["paragraphId"] for element in chapter["elements"]] for chapter in chapters]
        self.storage.update_paragraph(self.ids[0][0], "Готовий переклад", False)
        self.storage.update_paragraph(self.ids[0][1], "Вичитаний переклад", True)
        self.storage.set_chapter_export_flag(self.chapter_ids[2], True)
        self.storage = Storage(self.database_path)  # the existing translations become the chosen «Поточний»
        self.start()

    def start(self, transport=None):
        self.transport = transport or QueueTransport()
        self.translation = TranslationService(self.storage, self.vault, ProviderRegistry([ClaudeProvider(self.transport)]))
        self.queues = TranslationQueueService(self.storage, self.translation, retry_delay=0, sleep=lambda seconds: None)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def sql(self, statement, *params):
        with sqlite3.connect(self.database_path) as connection:
            return connection.execute(statement, params).fetchall()

    def create(self, **data):
        data = {"mode": "untranslated", **data}
        return self.queues.create(self.project_id, data)

    def run_to_end(self, queue_id, limit=100):
        for _ in range(limit):
            if self.queues.step(queue_id) in {"idle", "finished"}:
                return
        self.fail("the queue did not finish")

    def paragraph(self, paragraph_id):
        return self.storage.get_paragraph(paragraph_id)

    def engine_variants(self, paragraph_id, engine="claude"):
        return [v for v in self.paragraph(paragraph_id)["translationVariants"] if v["engine"] == engine]


class PlanTests(QueueFixture):
    def test_default_plan_skips_translated_proofread_and_not_exported(self):
        estimate = self.queues.estimate(self.project_id, {"mode": "untranslated"})
        self.assertEqual([1, 2, 4], [chapter["number"] for chapter in estimate["chapters"]])
        self.assertEqual([2, 2, 3], [chapter["paragraphs"] for chapter in estimate["chapters"]])  # chapter 1: p2, p3 only
        self.assertEqual({"chapters": 3, "paragraphs": 7, "batches": 7}, {k: estimate["totals"][k] for k in ("chapters", "paragraphs", "batches")})
        self.assertEqual(1, estimate["skipped"]["reviewedParagraphs"])
        self.assertEqual(1, estimate["skipped"]["translatedParagraphs"])
        self.assertEqual(1, estimate["skipped"]["excludedChapters"])
        self.assertEqual(("claude", "claude-sonnet-5-5", estimate["reasoning"]), (estimate["engine"], estimate["model"], estimate["reasoning"]))

    def test_including_translated_paragraphs_never_includes_proofread_ones(self):
        estimate = self.queues.estimate(self.project_id, {"mode": "untranslated", "includeTranslated": True})
        self.assertEqual([3, 2, 3], [chapter["paragraphs"] for chapter in estimate["chapters"]])  # p0 joins, p1 (proofread) does not
        self.assertEqual(0, estimate["skipped"]["translatedParagraphs"])
        self.assertEqual(1, estimate["skipped"]["reviewedParagraphs"])

    def test_a_range_counts_the_chapter_marked_not_to_export_as_skipped(self):
        estimate = self.queues.estimate(self.project_id, {"mode": "range", "fromChapter": 2, "toChapter": 4})
        self.assertEqual([2, 4], [chapter["number"] for chapter in estimate["chapters"]])
        self.assertEqual(1, estimate["skipped"]["excludedChapters"])
        one = self.queues.estimate(self.project_id, {"mode": "range", "fromChapter": 1, "toChapter": 1})
        self.assertEqual([2], [chapter["paragraphs"] for chapter in one["chapters"]])

    def test_invalid_selections_are_refused(self):
        for data in ({}, {"mode": "all"}, {"mode": "range"}, {"mode": "range", "fromChapter": 3, "toChapter": 2},
                     {"mode": "range", "fromChapter": 0, "toChapter": 2}, {"mode": "range", "fromChapter": 1, "toChapter": 9},
                     {"mode": "range", "fromChapter": True, "toChapter": 2}, {"mode": "untranslated", "includeTranslated": "yes"}):
            with self.subTest(data=data), self.assertRaises(QueueError) as raised:
                self.queues.estimate(self.project_id, data)
            self.assertEqual(400, raised.exception.http_status)

    def test_only_claude_gpt_and_gemini_are_supported_and_the_connection_must_be_ready(self):
        deepl = self.storage.create_integration_connection("deepl", "DeepL", b"x")
        self.storage.update_integration_connection_status(deepl["connectionId"], "connected", "ok", "ok", {})
        self.storage.update_project(self.project_id, {"aiConfiguration": {"translationConnectionId": deepl["connectionId"]}})
        with self.assertRaises(QueueError) as raised:
            self.queues.estimate(self.project_id, {"mode": "untranslated"})
        self.assertEqual("queue_engine_unsupported", raised.exception.code)
        self.assertIn("DeepL", str(raised.exception))
        self.storage.update_project(self.project_id, {"aiConfiguration": {}})
        with self.assertRaises(QueueError):
            self.queues.estimate(self.project_id, {"mode": "untranslated"})
        self.storage.update_integration_connection_status(self.connection["connectionId"], "error", "x", "x", {})
        self.storage.update_project(self.project_id, {"aiConfiguration": {"translationConnectionId": self.connection["connectionId"]}})
        with self.assertRaises(QueueError) as raised:
            self.queues.estimate(self.project_id, {"mode": "untranslated"})
        self.assertEqual("queue_connection_not_ready", raised.exception.code)

    def test_estimate_without_history_comes_from_tokens_and_prices(self):
        estimate = self.queues.estimate(self.project_id, {"mode": "untranslated"})["estimate"]
        self.assertEqual("tokens", estimate["method"])
        self.assertGreater(estimate["usd"], 0)
        self.assertTrue(estimate["perCharUsd"] > 0)

    def test_estimate_from_the_history_of_this_engine_and_model(self):
        # 10000 source characters cost $0.35 in earlier runs -> $0.000035 per character
        for _ in range(5):
            self.storage.record_translation_usage(self.project_id, self.chapter_ids[0], "claude", "claude-sonnet-5-5", "translate", USAGE,
                                                  source_chars=2000)
        self.storage.record_translation_usage(self.project_id, None, "openai", "gpt-5.5", "translate", USAGE, source_chars=99999)  # another engine
        estimate = self.queues.estimate(self.project_id, {"mode": "untranslated"})
        chars = estimate["totals"]["chars"]
        self.assertEqual("history", estimate["estimate"]["method"])
        self.assertAlmostEqual(5 * CALL_COST / 10000, estimate["estimate"]["perCharUsd"])
        self.assertAlmostEqual(round(chars * 5 * CALL_COST / 10000, 4), estimate["estimate"]["usd"])

    def test_old_usage_rows_without_source_chars_are_a_stand_in(self):
        self.storage.add_translation_variant(self.ids[1][0], "claude", "x" * 10)
        for index in range(4):  # a chapter whose paragraphs have Claude variants and long original text
            self.storage.record_translation_usage(self.project_id, self.chapter_ids[3], "claude", "claude-sonnet-5-5", "translate", USAGE)
        self.sql("UPDATE book_paragraphs SET original_text = ? WHERE chapter_id = ?", "y" * 5000, self.chapter_ids[3])
        for paragraph_id in self.ids[3]:
            self.storage.add_translation_variant(paragraph_id, "claude", "z")
        estimate = self.queues.estimate(self.project_id, {"mode": "untranslated"})["estimate"]
        self.assertEqual("history_legacy", estimate["method"])
        self.assertAlmostEqual(4 * CALL_COST / 15000, estimate["perCharUsd"])

    def test_an_unpriced_model_has_no_estimate(self):
        self.storage.save_model_prices([{"model": "claude-sonnet-5-5"}])
        estimate = self.queues.estimate(self.project_id, {"mode": "untranslated"})
        self.assertEqual((False, None, "none"), (estimate["priced"], estimate["estimate"]["usd"], estimate["estimate"]["method"]))


class RunTests(QueueFixture):
    def test_a_queue_translates_the_plan_batch_by_batch_and_keeps_existing_translations(self):
        queue = self.create(includeTranslated=True)
        self.assertEqual("running", queue["status"])
        self.run_to_end(queue["queueId"])
        state = self.queues.state(queue["queueId"])
        self.assertEqual("completed", state["status"])
        self.assertEqual({"done": 3, "partial": 0, "error": 0, "skipped": 0, "pending": 0, "running": 0}, state["summary"]["chapters"])
        self.assertEqual(8, state["summary"]["paragraphs"])
        self.assertEqual(8, len(self.transport.calls))  # one batch per paragraph, the XML id check is the same code as before
        # untranslated paragraphs: the new variant is chosen; the translated one: a variant is added, nothing is replaced
        for paragraph_id in (self.ids[0][2], self.ids[0][3], *self.ids[1], *self.ids[3]):
            paragraph = self.paragraph(paragraph_id)
            variant = self.engine_variants(paragraph_id)[0]
            self.assertEqual((variant["variantId"], variant["text"]), (paragraph["selectedVariantId"], paragraph["translationText"]))
        existing = self.paragraph(self.ids[0][0])
        self.assertEqual("Готовий переклад", existing["translationText"])
        self.assertEqual("current", next(v["engine"] for v in existing["translationVariants"] if v["variantId"] == existing["selectedVariantId"]))
        self.assertEqual(1, len(self.engine_variants(self.ids[0][0])))
        # proofread paragraph and the not-exported chapter: untouched, never sent
        self.assertEqual([], self.engine_variants(self.ids[0][1]))
        self.assertEqual([], self.engine_variants(self.ids[2][0]))
        self.assertFalse(any("Ch3" in re.search(r"<chunk>.*</chunk>", call["message"], re.S).group(0) for call in self.transport.calls))  # it may only appear as context
        self.assertEqual(8, state["summary"]["variantsCreated"])

    def test_every_call_is_recorded_with_the_queue_id_and_the_source_characters(self):
        queue = self.create()
        self.run_to_end(queue["queueId"])
        rows = self.storage.list_translation_usage(self.project_id)
        self.assertEqual(7, len(rows))
        self.assertTrue(all(row["queueId"] == queue["queueId"] and row["kind"] == "translate" and row["sourceChars"] > 0 for row in rows))
        state = self.queues.state(queue["queueId"])
        self.assertAlmostEqual(7 * CALL_COST, state["spentUsd"])
        self.assertEqual((False, 7), (state["costIncomplete"], state["calls"]))

    def test_the_model_chosen_at_the_start_is_kept_for_the_whole_queue(self):
        queue = self.create()
        self.queues.step(queue["queueId"])
        self.storage.update_project(self.project_id, {"aiConfiguration": {
            "translationConnectionId": self.connection["connectionId"], "translationModels": {"claude": "claude-other-model"}, "translationBatch": {"maxParagraphs": 1}}})
        self.run_to_end(queue["queueId"])
        self.assertEqual({"claude-sonnet-5-5"}, {call["model"] for call in self.transport.calls})

    def test_only_one_queue_can_be_active_in_a_project(self):
        queue = self.create()
        with self.assertRaises(QueueError) as raised:
            self.create()
        self.assertEqual((409, "queue_active"), (raised.exception.http_status, raised.exception.code))
        self.queues.stop(queue["queueId"])
        self.assertEqual("running", self.create()["status"])

    def test_nothing_to_translate_is_refused(self):
        self.storage.update_paragraph(self.ids[0][2], "x", True)
        for paragraph_id in (*self.ids[0][3:], *self.ids[1], *self.ids[3]):
            self.storage.update_paragraph(paragraph_id, "x", True)
        with self.assertRaises(QueueError) as raised:
            self.create()
        self.assertEqual("queue_empty", raised.exception.code)

    def test_unpriced_model_starts_only_without_a_limit_and_with_confirmation(self):
        self.storage.save_model_prices([{"model": "claude-sonnet-5-5"}])
        for data, code in (({}, "queue_unpriced_confirm"), ({"confirmUnpriced": False}, "queue_unpriced_confirm"),
                           ({"budgetUsd": 1.0, "confirmUnpriced": True}, "queue_unpriced")):
            with self.subTest(data=data), self.assertRaises(QueueError) as raised:
                self.create(**data)
            self.assertEqual(code, raised.exception.code)
        queue = self.create(confirmUnpriced=True)
        self.run_to_end(queue["queueId"])
        state = self.queues.state(queue["queueId"])
        self.assertEqual(("completed", True, 7, None), (state["status"], state["costIncomplete"], state["unpricedCalls"], None))

    def test_budget_values_are_validated(self):
        for budget in (0, -1, "5", True, float("inf")):
            with self.subTest(budget=budget), self.assertRaises(QueueError):
                self.create(budgetUsd=budget)


class BudgetTests(QueueFixture):
    def test_the_queue_stops_at_a_batch_boundary_when_the_next_batch_would_pass_the_limit(self):
        queue = self.create(budgetUsd=2.5 * CALL_COST)  # room for two batches, not for a third
        self.run_to_end(queue["queueId"])
        state = self.queues.state(queue["queueId"])
        self.assertEqual("budget_reached", state["status"])
        self.assertEqual(2, len(self.transport.calls))
        self.assertLessEqual(state["spentUsd"], 2.5 * CALL_COST)
        self.assertEqual([("done", 2), ("skipped", 0), ("skipped", 0)], [(i["status"], i["paragraphsDone"]) for i in state["items"]])

    def test_a_chapter_in_the_middle_is_marked_partial_and_a_second_queue_finishes_it(self):
        queue = self.create(budgetUsd=3.5 * CALL_COST)  # chapter 1 (2 batches) + the first batch of chapter 2
        self.run_to_end(queue["queueId"])
        state = self.queues.state(queue["queueId"])
        self.assertEqual("budget_reached", state["status"])
        self.assertEqual([("done", 2), ("partial", 1), ("skipped", 0)], [(i["status"], i["paragraphsDone"]) for i in state["items"]])
        self.assertEqual(3, len(self.transport.calls))
        # the saved batches stay; a new «усі без перекладу» queue takes only what is still untranslated
        later = self.create()
        self.assertEqual([1, 3], [item["paragraphsTotal"] for item in later["items"]])  # 1 left in chapter 2 + 3 in chapter 4
        self.run_to_end(later["queueId"])
        self.assertEqual(7, len(self.transport.calls))
        for paragraph_id in (self.ids[0][2], self.ids[0][3], *self.ids[1], *self.ids[3]):
            self.assertEqual(1, len(self.engine_variants(paragraph_id)))  # nothing was translated twice

    def test_a_limit_below_the_first_batch_stops_before_any_call(self):
        queue = self.create(budgetUsd=0.0001)
        self.run_to_end(queue["queueId"])
        state = self.queues.state(queue["queueId"])
        self.assertEqual(("budget_reached", 0), (state["status"], len(self.transport.calls)))
        self.assertEqual({"skipped": 3}, {k: v for k, v in state["summary"]["chapters"].items() if v})

    def test_without_a_limit_the_queue_runs_to_the_end(self):
        queue = self.create()
        self.run_to_end(queue["queueId"])
        self.assertEqual("completed", self.queues.state(queue["queueId"])["status"])


class ControlTests(QueueFixture):
    def test_pause_stops_after_the_batch_and_resume_continues(self):
        queue = self.create()
        qid = queue["queueId"]
        self.queues.step(qid)
        self.queues.step(qid)
        self.assertEqual("paused", self.queues.pause(qid)["status"])
        self.assertEqual("idle", self.queues.step(qid))
        self.assertEqual(2, len(self.transport.calls))  # nothing happens while paused
        self.assertEqual("paused", self.queues.pause(qid)["status"])  # idempotent
        self.assertEqual("running", self.queues.resume(qid)["status"])
        self.run_to_end(qid)
        self.assertEqual(("completed", 7), (self.queues.state(qid)["status"], len(self.transport.calls)))
        for action in (self.queues.pause, self.queues.resume):
            with self.assertRaises(QueueError) as raised:
                action(qid)
            self.assertEqual("queue_finished", raised.exception.code)

    def test_stop_finishes_nothing_more_and_marks_the_chapters(self):
        queue = self.create()
        qid = queue["queueId"]
        for _ in range(3):  # chapter 1 done (2 batches), the first batch of chapter 2
            self.queues.step(qid)
        self.queues.step(qid)  # one more batch happened; now stop
        state = self.queues.stop(qid)
        self.assertEqual("stopped", state["status"])
        self.assertEqual([("done", 2), ("done", 2), ("skipped", 0)], [(i["status"], i["paragraphsDone"]) for i in state["items"]])
        calls = len(self.transport.calls)
        self.assertEqual("idle", self.queues.step(qid))
        self.assertEqual(calls, len(self.transport.calls))
        self.assertEqual("stopped", self.queues.stop(qid)["status"])  # idempotent

    def test_a_paused_queue_can_be_stopped(self):
        queue = self.create()
        self.queues.step(queue["queueId"])
        self.queues.pause(queue["queueId"])
        state = self.queues.stop(queue["queueId"])
        self.assertEqual(("stopped", ["partial", "skipped", "skipped"]), (state["status"], [i["status"] for i in state["items"]]))

    def test_unknown_queue(self):
        for action in (self.queues.pause, self.queues.resume, self.queues.stop, self.queues.state):
            with self.assertRaises(QueueError) as raised:
                action("nope")
            self.assertEqual(404, raised.exception.http_status)


class FailureTests(QueueFixture):
    @staticmethod
    def fail_chapter_two(number, message):
        return ("http", 500) if "Ch2" in message else None

    def test_a_failed_chapter_is_marked_after_one_retry_and_the_queue_goes_on(self):
        self.start(QueueTransport(self.fail_chapter_two))
        queue = self.create()
        self.run_to_end(queue["queueId"])
        state = self.queues.state(queue["queueId"])
        self.assertEqual("completed", state["status"])
        self.assertEqual(["done", "error", "done"], [i["status"] for i in state["items"]])
        self.assertEqual(2, sum(1 for call in self.transport.calls if "Ch2" in call["message"].split("<chunk>")[1]))  # the batch and exactly one retry
        self.assertEqual(1, len(state["errors"]))
        error = state["errors"][0]
        self.assertEqual((2, "Two", 0, 2), (error["chapterNumber"], error["title"], error["paragraphsDone"], error["paragraphsTotal"]))
        self.assertIn("HTTP 500", error["error"])
        self.assertEqual([], self.engine_variants(self.ids[1][0]))
        self.assertEqual(1, len(self.engine_variants(self.ids[3][2])))  # chapter 4 was still translated
        self.assertEqual(1, state["summary"]["chapters"]["error"])

    def test_the_retry_can_succeed(self):
        self.start(QueueTransport(lambda number, message: ("http", 503) if number == 3 else None))
        queue = self.create()
        self.run_to_end(queue["queueId"])
        state = self.queues.state(queue["queueId"])
        self.assertEqual(("completed", ["done", "done", "done"]), (state["status"], [i["status"] for i in state["items"]]))
        self.assertEqual(8, len(self.transport.calls))  # 7 batches + the repeated one
        self.assertEqual([], state["errors"])

    def test_a_chapter_failing_after_some_batches_keeps_them(self):
        self.start(QueueTransport(lambda number, message: ("http", 500) if "Ch4 paragraph 1" in message else None))
        queue = self.create()
        self.run_to_end(queue["queueId"])
        state = self.queues.state(queue["queueId"])
        self.assertEqual("error", state["items"][2]["status"])
        self.assertEqual(1, state["items"][2]["paragraphsDone"])
        self.assertIn("перекладено 1 з 3 абзаців", state["errors"][0]["error"])
        self.assertEqual(1, len(self.engine_variants(self.ids[3][0])))
        self.assertEqual([], self.engine_variants(self.ids[3][1]))

    def test_a_truncated_answer_is_billed_and_recorded_even_though_the_batch_fails(self):
        self.start(QueueTransport(lambda number, message: ("truncate",) if "Ch2 paragraph 0" in message else None))
        queue = self.create()
        self.run_to_end(queue["queueId"])
        rows = [row for row in self.storage.list_translation_usage(self.project_id) if row["queueId"] == queue["queueId"]]
        self.assertEqual(2 + 2 + 3, len(rows))  # chapter 1, chapter 2's first batch twice (both billed), chapter 4
        self.assertEqual("error", self.queues.state(queue["queueId"])["items"][1]["status"])

    def test_a_pause_during_the_retry_wait_repeats_the_batch_on_resume(self):
        calls = {"waits": 0}
        queues = self.queues

        def sleep(seconds):
            calls["waits"] += 1
            queues.pause(queue["queueId"])

        self.start(QueueTransport(lambda number, message: ("http", 500) if number == 1 else None))
        self.queues._sleep = sleep
        queue = self.create()
        self.assertEqual("idle", self.queues.step(queue["queueId"]))
        self.assertEqual((1, "paused"), (calls["waits"], self.queues.state(queue["queueId"])["status"]))
        self.queues.resume(queue["queueId"])
        self.run_to_end(queue["queueId"])
        self.assertEqual("completed", self.queues.state(queue["queueId"])["status"])
        self.assertEqual(0, self.queues.state(queue["queueId"])["summary"]["chapters"]["error"])


class RestartTests(QueueFixture):
    def test_after_a_restart_the_queue_goes_on_from_where_it_stopped(self):
        queue = self.create(includeTranslated=True)
        qid = queue["queueId"]
        for _ in range(4):
            self.queues.step(qid)
        first_calls = len(self.transport.calls)
        self.start()  # a new process: new service, new transport, same database
        self.assertEqual([qid], self.queues.running_queue_ids())
        self.run_to_end(qid)
        self.assertEqual("completed", self.queues.state(qid)["status"])
        self.assertEqual(8, first_calls + len(self.transport.calls))  # every batch exactly once
        for paragraph_id in (self.ids[0][0], self.ids[0][2], self.ids[0][3], *self.ids[1], *self.ids[3]):
            self.assertEqual(1, len(self.engine_variants(paragraph_id)))

    def test_a_paused_queue_stays_paused_after_a_restart(self):
        queue = self.create()
        self.queues.step(queue["queueId"])
        self.queues.pause(queue["queueId"])
        self.start()
        self.assertEqual([], self.queues.running_queue_ids())
        self.assertEqual("paused", self.queues.state(queue["queueId"])["status"])

    def test_a_batch_is_saved_atomically(self):
        queue = self.create()
        item = self.storage.get_translation_queue(queue["queueId"])["items"][0]
        entries = [{"paragraphId": self.ids[0][2], "text": "A"}, {"paragraphId": self.ids[0][3], "text": "B"}]
        original = Storage._add_variant_in
        calls = []

        def fail_second(self_, connection, *args):
            calls.append(1)
            if len(calls) == 2:
                raise RuntimeError("boom")
            return original(self_, connection, *args)

        with patch.object(Storage, "_add_variant_in", fail_second), self.assertRaises(RuntimeError):
            self.storage.save_queue_batch(queue["queueId"], item["itemId"], "claude", entries)
        self.assertEqual([], self.engine_variants(self.ids[0][2]))
        self.assertEqual((0, 0), tuple(self.storage.get_translation_queue(queue["queueId"])["items"][0][k] for k in ("batchesDone", "paragraphsDone")))
        self.assertEqual(0, self.storage.queue_variant_count(queue["queueId"]))

    def test_the_migration_is_idempotent_and_upgrades_old_usage_rows(self):
        self.storage.record_translation_usage(self.project_id, None, "claude", "claude-sonnet-5-5", "chat", USAGE)
        with sqlite3.connect(self.database_path) as connection:
            connection.executescript("""
                DROP INDEX IF EXISTS idx_translation_usage_queue;
                ALTER TABLE translation_usage DROP COLUMN queue_id;
                ALTER TABLE translation_usage DROP COLUMN source_chars;
            """)
        for _ in range(3):
            self.storage = Storage(self.database_path)
        columns = {row[1] for row in self.sql("PRAGMA table_info(translation_usage)")}
        self.assertTrue({"queue_id", "source_chars"} <= columns)
        rows = self.storage.list_translation_usage(self.project_id)
        self.assertEqual((1, None, None), (len(rows), rows[0]["queueId"], rows[0]["sourceChars"]))
        self.assertEqual(3, len({row[0] for row in self.sql("SELECT name FROM sqlite_master WHERE name LIKE 'translation_queue%' OR name = 'translation_queues'")}))


class UndoTests(QueueFixture):
    def finished_queue(self):
        queue = self.create(includeTranslated=True)
        self.run_to_end(queue["queueId"])
        return queue["queueId"]

    def test_undo_removes_the_variants_of_the_queue_and_the_choices_it_made_on_its_own(self):
        qid = self.finished_queue()
        dry = self.queues.undo(qid, dry_run=True)
        self.assertEqual((True, 8, 7, 0), (dry["dryRun"], dry["removedVariants"], dry["revertedSelections"], dry["keptChosen"]))
        self.assertEqual(1, len(self.engine_variants(self.ids[1][0])))  # a dry run changes nothing
        result = self.queues.undo(qid)
        self.assertEqual((8, 7, 0), (result["removedVariants"], result["revertedSelections"], result["keptChosen"]))
        for paragraph_id in (self.ids[0][2], self.ids[0][3], *self.ids[1], *self.ids[3]):
            paragraph = self.paragraph(paragraph_id)
            self.assertEqual((None, None, False, []), (paragraph["translationText"], paragraph["selectedVariantId"], paragraph["reviewed"], paragraph["translationVariants"]))
        existing = self.paragraph(self.ids[0][0])  # translated before the queue: its translation and «Поточний» are untouched
        self.assertEqual("Готовий переклад", existing["translationText"])
        self.assertEqual(["current"], [v["engine"] for v in existing["translationVariants"]])
        self.assertEqual("Вичитаний переклад", self.paragraph(self.ids[0][1])["translationText"])
        self.assertEqual(7, len(self.storage.list_translation_usage(self.project_id)) - 1)  # the money spent stays in the records
        self.assertIsNotNone(self.queues.state(qid)["undoneAt"])
        again = self.queues.undo(qid)
        self.assertEqual((0, 0), (again["removedVariants"], again["revertedSelections"]))

    def test_what_the_user_did_since_is_not_undone(self):
        qid = self.finished_queue()
        chosen_by_hand, edited, proofread = self.ids[1][0], self.ids[1][1], self.ids[3][0]
        untouched = self.ids[3][1]
        # 1. the user chose another queue variant of a paragraph by hand: a second version, then «У файл»
        self.storage.add_translation_variant(chosen_by_hand, "claude", "Новіша версія")
        newest = self.engine_variants(chosen_by_hand)[-1]
        self.storage.select_translation_variant(chosen_by_hand, newest["variantId"])
        # 2. an edit of the chosen text (a «Вручну» variant becomes the chosen one)
        self.storage.save_paragraph_edit(edited, "Моя правка", False)
        # 3. the paragraph was proofread
        self.storage.update_paragraph(proofread, self.paragraph(proofread)["translationText"], True)
        result = self.queues.undo(qid)
        self.assertEqual(1, result["keptChosen"])  # only the proofread paragraph; the other two no longer have a queue variant chosen
        self.assertEqual("Новіша версія", self.paragraph(chosen_by_hand)["translationText"])  # chosen by hand: kept
        self.assertEqual("Моя правка", self.paragraph(edited)["translationText"])  # the edit survives
        self.assertEqual(["manual"], [v["engine"] for v in self.paragraph(edited)["translationVariants"]])  # the queue's variant is gone
        self.assertEqual(True, self.paragraph(proofread)["reviewed"])  # proofread: left chosen
        self.assertIsNone(self.paragraph(untouched)["translationText"])  # untouched: taken back

    def test_a_running_queue_cannot_be_undone(self):
        queue = self.create()
        self.queues.step(queue["queueId"])
        for dry in (False, True):
            with self.assertRaises(QueueError) as raised:
                self.queues.undo(queue["queueId"], dry_run=dry)
            self.assertEqual("queue_running", raised.exception.code)
        self.queues.pause(queue["queueId"])
        with self.assertRaises(QueueError):
            self.queues.undo(queue["queueId"])
        self.queues.stop(queue["queueId"])
        self.assertEqual(1, self.queues.undo(queue["queueId"])["removedVariants"])

    def test_another_queues_variants_are_not_touched(self):
        first = self.create(budgetUsd=1.5 * CALL_COST)
        self.run_to_end(first["queueId"])  # one batch only
        second = self.create()
        self.run_to_end(second["queueId"])
        self.queues.undo(first["queueId"])
        self.assertEqual([], self.engine_variants(self.ids[0][2]))  # the first queue's only variant is gone
        remaining = sum(len(self.engine_variants(paragraph_id)) for paragraph_id in (self.ids[0][3], *self.ids[1], *self.ids[3]))
        self.assertEqual(6, remaining)  # the second queue's variants are all still there


class FakeHandler:
    def __init__(self, payload=None):
        self.payload = payload

    def read_json(self):
        return self.payload


class ApiAndWorkerTests(QueueFixture):
    def api(self, method, path, payload=None):
        with patch.object(server, "storage", self.storage), patch.object(server, "translation_queue_service", self.queues):
            return server.WorkbenchHandler.handle_api(FakeHandler(payload if payload is not None else {}), method, path)

    def test_routes_cover_estimate_create_control_and_undo(self):
        base = f"/api/projects/{self.project_id}/translation-queues"
        status, estimate = self.api("POST", base + "/estimate", {"mode": "untranslated"})
        self.assertEqual((200, 7), (status, estimate["totals"]["paragraphs"]))
        self.assertEqual((200, None), (self.api("GET", base + "/latest")[0], self.api("GET", base + "/latest")[1]["queue"]))
        status, queue = self.api("POST", base, {"mode": "untranslated"})
        self.assertEqual((201, "running"), (status, queue["status"]))
        qid = queue["queueId"]
        self.assertEqual(qid, self.api("GET", base + "/latest")[1]["queue"]["queueId"])
        self.assertEqual("paused", self.api("POST", f"/api/translation-queues/{qid}/pause")[1]["status"])
        self.assertEqual("running", self.api("POST", f"/api/translation-queues/{qid}/resume")[1]["status"])
        self.assertEqual("stopped", self.api("POST", f"/api/translation-queues/{qid}/stop")[1]["status"])
        self.assertEqual(200, self.api("GET", f"/api/translation-queues/{qid}")[0])
        status, dry = self.api("POST", f"/api/translation-queues/{qid}/undo", {"dryRun": True})
        self.assertEqual((200, True), (status, dry["dryRun"]))
        with self.assertRaises(QueueError):
            self.api("POST", base, {"mode": "bad"})

    def test_the_worker_thread_runs_the_queue_to_the_end(self):
        worker = QueueWorker(self.queues, idle_seconds=0.05)
        worker.start()
        try:
            queue = self.create()
            deadline = time.time() + 10
            while time.time() < deadline and self.queues.state(queue["queueId"])["status"] == "running":
                time.sleep(0.05)
        finally:
            worker.halt()
            worker.join(5)
        self.assertEqual(("completed", 7), (self.queues.state(queue["queueId"])["status"], len(self.transport.calls)))
