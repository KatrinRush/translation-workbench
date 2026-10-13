"""Translation queue: translate several chapters in the background, within a budget.

The queue is a job kept in the database (translation_queues / translation_queue_items), executed
by one worker thread of the server, one batch at a time, so it survives closing the tab, a sleeping
tablet, a server restart and a deploy: after a restart the worker simply continues the queues that
were running. The plan of each chapter is a fixed list of paragraph ids taken when the queue is
created, so batch k of a chapter is always the same batch, and a batch is saved together with the
chapter's counters in one transaction.

Each batch is the same request as a batch of a single-chapter translation (same prompt, the XML id
check, the 90 s timeout, glossary retry) and every call goes to translation_usage with the queue's id.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import math
import threading
import time
from typing import Any, Callable

from .translations.service import TranslationService, TranslationServiceError
from .usage import find_price, has_any_price, row_cost, summarize

QUEUE_ENGINES = ("claude", "openai", "gemini")
WARN_ESTIMATE_USD = 5.0
HISTORY_MIN_CHARS = 3000
# Estimate without history: source text is mostly English (~3.5 characters per token), Ukrainian
# output takes ~1.4x the tokens of the source; GPT/Gemini think before they answer.
CHARS_PER_TOKEN = 3.5
SYSTEM_CHARS_PER_TOKEN = 3.0
OUTPUT_TOKEN_RATIO = 1.4
CONTEXT_PARAGRAPHS = 6  # 3 source + 3 translated paragraphs go along with every batch
THINKING_TOKENS_PER_BATCH = {"minimal": 0, "low": 400, "medium": 1200}
ERROR_TEXT_LIMIT = 500


class QueueError(Exception):
    def __init__(self, message: str, http_status: int = 400, code: str = "queue_error"):
        super().__init__(message)
        self.http_status = http_status
        self.code = code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    moment = datetime.fromisoformat(value)
    return moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment


class TranslationQueueService:
    def __init__(
        self, storage: Any, translation_service: TranslationService, retry_delay: float = 5.0,
        sleep: Callable[[float], None] | None = None,
    ):
        self._storage = storage
        self._translation = translation_service
        self._retry_delay = retry_delay
        self._sleep = sleep or time.sleep
        self.on_change: Callable[[], None] = lambda: None  # the worker is woken when a queue becomes runnable

    # ------------------------------------------------------------------ planning and estimate

    @staticmethod
    def _selection(data: Any, chapter_count: int) -> dict[str, Any]:
        data = data if isinstance(data, dict) else {}
        mode = data.get("mode")
        if mode not in {"range", "untranslated"}:
            raise QueueError("Оберіть діапазон розділів або «усі без перекладу».", 400, "queue_invalid")
        include = data.get("includeTranslated", False)
        if not isinstance(include, bool):
            raise QueueError("includeTranslated має бути true або false.", 400, "queue_invalid")
        selection: dict[str, Any] = {"mode": mode, "includeTranslated": include}
        if mode == "range":
            for key in ("fromChapter", "toChapter"):
                value = data.get(key)
                if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= max(chapter_count, 1):
                    raise QueueError("Вкажіть розділи діапазону числами в межах книги.", 400, "queue_invalid")
                selection[key] = value
            if selection["fromChapter"] > selection["toChapter"]:
                raise QueueError("Початок діапазону має бути не пізніше за кінець.", 400, "queue_invalid")
        return selection

    def plan(self, project: dict[str, Any], selection: dict[str, Any]) -> dict[str, Any]:
        """Which paragraphs of which chapters the queue would translate. Skipped always: chapters marked
        «Не експортувати», reviewed or proofread paragraphs and empty ones; paragraphs that already have a translation
        unless includeTranslated."""
        structure = self._storage.get_book_structure(project["projectId"])
        if structure is None:
            raise QueueError("У проєкті ще немає завантаженої книги.", 409, "queue_no_book")
        max_chars, max_paragraphs = TranslationService.batch_limits(project)
        skipped = {"excludedChapters": 0, "reviewedParagraphs": 0, "translatedParagraphs": 0, "emptyChapters": 0}
        chapters = []
        for number, chapter in enumerate(structure.get("chapters", []), 1):
            if selection["mode"] == "range" and not selection["fromChapter"] <= number <= selection["toChapter"]:
                continue
            paragraphs = [item for item in chapter.get("elements", []) if item.get("type") == "paragraph" and item.get("paragraphId")]
            if chapter.get("excludeFromExport"):
                skipped["excludedChapters"] += 1
                continue
            reviewed = [item for item in paragraphs if item.get("reviewed") or item.get("proofread")]
            open_paragraphs = [item for item in paragraphs if not (item.get("reviewed") or item.get("proofread")) and (item.get("originalText") or "").strip()]
            untranslated = [item for item in open_paragraphs if not (item.get("translationText") or "").strip()]
            if selection["mode"] == "untranslated" and not untranslated:
                continue
            chosen = open_paragraphs if selection["includeTranslated"] else untranslated
            skipped["reviewedParagraphs"] += len(reviewed)
            skipped["translatedParagraphs"] += 0 if selection["includeTranslated"] else len(open_paragraphs) - len(untranslated)
            if not chosen:
                skipped["emptyChapters"] += 1
                continue
            texts = [(item["paragraphId"], item["originalText"] or "") for item in chosen]
            chapters.append({
                "chapterId": chapter["chapterId"], "chapterIndex": number, "title": chapter.get("title"),
                "plan": [paragraph_id for paragraph_id, _text in texts],
                "chars": sum(len(text) for _id, text in texts),
                "batchesTotal": len(TranslationService._llm_batches(texts, max_chars, max_paragraphs)),
            })
        return {"chapters": chapters, "skipped": skipped, "batchMaxChars": max_chars, "batchMaxParagraphs": max_paragraphs}

    def _engine(self, project: dict[str, Any]) -> dict[str, Any]:
        """The project's current translation choice: connection, engine, model and reasoning level."""
        connection_id = (project.get("aiConfiguration") or {}).get("translationConnectionId")
        connection = self._storage.get_integration_connection(connection_id) if connection_id else None
        if connection is None or connection["providerId"] not in QUEUE_ENGINES:
            raise QueueError(
                "Черга працює лише з Claude, GPT і Gemini. Для DeepL її немає: DeepL рахується в символах і квоті, "
                "а межа в $ не має сенсу. Переклад розділу DeepL — кнопкою «Перекласти розділ».", 409, "queue_engine_unsupported")
        if not connection["enabled"] or connection["testStatus"] != "connected":
            raise QueueError("Підключення для перекладу має бути активним і перевіреним (Connections).", 409, "queue_connection_not_ready")
        provider_id = connection["providerId"]
        provider = self._translation._registry.get(provider_id)
        requested = self._translation._translation_model_for(project, provider_id)
        model = provider.translation_model(requested) if provider is not None else requested
        return {
            "connectionId": connection["connectionId"], "engine": provider_id, "model": model,
            "reasoning": TranslationService.reasoning_level(project, provider_id),
        }

    def _history_cost_per_char(self, engine: str, model: str, prices: dict[str, Any]) -> tuple[float | None, str | None]:
        """Average cost of one source character for this engine and model, from translation_usage."""
        price = find_price(model, prices)
        if not has_any_price(price):
            return None, None
        rows = [row for row in self._storage.list_translation_usage_all()
                if row["engine"] == engine and row["kind"] in {"translate", "retry"} and find_price(row["model"], prices) is price]
        exact_cost = exact_chars = 0.0
        legacy: dict[str, float] = {}
        for row in rows:
            cost, _estimated = row_cost(row, price)
            if cost is None:
                continue
            if row.get("sourceChars"):
                exact_cost += cost
                exact_chars += row["sourceChars"]
            elif row.get("chapterId"):
                legacy[row["chapterId"]] = legacy.get(row["chapterId"], 0.0) + cost
        if exact_chars >= HISTORY_MIN_CHARS:
            return exact_cost / exact_chars, "history"
        legacy_chars = sum(self._storage.chapter_variant_chars(chapter_id, engine) for chapter_id in legacy)
        legacy_cost = sum(legacy.values())
        if legacy_chars >= HISTORY_MIN_CHARS and legacy_cost > 0:
            return legacy_cost / legacy_chars, "history_legacy"
        return None, None

    def _token_estimate(self, project: dict[str, Any], plan: dict[str, Any], engine: dict[str, Any], price: dict[str, Any]) -> float:
        chars = sum(chapter["chars"] for chapter in plan["chapters"])
        batches = sum(chapter["batchesTotal"] for chapter in plan["chapters"])
        paragraphs = sum(len(chapter["plan"]) for chapter in plan["chapters"])
        system_chars = len(self._translation._llm_system_prompt(project, engine.get("engine"))[0] or "")
        average = chars / paragraphs if paragraphs else 0
        input_tokens = batches * (system_chars / SYSTEM_CHARS_PER_TOKEN + CONTEXT_PARAGRAPHS * average / CHARS_PER_TOKEN) + chars / CHARS_PER_TOKEN
        output_tokens = chars / CHARS_PER_TOKEN * OUTPUT_TOKEN_RATIO + batches * THINKING_TOKENS_PER_BATCH.get(engine["reasoning"] or "", 0)
        return (input_tokens * (price["inputPerMTok"] or 0) + output_tokens * (price["outputPerMTok"] or 0)) / 1_000_000

    def estimate(self, project_id: str, data: Any) -> dict[str, Any]:
        """The numbers shown before the start: chapters, paragraphs, characters, batches and ≈$."""
        result = self._estimate_with_plan(project_id, data)
        result.pop("_plan")
        return result

    def _estimate_with_plan(self, project_id: str, data: Any) -> dict[str, Any]:
        project = self._storage.get_project(project_id)
        if project is None:
            raise QueueError("Проєкт не знайдено.", 404, "not_found")
        engine = self._engine(project)
        structure = self._storage.get_book_structure(project_id) or {}
        selection = self._selection(data, len(structure.get("chapters", [])))
        plan = self.plan(project, selection)
        prices = self._storage.list_model_prices()
        price = find_price(engine["model"], prices)
        priced = bool(price) and price.get("inputPerMTok") is not None and price.get("outputPerMTok") is not None
        chars = sum(chapter["chars"] for chapter in plan["chapters"])
        usd = per_char = method = None
        if priced and plan["chapters"]:
            per_char, method = self._history_cost_per_char(engine["engine"], engine["model"], prices)
            if per_char is not None:
                usd = per_char * chars
            else:
                usd, method = self._token_estimate(project, plan, engine, price), "tokens"
                per_char = usd / chars if chars else None
        return {
            **engine, "priced": priced, "selection": selection,
            "chapters": [{"chapterId": c["chapterId"], "number": c["chapterIndex"], "title": c["title"], "paragraphs": len(c["plan"]),
                          "chars": c["chars"], "batches": c["batchesTotal"]} for c in plan["chapters"]],
            "totals": {"chapters": len(plan["chapters"]), "paragraphs": sum(len(c["plan"]) for c in plan["chapters"]), "chars": chars,
                       "batches": sum(c["batchesTotal"] for c in plan["chapters"])},
            "skipped": plan["skipped"],
            "estimate": {"usd": None if usd is None else round(usd, 4), "method": method or "none",
                         "perCharUsd": per_char, "warnOver": WARN_ESTIMATE_USD},
            "_plan": plan,
        }

    # ------------------------------------------------------------------ create and control

    def create(self, project_id: str, data: Any) -> dict[str, Any]:
        data = data if isinstance(data, dict) else {}
        estimate = self._estimate_with_plan(project_id, data)
        plan = estimate.pop("_plan")
        if not plan["chapters"]:
            raise QueueError("За цими умовами нема що перекладати.", 409, "queue_empty")
        budget = data.get("budgetUsd")
        if budget is not None and (isinstance(budget, bool) or not isinstance(budget, (int, float)) or not math.isfinite(budget) or budget <= 0):
            raise QueueError("Максимум $ має бути додатним числом або порожнім (без межі).", 400, "queue_invalid")
        if not estimate["priced"]:
            if budget is not None:
                raise QueueError("Для цієї моделі не задано ціну, тому межу в $ перевірити неможливо. Задайте ціну в ⚙ або запустіть без межі.", 409, "queue_unpriced")
            if data.get("confirmUnpriced") is not True:
                raise QueueError("Модель без ціни: запуск можливий лише без межі й з підтвердженням.", 409, "queue_unpriced_confirm")
        options = {**estimate["selection"], "batchMaxChars": plan["batchMaxChars"], "batchMaxParagraphs": plan["batchMaxParagraphs"],
                   "costPerChar": estimate["estimate"]["perCharUsd"], "estimateMethod": estimate["estimate"]["method"]}
        try:
            queue = self._storage.create_translation_queue(
                project_id, estimate["engine"], estimate["connectionId"], estimate["model"], estimate["reasoning"], options,
                float(budget) if budget is not None else None, estimate["estimate"]["usd"], plan["chapters"],
            )
        except ValueError as error:
            raise QueueError(str(error), 409, "queue_active") from error
        self.on_change()
        return self.state(queue["queueId"])

    def _queue_or_404(self, queue_id: str) -> dict[str, Any]:
        queue = self._storage.get_translation_queue(queue_id)
        if queue is None:
            raise QueueError("Чергу не знайдено.", 404, "not_found")
        return queue

    def pause(self, queue_id: str) -> dict[str, Any]:
        queue = self._queue_or_404(queue_id)
        if queue["status"] == "running":
            self._storage.transition_queue(queue_id, ("running",), "paused")
        elif queue["status"] != "paused":
            raise QueueError("Чергу вже завершено.", 409, "queue_finished")
        return self.state(queue_id)

    def resume(self, queue_id: str) -> dict[str, Any]:
        queue = self._queue_or_404(queue_id)
        if queue["status"] == "paused":
            self._storage.transition_queue(queue_id, ("paused",), "running")
            self.on_change()
        elif queue["status"] != "running":
            raise QueueError("Чергу вже завершено.", 409, "queue_finished")
        return self.state(queue_id)

    def stop(self, queue_id: str) -> dict[str, Any]:
        """Stops at the batch boundary: a batch in flight is finished and saved, nothing more is started."""
        queue = self._queue_or_404(queue_id)
        if queue["status"] in self._storage.QUEUE_ACTIVE_STATUSES:
            if self._storage.transition_queue(queue_id, self._storage.QUEUE_ACTIVE_STATUSES, "stopped", finished=True):
                self._storage.skip_pending_queue_items(queue_id, running_to="partial")
        return self.state(queue_id)

    def undo(self, queue_id: str, dry_run: bool = False) -> dict[str, Any]:
        queue = self._queue_or_404(queue_id)
        if queue["status"] in self._storage.QUEUE_ACTIVE_STATUSES:
            raise QueueError("Спершу зупиніть чергу.", 409, "queue_running")
        return {"dryRun": dry_run, **(self._storage.undo_queue_results(queue_id, dry_run) or {}), "queue": self.state(queue_id)}

    def running_queue_ids(self) -> list[str]:
        return self._storage.running_queue_ids()

    # ------------------------------------------------------------------ the worker's step

    def _item_batches(self, queue: dict[str, Any], item: dict[str, Any]) -> list[list[str]]:
        texts = self._storage.paragraph_original_texts(item["plan"])
        ordered = [(paragraph_id, texts[paragraph_id]) for paragraph_id in item["plan"] if paragraph_id in texts]
        options = queue["options"]
        return TranslationService._llm_batches(ordered, options.get("batchMaxChars"), options.get("batchMaxParagraphs"))

    def _spent(self, queue_id: str) -> tuple[float, int]:
        """(cost so far at the current prices, source characters translated so far)"""
        rows = self._storage.list_queue_usage(queue_id)
        total = summarize(rows, self._storage.list_model_prices())
        chars = sum(row.get("sourceChars") or 0 for row in rows if row["kind"] == "translate")
        return float(total["costUsd"] or 0.0), chars

    def _fail_item(self, item: dict[str, Any], error: Exception) -> None:
        message = str(error).strip() or error.__class__.__name__
        if item["paragraphsDone"]:
            message = f"перекладено {item['paragraphsDone']} з {item['paragraphsTotal']} абзаців; {message}"
        self._storage.update_queue_item(item["itemId"], status="error", error=message[:ERROR_TEXT_LIMIT], finished_at=_now().isoformat())

    def _still_running(self, queue_id: str) -> bool:
        queue = self._storage.get_translation_queue(queue_id)
        return bool(queue and queue["status"] == "running")

    def step(self, queue_id: str) -> str:
        """One batch of the queue. Returns "idle" (not running / nothing done), "progress" or "finished"."""
        queue = self._storage.get_translation_queue(queue_id, with_plans=True)
        if queue is None or queue["status"] != "running":
            return "idle"
        item = next((i for i in queue["items"] if i["status"] == "running"), None) or next((i for i in queue["items"] if i["status"] == "pending"), None)
        if item is None:
            self._storage.set_queue_status(queue_id, "completed", finished=True)
            return "finished"
        if item["status"] == "pending":
            self._storage.update_queue_item(item["itemId"], status="running", started_at=_now().isoformat())
        batches = self._item_batches(queue, item)
        if not batches:
            self._fail_item(item, QueueError("Абзаци цього розділу більше не існують."))
            return "progress"
        if item["batchesDone"] >= len(batches):
            self._storage.update_queue_item(item["itemId"], status="done", finished_at=_now().isoformat())
            return "progress"
        batch_ids = batches[item["batchesDone"]]
        budget = queue["budgetUsd"]
        if budget is not None:
            spent, done_chars = self._spent(queue_id)
            per_char = spent / done_chars if done_chars and spent > 0 else (queue["options"].get("costPerChar") or 0.0)
            batch_chars = sum(len(text) for text in self._storage.paragraph_original_texts(batch_ids).values())
            if spent >= budget or spent + per_char * batch_chars > budget:
                # stop before a batch that would go over the limit; what was saved stays, the chapter is "partial"
                self._storage.set_queue_status(queue_id, "budget_reached", finished=True)
                self._storage.skip_pending_queue_items(queue_id, running_to="partial" if item["batchesDone"] else "skipped")
                return "finished"
        entries = None
        last_error: Exception | None = None
        for attempt in (1, 2):
            try:
                entries = self._translation.translate_queue_batch(
                    queue["projectId"], item["chapterId"], batch_ids, queue["connectionId"], queue_id, queue["model"], queue["reasoning"]
                )["entries"]
                break
            except Exception as error:  # a failed batch: one more try, then the chapter is marked and the queue goes on
                last_error = error
                logging.warning("Queue %s chapter %s batch %s attempt %s failed: %s", queue_id, item["chapterId"], item["batchesDone"] + 1, attempt, error)
                if attempt == 1:
                    self._sleep(self._retry_delay)
                    if not self._still_running(queue_id):
                        return "idle"  # paused or stopped while waiting: the batch is repeated on resume
        if entries is None:
            self._fail_item(item, last_error or RuntimeError("Помилка перекладу"))
            return "progress"
        self._storage.save_queue_batch(queue_id, item["itemId"], queue["engine"], entries)
        return "progress"

    # ------------------------------------------------------------------ state for the UI

    def state(self, queue_id: str) -> dict[str, Any]:
        queue = self._queue_or_404(queue_id)
        rows = self._storage.list_queue_usage(queue_id)
        cost = summarize(rows, self._storage.list_model_prices())
        active = queue["status"] in self._storage.QUEUE_ACTIVE_STATUSES
        items = []
        for item in queue["items"]:
            shown = dict(item)
            if shown["status"] == "partial" and not shown["paragraphsDone"]:
                shown["status"] = "skipped"
            if shown["status"] == "running" and not active:
                shown["status"] = "partial" if shown["paragraphsDone"] else "skipped"
            items.append(shown)
        current = next((i for i in items if i["status"] == "running"), None) or next((i for i in items if i["status"] == "pending"), None)
        started, finished = _parse(queue["startedAt"]), _parse(queue["finishedAt"])
        seconds = max(0.0, ((finished or _now()) - started).total_seconds()) if started else 0.0
        counts = {status: sum(1 for i in items if i["status"] == status) for status in ("done", "partial", "error", "skipped", "pending", "running")}
        total_batches = sum(i["batchesTotal"] for i in items if i["status"] != "skipped")
        return {
            **{key: queue[key] for key in ("queueId", "projectId", "engine", "connectionId", "model", "reasoning", "status", "budgetUsd",
                                           "estimateUsd", "error", "createdAt", "startedAt", "finishedAt", "undoneAt")},
            "options": queue["options"],
            "active": active,
            "spentUsd": round(float(cost["costUsd"] or 0.0), 6), "costIncomplete": bool(cost["unpriced"]), "costEstimated": bool(cost["estimated"]),
            "unpricedCalls": cost["unpricedCalls"], "calls": cost["calls"], "tokens": cost["tokens"],
            "progress": {
                "chapterPosition": (current["position"] if current else len(items)), "chaptersTotal": len(items),
                "chapterNumber": current["chapterIndex"] if current else None, "chapterTitle": current["title"] if current else None,
                "batch": (min(current["batchesDone"] + 1, current["batchesTotal"]) if current else None),
                "batchesTotal": current["batchesTotal"] if current else None,
                "batchesDone": sum(i["batchesDone"] for i in items), "batchesAll": total_batches,
            },
            "summary": {
                "chapters": counts, "paragraphs": sum(i["paragraphsDone"] for i in items),
                "variantsCreated": self._storage.queue_variant_count(queue_id), "seconds": round(seconds, 1),
                "costUsd": round(float(cost["costUsd"] or 0.0), 6),
            },
            "errors": [{"chapterNumber": i["chapterIndex"], "title": i["title"], "error": i["error"],
                        "paragraphsDone": i["paragraphsDone"], "paragraphsTotal": i["paragraphsTotal"]} for i in items if i["status"] == "error"],
            "items": [{key: i[key] for key in ("position", "chapterId", "chapterIndex", "title", "status", "paragraphsTotal", "paragraphsDone",
                                               "batchesTotal", "batchesDone", "error")} for i in items],
        }

    def latest(self, project_id: str) -> dict[str, Any] | None:
        queue = self._storage.latest_translation_queue(project_id)
        return self.state(queue["queueId"]) if queue else None


class QueueWorker(threading.Thread):
    """The server's single background thread: one batch at a time, queues in turn. It resumes the
    queues that were running when the server stopped (their state is in the database)."""

    def __init__(self, service: TranslationQueueService, idle_seconds: float = 1.0):
        super().__init__(name="translation-queue-worker", daemon=True)
        self._service = service
        self._idle = idle_seconds
        self._halt = threading.Event()
        self._wake = threading.Event()
        service.on_change = self.wake

    def wake(self) -> None:
        self._wake.set()

    def halt(self) -> None:
        self._halt.set()
        self._wake.set()

    def run(self) -> None:
        while not self._halt.is_set():
            worked = False
            try:
                for queue_id in self._service.running_queue_ids():
                    if self._halt.is_set():
                        break
                    if self._service.step(queue_id) in {"progress", "finished"}:
                        worked = True
            except Exception:
                logging.exception("Translation queue worker step failed")
            if not worked:
                self._wake.wait(self._idle)
                self._wake.clear()


__all__ = ["QUEUE_ENGINES", "QueueError", "QueueWorker", "TranslationQueueService", "WARN_ESTIMATE_USD"]
