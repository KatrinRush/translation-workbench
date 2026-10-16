from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from backend import server
from backend.logging_utils import is_successful_request, read_recent_lines, redact, without_successful_requests


class RedactTests(unittest.TestCase):
    def test_redacts_api_key_value(self):
        line = "[DEEPL DEBUG] apiKey=sk-abcdef123456 tag_handling='xml'"
        self.assertNotIn("sk-abcdef123456", redact(line))

    def test_redacts_authorization_header_style_value(self):
        line = "Authorization: DeepL-Auth-Key abcdef1234567890"
        redacted = redact(line)
        self.assertNotIn("abcdef1234567890", redacted)

    def test_leaves_non_secret_debug_fields_untouched(self):
        line = (
            "[DEEPL DEBUG] tag_handling='xml' tag_handling_version='1' "
            "glossary_id='glossary-1' context_present=True context='Some context'"
        )
        self.assertEqual(line, redact(line))


class ReadRecentLinesTests(unittest.TestCase):
    def test_returns_empty_list_when_log_file_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            missing_path = Path(directory) / "workbench.log"
            with patch("backend.logging_utils.LOG_FILE", missing_path):
                self.assertEqual([], read_recent_lines())

    def test_returns_most_recent_lines_in_order(self):
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "workbench.log"
            log_path.write_text("\n".join(f"line-{i}" for i in range(10)) + "\n", encoding="utf-8")
            with patch("backend.logging_utils.LOG_FILE", log_path):
                lines = read_recent_lines(3)
        self.assertEqual(["line-7", "line-8", "line-9"], lines)


def request_line(path, status, method="GET", seconds=0):
    return f'2026-10-16 22:00:{seconds:02d},000 [ERROR] 127.0.0.1 - - [16/Oct/2026 22:00:{seconds:02d}] "{method} {path} HTTP/1.1" {status} -'


TRACEBACK = [
    "2026-10-16 22:01:00,000 [ERROR] Traceback (most recent call last):",
    '2026-10-16 22:01:00,001 [ERROR]   File "backend/server.py", line 1, in handle_api',
    "2026-10-16 22:01:00,002 [ERROR]     raise ValueError('boom')",
    "2026-10-16 22:01:00,003 [ERROR] ValueError: boom",
]


class SuccessfulRequestFilterTests(unittest.TestCase):
    def test_2xx_and_3xx_requests_are_recognised_4xx_5xx_are_not(self):
        for status in (200, 201, 204, 301, 302, 304):
            self.assertTrue(is_successful_request(request_line("/api/projects", status)), status)
        for status in (400, 404, 409, 500, 502):
            self.assertFalse(is_successful_request(request_line("/api/projects", status)), status)
        self.assertTrue(is_successful_request(request_line("/api/projects", 200, method="POST")))
        self.assertTrue(is_successful_request('127.0.0.1 - - [16/Oct/2026 22:00:00] "GET /app.js?v=2 HTTP/1.1" 304 -'))  # without the logger prefix

    def test_filter_drops_200_and_304_keeps_404_500_and_other_lines(self):
        lines = [
            request_line("/api/projects", 200, seconds=1),
            request_line("/api/books", 404, seconds=2),
            request_line("/app.js", 304, seconds=3),
            request_line("/api/paragraphs/x", 500, method="PUT", seconds=4),
            "2026-10-16 22:00:05,000 [INFO] [DEEPL DEBUG] glossary_id='g' status 200",
            '2026-10-16 22:00:06,000 [ERROR] 127.0.0.1 - - [16/Oct/2026 22:00:06] code 404, message File not found',
        ]
        kept = without_successful_requests(lines)
        self.assertEqual([lines[1], lines[3], lines[4], lines[5]], kept)

    def test_traceback_keeps_every_line_that_follows_it(self):
        lines = [request_line("/a", 200, seconds=1), *TRACEBACK, request_line("/b", 200, seconds=2), request_line("/c", 500, seconds=3)]
        self.assertEqual([*TRACEBACK, lines[-1]], without_successful_requests(lines))

    def test_a_logging_exception_traceback_without_prefixes_stays_whole(self):
        raw = ["Traceback (most recent call last):", '  File "x.py", line 1, in f', "    g()", "KeyError: 'a'"]
        lines = [request_line("/a", 200), *raw, request_line("/a", 200, seconds=1)]
        self.assertEqual(raw, without_successful_requests(lines))


class ReadRecentLinesRequestsTests(unittest.TestCase):
    def read(self, lines, *args, **kwargs):
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "workbench.log"
            log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            with patch("backend.logging_utils.LOG_FILE", log_path):
                return read_recent_lines(*args, **kwargs)

    def test_requests_are_included_unless_asked_otherwise_for_the_function(self):
        lines = [request_line("/a", 200), "[INFO] hello"]
        self.assertEqual(lines, self.read(lines))
        self.assertEqual(["[INFO] hello"], self.read(lines, 200, include_requests=False))

    def test_the_limit_counts_the_lines_left_after_the_filter(self):
        lines = ["[INFO] one", "[INFO] two"] + [request_line("/p", 200, seconds=i % 60) for i in range(50)] + ["[INFO] three"]
        # 53 lines in the file; the last 3 of them are requests and "three": the limit must not be spent on requests
        self.assertEqual(["[INFO] one", "[INFO] two", "[INFO] three"], self.read(lines, 3, include_requests=False))
        self.assertEqual(3, len(self.read(lines, 3)))
        self.assertEqual(lines[-3:], self.read(lines, 3, include_requests=True))


class LogsEndpointTests(unittest.TestCase):
    class Handler:
        def __init__(self, path):
            self.path = path

    def get(self, path, lines):
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "workbench.log"
            log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            with patch("backend.logging_utils.LOG_FILE", log_path):
                return server.WorkbenchHandler.handle_api(self.Handler(path), "GET", path.split("?")[0])

    def test_requests_are_hidden_by_default_and_come_back_with_include_requests_1(self):
        lines = [request_line("/api/projects", 200), request_line("/api/x", 404, seconds=1), *TRACEBACK, "[INFO] done"]
        status, payload = self.get("/api/logs", lines)
        self.assertEqual((200, [lines[1], *TRACEBACK, "[INFO] done"]), (status, payload["lines"]))
        self.assertEqual(lines, self.get("/api/logs?includeRequests=1", lines)[1]["lines"])
        self.assertEqual(payload["lines"], self.get("/api/logs?includeRequests=0", lines)[1]["lines"])
        self.assertEqual(payload["lines"], self.get("/api/logs?includeRequests=yes", lines)[1]["lines"])  # anything but 1 is 0

    def test_limit_applies_after_the_filter(self):
        lines = ["[INFO] a", "[INFO] b"] + [request_line("/p", 200, seconds=i) for i in range(30)]
        self.assertEqual(["[INFO] a", "[INFO] b"], self.get("/api/logs?limit=2", lines)[1]["lines"])
        self.assertEqual(lines[-2:], self.get("/api/logs?limit=2&includeRequests=1", lines)[1]["lines"])


if __name__ == "__main__":
    unittest.main()
