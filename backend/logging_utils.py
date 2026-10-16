"""Persistent application logging for the production log viewer.

Mirrors everything written to stdout/stderr (print() calls, including the
"[DEEPL DEBUG]" lines) into a size-bounded rotating log file, while masking
anything that looks like a credential or API key before it hits disk.
"""

from __future__ import annotations

from logging.handlers import RotatingFileHandler
from pathlib import Path
import logging
import os
import re
import sys

DEFAULT_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
# WORKBENCH_LOG_DIR is set by the e2e server so that browser tests do not write into the application's own logs/.
LOG_DIR = Path(os.environ.get("WORKBENCH_LOG_DIR", "").strip() or DEFAULT_LOG_DIR)
LOG_FILE = LOG_DIR / "workbench.log"
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 3

_SECRET_PATTERN = re.compile(
    r"(?i)\b(api[_-]?key|apikey|authorization|secret|password|token|bearer|deepl-auth-key)\b"
    r"(\s*[:=]\s*|\s+)(\S.*)"
)

_logger = logging.getLogger("workbench")
_configured = False


def redact(text: str) -> str:
    """Mask a keyword-looking credential/API key and everything after it on the line."""
    return _SECRET_PATTERN.sub(lambda match: f"{match.group(1)}={'*' * 8}", text)


class _TeeWriter:
    """Writes to the original stream (so journalctl keeps working) and to the logger."""

    def __init__(self, original_stream, level):
        self._original = original_stream
        self._level = level
        self._buffer = ""

    def write(self, message):
        self._original.write(message)
        self._buffer += message
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if line:
                _logger.log(self._level, redact(line))
        return len(message)

    def flush(self):
        self._original.flush()

    def isatty(self):
        return False


def configure_logging() -> None:
    """Start mirroring stdout/stderr into the persistent log file.

    Safe to call more than once; only configures the process the first time.
    """
    global _configured
    if _configured:
        return
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    _logger.addHandler(handler)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False

    sys.stdout = _TeeWriter(sys.stdout, logging.INFO)
    sys.stderr = _TeeWriter(sys.stderr, logging.ERROR)
    _configured = True


# http.server writes one line per request to stderr: `127.0.0.1 - - [date] "GET /path HTTP/1.1" 200 -`. The logger puts its own
# "date [LEVEL] " in front of it; only that prefix and the request line itself are matched here.
_ACCESS_LINE = re.compile(r'"[A-Z]+ \S+ HTTP/\d(?:\.\d)?" [23]\d\d\b')
_LOG_PREFIX = re.compile(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d+ \[\w+\] ")


def is_successful_request(line: str) -> bool:
    """An access-log line of a request that went through (status 2xx or 3xx). 4xx/5xx and anything else are not."""
    return bool(_ACCESS_LINE.search(line))


def without_successful_requests(lines: list[str]) -> list[str]:
    """The lines without the 2xx/3xx access-log lines. Failed requests (4xx/5xx), tracebacks with every line that
    follows "Traceback" (the indented frames and the exception line) and anything that does not look like an access
    log stay."""
    kept: list[str] = []
    in_traceback = False
    for line in lines:
        body = _LOG_PREFIX.sub("", line, count=1)
        if body.startswith("Traceback"):
            in_traceback = True
            kept.append(line)
        elif in_traceback:
            kept.append(line)
            if body and not body[0].isspace():  # the exception line closes the block
                in_traceback = False
        elif not is_successful_request(line):
            kept.append(line)
    return kept


def read_recent_lines(max_lines: int = 200, include_requests: bool = True) -> list[str]:
    """Return up to max_lines most recent log lines, oldest first. Without include_requests the successful
    request lines are dropped first, so the limit counts the lines that are left."""
    if not LOG_FILE.exists():
        return []
    max_lines = max(1, min(max_lines, 2000))
    with LOG_FILE.open("r", encoding="utf-8", errors="replace") as handle:
        lines = [line.rstrip("\n") for line in handle.readlines()]
    if not include_requests:
        lines = without_successful_requests(lines)
    return lines[-max_lines:]
