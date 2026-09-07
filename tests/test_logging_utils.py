from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from backend.logging_utils import read_recent_lines, redact


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


if __name__ == "__main__":
    unittest.main()
