"""Active working time: aggregation of the stored minutes (`activity_minutes`).

One row is one active minute of a project, stored in UTC. Days are counted here in Python in the chosen
time zone (Europe/Kyiv by default, DST included), exactly like the usage report. Identifiers and times
only; titles come from the caller.
"""

from __future__ import annotations

import csv
from datetime import date, datetime, timedelta, timezone
import io
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

try:
    from .usage import _csv_text, local_date
except ImportError:  # launched as `python server.py` from inside backend/
    from usage import _csv_text, local_date


def _by_minutes_then_name(items: list[dict[str, Any]], name_key: str) -> list[dict[str, Any]]:
    return sorted(items, key=lambda item: (-item["minutes"], str(item.get(name_key) or "")))


def activity_report(
    rows: Iterable[Mapping[str, Any]],
    zone: ZoneInfo,
    days: int,
    today: date | None = None,
    project_titles: Mapping[str, str] | None = None,
    chapters: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Minutes per local calendar day for the last `days` days (today included, empty days kept), per
    project and per chapter. `chapters` maps chapterId -> {chapterIndex, title}; a chapter that is gone
    (or no chapter at all) is reported with title None."""
    today = today or datetime.now(timezone.utc).astimezone(zone).date()
    first = today - timedelta(days=days - 1)
    per_day: dict[date, int] = {first + timedelta(days=offset): 0 for offset in range(days)}
    per_project: dict[str, int] = {}
    per_chapter: dict[tuple[str, str | None], int] = {}
    total = 0
    for row in rows:
        day = local_date(row["minuteUtc"], zone)
        if day not in per_day:
            continue
        per_day[day] += 1
        per_project[row["projectId"]] = per_project.get(row["projectId"], 0) + 1
        key = (row["projectId"], row.get("chapterId"))
        per_chapter[key] = per_chapter.get(key, 0) + 1
        total += 1
    titles = project_titles or {}
    chapter_info = chapters or {}
    by_project = [{"projectId": project_id, "title": titles.get(project_id), "minutes": minutes}
                  for project_id, minutes in per_project.items()]
    by_chapter = []
    for (project_id, chapter_id), minutes in per_chapter.items():
        info = chapter_info.get(chapter_id) if chapter_id else None
        by_chapter.append({
            "projectId": project_id, "projectTitle": titles.get(project_id), "chapterId": chapter_id,
            "chapterIndex": info.get("chapterIndex") if info else None, "title": info.get("title") if info else None,
            "minutes": minutes,
        })
    return {
        "timezone": getattr(zone, "key", str(zone)),
        "days": days,
        "from": first.isoformat(),
        "to": today.isoformat(),
        "totalMinutes": total,
        "rows": [{"date": day.isoformat(), "minutes": minutes} for day, minutes in per_day.items()],
        "byProject": _by_minutes_then_name(by_project, "title"),
        "byChapter": _by_minutes_then_name(by_chapter, "title"),
    }


def activity_csv(
    rows: Iterable[Mapping[str, Any]],
    zone: ZoneInfo,
    first: date,
    last: date,
    project_titles: Mapping[str, str],
    chapters: Mapping[str, Mapping[str, Any]],
) -> str:
    """CSV for local days first..last: one line per (date, project, chapter) with the minutes. Identifiers,
    titles and counts only. UTF-8 with a BOM, like the usage export."""
    groups: dict[tuple[str, str, str | None], int] = {}
    for row in rows:
        day = local_date(row["minuteUtc"], zone)
        if not first <= day <= last:
            continue
        key = (day.isoformat(), row["projectId"], row.get("chapterId"))
        groups[key] = groups.get(key, 0) + 1
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(["date", "project", "chapter", "minutes"])
    for (day, project_id, chapter_id), minutes in sorted(groups.items(), key=lambda item: (item[0][0], item[0][1], item[0][2] or "")):
        info = chapters.get(chapter_id) if chapter_id else None
        writer.writerow([day, _csv_text(project_titles.get(project_id, project_id)), _csv_text(info["title"] if info else ""), minutes])
    return "﻿" + buffer.getvalue()
