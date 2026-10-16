"""Active working time: one row per active minute (UTC), days counted in Europe/Kyiv (DST included),
per day / book / chapter, CSV, the endpoints and the cascade on project delete."""
import csv
import io
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from backend import server
from backend.activity import activity_csv, activity_report
from backend.storage import Storage

KYIV = ZoneInfo("Europe/Kyiv")


def utc(text):
    return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)


def minute_row(project_id, stamp, chapter_id=None):
    return {"projectId": project_id, "chapterId": chapter_id, "minuteUtc": utc(stamp).isoformat()}


class Base(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.directory.name) / "w.sqlite3")
        self.project_id = self.storage.create_project({"title": "Книга", "status": "translation"})["projectId"]
        self.storage.save_book_structure(self.project_id, "b.epub", "application/epub+zip", b"b", {"chapters": [
            {"title": "Перший", "elements": [{"type": "paragraph", "text": "a"}]},
            {"title": "Другий", "elements": [{"type": "paragraph", "text": "b"}]},
        ]})
        self.chapters = [c["chapterId"] for c in self.storage.get_book_structure(self.project_id)["chapters"]]

    def tearDown(self):
        self.directory.cleanup()

    def count(self, project_id=None):
        with self.storage.connection() as connection:
            if project_id:
                return connection.execute("SELECT COUNT(*) FROM activity_minutes WHERE project_id = ?", (project_id,)).fetchone()[0]
            return connection.execute("SELECT COUNT(*) FROM activity_minutes").fetchone()[0]


class StorageTests(Base):
    def test_two_pings_in_one_minute_are_one_row(self):
        self.assertTrue(self.storage.record_activity_minute(self.project_id, self.chapters[0], utc("2026-10-16T10:30:05")))
        self.assertTrue(self.storage.record_activity_minute(self.project_id, self.chapters[0], utc("2026-10-16T10:30:59")))
        self.storage.record_activity_minute(self.project_id, self.chapters[1], utc("2026-10-16T10:30:30"))  # another tab, another chapter
        self.assertEqual(1, self.count())
        self.storage.record_activity_minute(self.project_id, self.chapters[0], utc("2026-10-16T10:31:00"))
        self.assertEqual(2, self.count())

    def test_minute_is_utc_iso_cut_to_the_minute(self):
        self.storage.record_activity_minute(self.project_id, None, datetime(2026, 10, 16, 13, 30, 47, 123456, tzinfo=KYIV))
        row = self.storage.list_activity_minutes()[0]
        self.assertEqual("2026-10-16T10:30:00+00:00", row["minuteUtc"])
        self.assertIsNone(row["chapterId"])

    def test_a_chapter_of_another_project_is_not_stored_and_an_unknown_project_is_refused(self):
        other = self.storage.create_project({"title": "Інша", "status": "translation"})["projectId"]
        self.assertTrue(self.storage.record_activity_minute(other, self.chapters[0], utc("2026-10-16T10:30:00")))
        self.assertIsNone(self.storage.list_activity_minutes(other)[0]["chapterId"])
        self.assertFalse(self.storage.record_activity_minute("nope", None, utc("2026-10-16T10:30:00")))
        self.assertEqual(1, self.count())

    def test_only_identifiers_and_time_are_stored(self):
        with self.storage.connection() as connection:
            columns = [row["name"] for row in connection.execute("PRAGMA table_info(activity_minutes)")]
        self.assertEqual(["project_id", "chapter_id", "minute_utc"], columns)

    def test_deleting_the_project_deletes_its_minutes_only(self):
        other = self.storage.create_project({"title": "Інша", "status": "translation"})["projectId"]
        for stamp in ("2026-10-16T10:30:00", "2026-10-16T10:31:00"):
            self.storage.record_activity_minute(self.project_id, self.chapters[0], utc(stamp))
        self.storage.record_activity_minute(other, None, utc("2026-10-16T10:30:00"))
        self.storage.delete_project(self.project_id)
        self.assertEqual(0, self.count(self.project_id))
        self.assertEqual(1, self.count(other))

    def test_the_migration_is_idempotent_on_an_existing_database(self):
        self.storage.record_activity_minute(self.project_id, None, utc("2026-10-16T10:30:00"))
        again = Storage(self.storage.database_path if hasattr(self.storage, "database_path") else Path(self.directory.name) / "w.sqlite3")
        self.assertEqual(1, len(again.list_activity_minutes()))


