"""Keeps the e2e server away from the application's own data.

The browser tests run against a throwaway database and a throwaway log directory. Without
WORKBENCH_DATABASE_PATH / WORKBENCH_LOG_DIR the e2e server makes a fresh temporary directory (so every
start begins with an empty database), with them it uses the given paths, but never one that is, or lies
inside, the application's own database/ or logs/. The only thing ever deleted is the temporary directory
the server created itself.
"""

from __future__ import annotations

import atexit
import os
from pathlib import Path
import shutil
import signal
import sys
import tempfile
from typing import MutableMapping

REPO_ROOT = Path(__file__).resolve().parent.parent
PROTECTED_DATABASE = (REPO_ROOT / "database" / "workbench.sqlite3").resolve()
PROTECTED_DIRECTORIES = ((REPO_ROOT / "database").resolve(), (REPO_ROOT / "logs").resolve())
TEMPORARY_PREFIX = "workbench-e2e-"


class UnsafeE2ePath(RuntimeError):
    """The e2e server was pointed at data that belongs to the application."""


def _inside(path: Path, directory: Path) -> bool:
    return path == directory or directory in path.parents


def check_database_path(raw: str | os.PathLike) -> Path:
    path = Path(raw).expanduser().resolve()  # resolves symlinks and ".."
    if path == PROTECTED_DATABASE or any(_inside(path, directory) for directory in PROTECTED_DIRECTORIES):
        raise UnsafeE2ePath(f"The e2e database must not be the application's own data: {path}")
    if path.suffix != ".sqlite3":
        raise UnsafeE2ePath(f"The e2e database must be a *.sqlite3 file: {path}")
    return path


def check_log_directory(raw: str | os.PathLike) -> Path:
    path = Path(raw).expanduser().resolve()
    if path in (REPO_ROOT, Path(path.anchor)) or any(_inside(path, directory) for directory in PROTECTED_DIRECTORIES) \
            or _inside(REPO_ROOT, path):
        raise UnsafeE2ePath(f"The e2e log directory must not be the application's own data: {path}")
    return path


def remove_created_directory(directory: Path) -> bool:
    """Deletes `directory` only when it is a temporary directory this module made. Returns whether it did."""
    try:
        resolved = directory.resolve()
        temp_root = Path(tempfile.gettempdir()).resolve()
        if directory.is_symlink() or resolved.parent != temp_root or not resolved.name.startswith(TEMPORARY_PREFIX):
            return False
        shutil.rmtree(resolved, ignore_errors=True)
        return True
    except OSError:
        return False


def prepare(environ: MutableMapping[str, str] | None = None) -> dict[str, str]:
    """Sets WORKBENCH_DATABASE_PATH and WORKBENCH_LOG_DIR in `environ`. Call before importing backend.server."""
    environ = os.environ if environ is None else environ
    database = environ.get("WORKBENCH_DATABASE_PATH", "").strip()
    logs = environ.get("WORKBENCH_LOG_DIR", "").strip()
    created = None
    if not database or not logs:
        created = Path(tempfile.mkdtemp(prefix=TEMPORARY_PREFIX))
    database_path = check_database_path(database or created / "workbench.sqlite3")
    log_directory = check_log_directory(logs or created / "logs")
    environ["WORKBENCH_DATABASE_PATH"] = str(database_path)
    environ["WORKBENCH_LOG_DIR"] = str(log_directory)
    return {"database": str(database_path), "logs": str(log_directory), "created": str(created) if created else ""}


def install_cleanup(created: str) -> None:
    """Removes the temporary directory at exit (a SIGTERM from Playwright counts as an exit)."""
    if not created:
        return
    directory = Path(created)
    atexit.register(remove_created_directory, directory)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
