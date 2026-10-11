#!/usr/bin/env bash
# Consistent backup of the production SQLite database to a dated file next to the
# original, via SQLite's online backup API (sqlite3.Connection.backup): the copy is a
# single self-contained file, taken while the service keeps running. Older copies are
# never deleted. Piped over SSH from the "backup" variant of
# .github/workflows/diagnose.yml, so it does not need to be deployed first.
set -euo pipefail

export DB_DIR="${WORKBENCH_DB_DIR:-/opt/translation-workbench/database}"

python3 - <<'PY'
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

db_dir = Path(os.environ["DB_DIR"])
source = db_dir / "workbench.sqlite3"
stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%SUTC")
target = db_dir / f"workbench-{stamp}.sqlite3"


def size(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


def human(n: int) -> str:
    return f"{n} B ({n / 1024 / 1024:.2f} MiB)"


print(f"=== DATABASE BACKUP ({stamp}) ===", flush=True)
if not source.is_file():
    sys.exit(f"Database not found: {source}")
if target.exists():
    sys.exit(f"Refusing to overwrite existing copy: {target}")

# The copy holds every committed page, including those still in -wal, so it can be
# as large as the database plus its WAL.
needed = size(source) + size(source.with_name(source.name + "-wal"))
free = shutil.disk_usage(db_dir).free
print(f"Source: {source} = {human(size(source))}, -wal = {human(size(source.with_name(source.name + '-wal')))}")
print(f"Need up to {human(needed)}, free {human(free)} in {db_dir}")
if needed >= free:
    sys.exit("Not enough free space for the copy; nothing was copied.")

try:
    source_connection = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    source_connection.execute("SELECT count(*) FROM sqlite_master").fetchone()
except sqlite3.Error as error:
    # A read-only connection to a WAL database needs a usable -shm; fall back to a
    # normal connection, which still only reads here.
    print(f"Read-only open failed ({error}); using a regular connection.")
    source_connection = sqlite3.connect(source)

# O_EXCL: never overwrite, even if a copy with this name appears in the meantime.
os.close(os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o640))
try:
    target_connection = sqlite3.connect(target)
    with target_connection:
        source_connection.backup(target_connection)
    # The backup copies the WAL flag from the source header; switch the copy to a
    # rollback journal so it stays one standalone file with no -wal/-shm.
    target_connection.execute("PRAGMA journal_mode=DELETE").fetchone()
    target_connection.close()
except BaseException:
    target.unlink(missing_ok=True)  # only the partial file this run created
    raise
finally:
    source_connection.close()

print(f"Copied {source} -> {target}")
print(f"Backup size: {human(size(target))}")

check_connection = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
results = [row[0] for row in check_connection.execute("PRAGMA integrity_check").fetchall()]
journal_mode = check_connection.execute("PRAGMA journal_mode").fetchone()[0]
check_connection.close()
print(f"PRAGMA integrity_check on {target.name}: {'; '.join(results)}")
print(f"Backup journal_mode: {journal_mode}")
leftovers = [p.name for p in (target.with_name(target.name + "-wal"), target.with_name(target.name + "-shm")) if p.exists()]
if leftovers:
    print(f"Warning: unexpected files next to the copy: {', '.join(leftovers)}")
if results != ["ok"]:
    sys.exit("Integrity check FAILED for the backup copy (the copy is kept for inspection).")
PY

echo "=== COPIES IN $DB_DIR (none are deleted) ==="
ls -la "$DB_DIR"