class DayBoundaryTests(unittest.TestCase):
    def day_of(self, stamp, today):
        report = activity_report([minute_row("p", stamp)], KYIV, 7, today)
        return [row["date"] for row in report["rows"] if row["minutes"]]

    def test_2230_utc_is_the_next_day_in_kyiv_summer_and_winter(self):
        self.assertEqual(["2026-07-16"], self.day_of("2026-07-15T22:30:00", date(2026, 7, 16)))   # UTC+3 → 01:30
        self.assertEqual(["2026-01-16"], self.day_of("2026-01-15T22:30:00", date(2026, 1, 16)))   # UTC+2 → 00:30

    def test_2130_utc_depends_on_dst(self):
        self.assertEqual(["2026-07-16"], self.day_of("2026-07-15T21:30:00", date(2026, 7, 16)))   # summer: 00:30 next day
        self.assertEqual(["2026-01-15"], self.day_of("2026-01-15T21:30:00", date(2026, 1, 16)))   # winter: 23:30 same day

    def test_the_switch_days_count_correctly(self):
        # 2026-03-29 03:00 Kyiv time jumps to 04:00 (UTC+2 → UTC+3); 2026-10-25 04:00 falls back to 03:00
        self.assertEqual(["2026-03-29"], self.day_of("2026-03-28T22:30:00", date(2026, 3, 29)))
        self.assertEqual(["2026-03-30"], self.day_of("2026-03-29T21:00:00", date(2026, 3, 30)))
        self.assertEqual(["2026-10-25"], self.day_of("2026-10-24T21:00:00", date(2026, 10, 25)))
        self.assertEqual(["2026-10-26"], self.day_of("2026-10-25T22:00:00", date(2026, 10, 26)))


class AggregationTests(Base):
    def test_per_day_book_and_chapter(self):
        other = self.storage.create_project({"title": "Інша", "status": "translation"})["projectId"]
        rows = (
            [minute_row(self.project_id, f"2026-10-14T10:{m:02d}:00", self.chapters[0]) for m in range(3)]
            + [minute_row(self.project_id, "2026-10-15T09:00:00", self.chapters[1])]
            + [minute_row(self.project_id, "2026-10-15T09:01:00")]
            + [minute_row(other, "2026-10-15T09:00:00")]
            + [minute_row(other, "2026-09-01T09:00:00")]  # out of the 7 days
        )
        report = activity_report(rows, KYIV, 7, date(2026, 10, 15), self.storage.project_titles(), self.storage.usage_chapters(self.project_id))
        self.assertEqual((7, "2026-10-09", "2026-10-15", "Europe/Kyiv"), (len(report["rows"]), report["from"], report["to"], report["timezone"]))
        self.assertEqual(6, report["totalMinutes"])
        self.assertEqual({"2026-10-14": 3, "2026-10-15": 3}, {row["date"]: row["minutes"] for row in report["rows"] if row["minutes"]})
        self.assertEqual([("Книга", 5), ("Інша", 1)], [(item["title"], item["minutes"]) for item in report["byProject"]])
        chapters = [(item["title"], item["minutes"]) for item in report["byChapter"] if item["projectId"] == self.project_id]
        self.assertEqual([("Перший", 3), (None, 1), ("Другий", 1)], chapters)  # longest first; no chapter has no title

    def test_empty_range_keeps_every_day(self):
        report = activity_report([], KYIV, 90, date(2026, 10, 15))
        self.assertEqual((90, 0, [], []), (len(report["rows"]), report["totalMinutes"], report["byProject"], report["byChapter"]))

    def test_csv_has_one_line_per_day_project_chapter_and_cannot_run_as_a_formula(self):
        rows = [minute_row("p1", "2026-10-15T22:30:00", "c1"), minute_row("p1", "2026-10-15T22:31:00", "c1"), minute_row("p1", "2026-10-14T10:00:00")]
        text = activity_csv(rows, KYIV, date(2026, 10, 14), date(2026, 10, 16), {"p1": "=Книга"}, {"c1": {"chapterIndex": 1, "title": "Розділ"}})
        self.assertTrue(text.startswith("﻿"))
        lines = list(csv.reader(io.StringIO(text.lstrip("﻿"))))
        self.assertEqual([["date", "project", "chapter", "minutes"], ["2026-10-14", "'=Книга", "", "1"], ["2026-10-16", "'=Книга", "Розділ", "2"]], lines)


