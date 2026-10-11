"""Token usage accounting for LLM calls: capture, price lookup, cost, aggregation.

Providers call `report_usage()` for every API response that carries token counts (also for
a reply that is then rejected: truncated, refused, unusable XML — it was billed). Nothing
happens unless a caller wraps the call in `capture_usage(sink)`, so provider methods keep
their signatures (`analyze()` still returns just text) and existing callers and test
doubles are unaffected.

Only token counts are stored; the cost is computed from the *current* price table.
"""

from __future__ import annotations

import csv
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date, datetime, timedelta, timezone
import io
import logging
import re
from typing import Any, Callable, Iterable, Iterator, Mapping
from zoneinfo import ZoneInfo

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

    def __init__(
        self, storage: Any, project_id: str | None, chapter_id: str | None, engine: str, kind: str,
        queue_id: str | None = None, source_chars: int | None = None,
    ):
        self.storage = storage
        self.queue_id = queue_id
        self.source_chars = source_chars
        self.project_id = project_id
        self.chapter_id = chapter_id
        self.engine = engine
        self.kind = kind
        self.rows: list[dict[str, Any]] = []

    def __call__(self, model: str | None, usage: Mapping[str, int]) -> None:
        row = self.storage.record_translation_usage(
            self.project_id, self.chapter_id, self.engine, model or "", self.kind, usage,
            queue_id=self.queue_id, source_chars=self.source_chars,
        )
        if row:
            self.rows.append(row)


# --- prices --------------------------------------------------------------------------------

# "-2026-01-15" or "-20260115": the dated alias of a model. Only this exact shape is stripped,
# never an arbitrary prefix: "gpt-5.5" must not match "gpt-5.5-pro" or "gpt-5.5-mini".
_DATE_SUFFIX = re.compile(r"-(?:\d{4}-\d{2}-\d{2}|\d{8})$")


PRICE_KEYS = ("inputPerMTok", "outputPerMTok", "cacheReadPerMTok", "cacheWritePerMTok")


def has_any_price(entry: Mapping[str, Any] | None) -> bool:
    return bool(entry) and any(entry.get(key) is not None for key in PRICE_KEYS)


def find_price(model: str | None, prices: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Any] | None:
    """The price entry for a model: an exact match, or the model with a trailing date removed.
    A row with no price at all is ignored, so it never shadows the row of the undated model
    ("gpt-5.5-2026-04-23" without prices does not hide "gpt-5.5")."""
    if not model:
        return None
    name = model.removeprefix("models/")
    if has_any_price(prices.get(name)):
        return prices[name]
    undated = _DATE_SUFFIX.sub("", name)
    if undated != name and has_any_price(prices.get(undated)):
        return prices[undated]
    return None


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
            "costUsd": 0.0, "estimated": False, "unpriced": False, "unpricedCalls": 0}


def _add(total: dict[str, Any], row: Mapping[str, Any], cost: float | None, estimated: bool) -> None:
    total["calls"] += 1
    for key in ("inputTokens", "outputTokens", "cacheReadTokens", "cacheWriteTokens"):
        total[key] += row.get(key, 0)
    if cost is None:
        total["unpriced"] = True
        total["unpricedCalls"] += 1
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


# --- days (a time zone, DST included) -------------------------------------------------------------

DEFAULT_TIMEZONE = "Europe/Kyiv"
_TIMEZONE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_+\-]*(?:/[A-Za-z0-9_+\-]+){0,2}$")


def resolve_timezone(name: Any) -> ZoneInfo | None:
    """The zone for an IANA name, or None when it is not valid (never raises)."""
    if not isinstance(name, str) or len(name) > 64 or not _TIMEZONE_NAME.match(name):
        return None
    try:
        return ZoneInfo(name)
    except (ValueError, OSError, KeyError):  # ZoneInfoNotFoundError is a KeyError
        return None


def timezone_or_default(name: Any) -> ZoneInfo:
    return resolve_timezone(name) or ZoneInfo(DEFAULT_TIMEZONE)


def parse_utc(value: str) -> datetime:
    moment = datetime.fromisoformat(value)
    return moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment.astimezone(timezone.utc)


def local_date(created_at: str, zone: ZoneInfo) -> date:
    """The calendar day of a UTC timestamp in `zone` (created_at stays UTC in the database)."""
    return parse_utc(created_at).astimezone(zone).date()


def local_day_start_utc(day: date, zone: ZoneInfo) -> datetime:
    """The UTC instant at which `day` begins in `zone`."""
    return datetime(day.year, day.month, day.day, tzinfo=zone).astimezone(timezone.utc)


def _group_list(groups: dict[Any, dict[str, Any]], key_name: str) -> list[dict[str, Any]]:
    return [{**_finish(group), key_name: key} for key, group in sorted(groups.items(), key=lambda item: str(item[0]))]


