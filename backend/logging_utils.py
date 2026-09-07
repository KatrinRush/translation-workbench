"""Persistent application logging for the production log viewer.

Mirrors everything written to stdout/stderr (print() calls, including the
"[DEEPL DEBUG]" lines) into a size-bounded rotating log file, while masking
anything that looks like a credential or API key before it hits disk.
"""

from __future__ import annotations

from logging.handlers import RotatingFileHandler
from pathlib import Path
import logging
import re
import sys

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
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
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    _logger.addHandler(handler)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False

    sys.stdout = _TeeWriter(sys.stdout, logging.INFO)
    sys.stderr = _TeeWriter(sys.stderr, logging.ERROR)
    _configured = True


def read_recent_lines(max_lines: int = 200) -> list[str]:
    """Return up to max_lines most recent log lines, oldest first."""
    if not LOG_FILE.exists():
        return []
    max_lines = max(1, min(max_lines, 2000))
    with LOG_FILE.open("r", encoding="utf-8", errors="replace") as handle:
        lines = handle.readlines()
    return [line.rstrip("\n") for line in lines[-max_lines:]]
