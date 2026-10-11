"""Token usage accounting for LLM calls: capture, price lookup, cost, aggregation.

Providers call `report_usage()` for every API response that carries token counts (also for
a reply that is then rejected: truncated, refused, unusable XML — it was billed). Nothing
happens unless a caller wraps the call in `capture_usage(sink)`, so provider methods keep
their signatures (`analyze()` still returns just text) and existing callers and test
doubles are unaffected.

Only token counts are stored; the cost is computed from the *current* price table.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import logging
import re
from typing import Any, Callable, Iterable, Iterator, Mapping

USAGE_KINDS = ("translate", "retry", "qa", "analysis", "chat")

UsageSink = Callable[[str | None, Mapping[str, int]], None]
_SINK: ContextVar[UsageSink | None] = ContextVar("llm_usage_sink", default=None)


@contextmanager
def capture_usage(sink: UsageSink) -> Iterator[None]:
    token = _SINK.set(sink)
    try:
        yield
    finally:
        _SINK.reset(token)


def report_usage(model: str | None, usage: Mapping[str, int] | None) -> None:
    """Called by providers for each billed API response; a no-op outside capture_usage()."""
    sink = _SINK.get()
    if sink is None or not usage:
        return
    try:
        sink(model, usage)
    except Exception:  # accounting must never break a translation
        logging.exception("Could not record LLM token usage")


class UsageRecorder:
    """Writes one translation_usage row per reported API call. `kind` may be changed between
    calls (the glossary retry switches it to "retry")."""

    def __init__(self, storage: Any, project_id: str | None, chapter_id: str | None, engine: str, kind: str):
        self.storage = storage
        self.project_id = project_id
        self.chapter_id = chapter_id
        self.engine = engine
        self.kind = kind
        self.rows: list[dict[str, Any]] = []

    def __call__(self, model: str | None, usage: Mapping[str, int]) -> None:
        row = self.storage.record_translation_usage(
            self.project_id, self.chapter_id, self.engine, model or "", self.kind, usage
        )
        if row:
            self.rows.append(row)


# --- prices --------------------------------------------------------------------------------

# "-2026-01-15" or "-20260115": the dated alias of a model. Only this exact shape is stripped,
# never an arbitrary prefix: "gpt-5.5" must not match "gpt-5.5-pro" or "gpt-5.5-mini".
_DATE_SUFFIX = re.compile(r"-(?:\d{4}-\d{2}-\d{2}|\d{8})$")


def find_price(model: str | None, prices: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Any] | None:
    """The price entry for a model: an exact match, or the model with a trailing date removed."""
    if not model:
        return None
    name = model.removeprefix("models/")
    if name in prices:
        return prices[name]
    undated = _DATE_SUFFIX.sub("", name)
    return prices.get(undated) if undated != name else None


def row_cost(row: Mapping[str, Any], price: Mapping[str, Any] | None) -> tuple[float | None, bool]:
    """(cost in USD or None when a needed price is missing, whether it is an estimate).

    Cache tokens without their own price are priced as input ("оцінка")."""
    if price is None:
        return None, False
    input_price, output_price = price.get("inputPerMTok"), price.get("outputPerMTok")
    input_tokens = row.get("inputTokens", 0)
    output_tokens = row.get("outputTokens", 0)
    cache_read = row.get("cacheReadTokens", 0)
    cache_write = row.get("cacheWriteTokens", 0)
    if (input_tokens and input_price is None) or (output_tokens and output_price is None):
        return None, False
    estimated = False
    cost = 0.0
    if input_tokens:
        cost += input_tokens * input_price
    if output_tokens:
        cost += output_tokens * output_price
    for tokens, key in ((cache_read, "cacheReadPerMTok"), (cache_write, "cacheWritePerMTok")):
        if not tokens:
            continue
        rate = price.get(key)
        if rate is None:
            if input_price is None:
                return None, False
            rate, estimated = input_price, True
        cost += tokens * rate
    return cost / 1_000_000, estimated


def _blank() -> dict[str, Any]:
    return {"calls": 0, "inputTokens": 0, "outputTokens": 0, "cacheReadTokens": 0, "cacheWriteTokens": 0,
            "costUsd": 0.0, "estimated": False, "unpriced": False}


def _add(total: dict[str, Any], row: Mapping[str, Any], cost: float | None, estimated: bool) -> None:
    total["calls"] += 1
    for key in ("inputTokens", "outputTokens", "cacheReadTokens", "cacheWriteTokens"):
        total[key] += row.get(key, 0)
    if cost is None:
        total["unpriced"] = True
    else:
        total["costUsd"] += cost
    total["estimated"] = total["estimated"] or estimated


def _finish(total: dict[str, Any]) -> dict[str, Any]:
    total["tokens"] = total["inputTokens"] + total["outputTokens"] + total["cacheReadTokens"] + total["cacheWriteTokens"]
    # costUsd is None when nothing in the group could be priced; otherwise a (possibly partial,
    # see "unpriced") sum.
    if total["unpriced"] and total["costUsd"] == 0:
        total["costUsd"] = None
    elif total["costUsd"] is not None:
        total["costUsd"] = round(total["costUsd"], 6)
    return total


def summarize(rows: Iterable[Mapping[str, Any]], prices: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Totals for usage rows, priced with the given table."""
    total = _blank()
    for row in rows:
        cost, estimated = row_cost(row, find_price(row.get("model"), prices))
        _add(total, row, cost, estimated)
    return _finish(total)