def daily_report(
    rows: Iterable[Mapping[str, Any]],
    prices: Mapping[str, Mapping[str, Any]],
    zone: ZoneInfo,
    days: int,
    today: date | None = None,
) -> dict[str, Any]:
    """Usage per local calendar day for the last `days` days (today included, empty days kept).

    Rows without a price are counted, not dropped: every group has `unpricedCalls`, and a sum
    with unpriced calls is incomplete."""
    today = today or datetime.now(timezone.utc).astimezone(zone).date()
    first = today - timedelta(days=days - 1)
    per_day: dict[date, dict[str, Any]] = {first + timedelta(days=offset): _blank() for offset in range(days)}
    engines: dict[date, dict[str, dict[str, Any]]] = {day: {} for day in per_day}
    kinds: dict[date, dict[str, dict[str, Any]]] = {day: {} for day in per_day}
    range_engines: dict[str, dict[str, Any]] = {}
    range_kinds: dict[str, dict[str, Any]] = {}
    total = _blank()
    unpriced_models: set[str] = set()
    for row in rows:
        day = local_date(row["createdAt"], zone)
        if day not in per_day:
            continue
        cost, estimated = row_cost(row, find_price(row.get("model"), prices))
        if cost is None:
            unpriced_models.add(row.get("model") or "?")
        _add(per_day[day], row, cost, estimated)
        _add(engines[day].setdefault(row["engine"], _blank()), row, cost, estimated)
        _add(kinds[day].setdefault(row["kind"], _blank()), row, cost, estimated)
        _add(range_engines.setdefault(row["engine"], _blank()), row, cost, estimated)
        _add(range_kinds.setdefault(row["kind"], _blank()), row, cost, estimated)
        _add(total, row, cost, estimated)
    day_entries = [
        {
            **_finish(group),
            "date": day.isoformat(),
            "incomplete": group["unpricedCalls"] > 0,
            "byEngine": _group_list(engines[day], "engine"),
            "byKind": _group_list(kinds[day], "kind"),
        }
        for day, group in per_day.items()
    ]
    total_entry = {**_finish(total), "incomplete": total["unpricedCalls"] > 0}
    return {
        "timezone": getattr(zone, "key", str(zone)),
        "days": days,
        "from": first.isoformat(),
        "to": today.isoformat(),
        "rows": day_entries,
        "total": total_entry,
        "byEngine": _group_list(range_engines, "engine"),
        "byKind": _group_list(range_kinds, "kind"),
        "unpricedModels": sorted(unpriced_models),
    }


def _csv_text(value: Any) -> str:
    """A text cell that a spreadsheet will not run as a formula."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


def usage_csv(
    rows: Iterable[Mapping[str, Any]],
    prices: Mapping[str, Mapping[str, Any]],
    zone: ZoneInfo,
    first: date,
    last: date,
    project_titles: Mapping[str, str],
) -> str:
    """CSV of usage for local days first..last: one line per (day, project, engine, model, kind).
    Counts only, never book text. cost_usd is empty when the model has no price."""
    groups: dict[tuple, dict[str, Any]] = {}
    for row in rows:
        day = local_date(row["createdAt"], zone)
        if not first <= day <= last:
            continue
        cost, estimated = row_cost(row, find_price(row.get("model"), prices))
        key = (day.isoformat(), row.get("projectId") or "", row["engine"], row["model"], row["kind"])
        _add(groups.setdefault(key, _blank()), row, cost, estimated)
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(["date", "project", "engine", "model", "kind", "calls", "input_tokens", "output_tokens",
                     "cache_read_tokens", "cache_write_tokens", "cost_usd", "cost_note"])
    for (day, project_id, engine, model, kind), group in sorted(groups.items()):
        cost = None if group["unpriced"] else round(group["costUsd"], 6)
        note = "no price" if group["unpriced"] else ("estimate" if group["estimated"] else "")
        writer.writerow([
            day, _csv_text(project_titles.get(project_id, project_id)), engine, _csv_text(model), kind, group["calls"],
            group["inputTokens"], group["outputTokens"], group["cacheReadTokens"], group["cacheWriteTokens"],
            "" if cost is None else f"{cost:.6f}", note,
        ])
    return "\ufeff" + buffer.getvalue()


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
        "projectId": record["project_id"],
        "queueId": record["queue_id"] if "queue_id" in record.keys() else None,
        "sourceChars": record["source_chars"] if "source_chars" in record.keys() else None,
    }


# Initial price table, $ per 1M tokens: (input, output, cache read, cache write). None = not set.
DEFAULT_MODEL_PRICES: dict[str, tuple[float | None, float | None, float | None, float | None]] = {
    "claude-sonnet-5-5": (2.0, 10.0, 0.20, 2.50),
    "gpt-5.5": (5.0, 30.0, None, None),
    "gemini-3.6-flash": (1.5, 7.5, None, None),
}

__all__ = [
    "DEFAULT_MODEL_PRICES",
    "DEFAULT_TIMEZONE",
    "PRICE_KEYS",
    "daily_report",
    "has_any_price",
    "local_date",
    "local_day_start_utc",
    "resolve_timezone",
    "timezone_or_default",
    "usage_csv",
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