class ApiTests(Base):
    class Handler:
        def __init__(self, payload=None):
            self.payload = payload

        def read_json(self):
            return self.payload

    def api(self, method, path, payload=None):
        handler = self.Handler(payload)
        handler.path = path
        with patch.object(server, "storage", self.storage):
            return server.WorkbenchHandler.handle_api(handler, method, path.split("?")[0])

    def test_post_uses_the_server_clock_and_returns_204(self):
        client_time = {"projectId": self.project_id, "chapterId": self.chapters[0], "minuteUtc": "2001-01-01T00:00:00+00:00", "time": "2001"}
        self.assertEqual((204, None), self.api("POST", "/api/activity", client_time))
        self.assertEqual((204, None), self.api("POST", "/api/activity", {"projectId": self.project_id, "chapterId": None}))
        minutes = self.storage.list_activity_minutes()
        self.assertIn(len(minutes), (1, 2))  # both pings fell into one server minute (two only if the minute turned between them)
        stored = datetime.fromisoformat(minutes[0]["minuteUtc"])
        self.assertLess(abs((datetime.now(timezone.utc) - stored).total_seconds()), 120)

    def test_post_validates(self):
        self.assertEqual(404, self.api("POST", "/api/activity", {"projectId": "nope"})[0])
        for bad in ({}, {"projectId": 5}, {"projectId": ""}, {"projectId": self.project_id, "chapterId": 5}, None):
            with self.subTest(bad=bad):
                self.assertEqual(400, self.api("POST", "/api/activity", bad)[0])

    def test_stats_ranges_scope_and_the_project_filter(self):
        self.api("POST", "/api/activity", {"projectId": self.project_id, "chapterId": self.chapters[0]})
        status, report = self.api("GET", "/api/activity/stats?days=7")
        self.assertEqual((200, 1, 7), (status, report["totalMinutes"], len(report["rows"])))
        self.assertEqual("Перший", report["byChapter"][0]["title"])
        self.assertEqual(90, len(self.api("GET", "/api/activity/stats?days=90")[1]["rows"]))
        self.assertEqual(1, self.api("GET", f"/api/activity/stats?days=30&projectId={self.project_id}")[1]["totalMinutes"])
        other = self.storage.create_project({"title": "Інша", "status": "translation"})["projectId"]
        self.assertEqual(0, self.api("GET", f"/api/activity/stats?days=30&projectId={other}")[1]["totalMinutes"])
        for bad in ("days=5", "days=x"):
            self.assertEqual(400, self.api("GET", f"/api/activity/stats?{bad}")[0])
        self.assertEqual(404, self.api("GET", "/api/activity/stats?days=7&projectId=nope")[0])

    def test_export(self):
        self.api("POST", "/api/activity", {"projectId": self.project_id, "chapterId": self.chapters[1]})
        with patch.object(server, "storage", self.storage):
            status, error, filename, content = server.activity_export({"days": ["7"]})
            self.assertEqual((400, None), (server.activity_export({"days": ["8"]})[0], None))
        self.assertEqual(200, status)
        self.assertTrue(filename.startswith("activity-") and filename.endswith(".csv"))
        self.assertIn("Книга", content)
        self.assertIn("Другий", content)


if __name__ == "__main__":
    unittest.main()