def project_report(
    rows: list[Mapping[str, Any]],
    prices: Mapping[str, Mapping[str, Any]],
    chapters: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """The "Вартість" report: engine/model, chapter and kind breakdowns plus the project total.
    Counts and titles only — no book text."""
    by_model: dict[tuple[str, str], dict[str, Any]] = {}
    by_chapter: dict[str | None, dict[str, Any]] = {}
    by_kind: dict[str, dict[str, Any]] = {}
    total = _blank()
    unpriced_models: set[str] = set()
    for row in rows:
        price = find_price(row.get("model"), prices)
        cost, estimated = row_cost(row, price)
        if cost is None:
            unpriced_models.add(row.get("model") or "?")
        _add(by_model.setdefault((row["engine"], row["model"]), {**_blank(), "engine": row["engine"], "model": row["model"]}), row, cost, estimated)
        _add(by_chapter.setdefault(row.get("chapterId"), _blank()), row, cost, estimated)
        _add(by_kind.setdefault(row["kind"], {**_blank(), "kind": row["kind"]}), row, cost, estimated)
        _add(total, row, cost, estimated)

    def chapter_entry(chapter_id: str | None, group: dict[str, Any]) -> dict[str, Any]:
        info = chapters.get(chapter_id) if chapter_id else None
        return {
            **_finish(group),
            "chapterId": chapter_id,
            "chapterIndex": info.get("chapterIndex") if info else None,
            "title": (info.get("title") if info else None),
            "removed": bool(chapter_id and info is None),
        }

    chapter_entries = [chapter_entry(chapter_id, group) for chapter_id, group in by_chapter.items()]
    chapter_entries.sort(key=lambda item: (item["chapterIndex"] is None, item["chapterIndex"] or 0))
    return {
        "byModel": sorted((_finish(group) for group in by_model.values()), key=lambda item: (item["engine"], item["model"])),
        "byChapter": chapter_entries,
        "byKind": sorted((_finish(group) for group in by_kind.values()), key=lambda item: item["kind"]),
        "total": _finish(total),
        "unpricedModels": sorted(unpriced_models),
    }


def row_from_record(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "chapterId": record["chapter_id"],
        "engine": record["engine"],
        "model": record["model"],
        "kind": record["kind"],
        "inputTokens": record["input_tokens"],
        "outputTokens": record["output_tokens"],
        "cacheReadTokens": record["cache_read_tokens"],
        "cacheWriteTokens": record["cache_write_tokens"],
        "createdAt": record["created_at"],
    }


# Initial price table, $ per 1M tokens: (input, output, cache read, cache write). None = not set.
DEFAULT_MODEL_PRICES: dict[str, tuple[float | None, float | None, float | None, float | None]] = {
    "claude-sonnet-5-5": (2.0, 10.0, 0.20, 2.50),
    "gpt-5.5": (5.0, 30.0, None, None),
    "gemini-3.6-flash": (1.5, 7.5, None, None),
}

__all__ = [
    "DEFAULT_MODEL_PRICES",
    "USAGE_KINDS",
    "UsageRecorder",
    "capture_usage",
    "find_price",
    "project_report",
    "report_usage",
    "row_cost",
    "row_from_record",
    "summarize",
]
