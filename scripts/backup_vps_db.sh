#!/usr/bin/env bash
# Copy the production SQLite database to a dated file next to the original.
# Older copies are never deleted. Piped over SSH from the "backup" variant of
# .github/workflows/diagnose.yml, so it does not need to be deployed first.
set -euo pipefail

DB_DIR=/opt/translation-workbench/database
DB_NAME=workbench.sqlite3
DB_PATH="$DB_DIR/$DB_NAME"
STAMP="$(date -u +%Y-%m-%d_%H-%M-%S)UTC"
BACKUP_PATH="$DB_DIR/workbench-$STAMP.sqlite3"

echo "=== DATABASE BACKUP ($STAMP) ==="
if [ ! -f "$DB_PATH" ]; then
    echo "Database not found: $DB_PATH" >&2
    exit 1
fi

# The database runs in WAL mode: recent commits may still sit in -wal until a
# checkpoint, so the -wal/-shm files are copied with the same stamp. To restore,
# put all three back under the original names.
needed_kb=$(du -k "$DB_PATH" "$DB_PATH-wal" "$DB_PATH-shm" 2>/dev/null | awk '{sum += $1} END {print sum}')
available_kb=$(df -Pk "$DB_DIR" | awk 'NR == 2 {print $4}')
echo "Need ${needed_kb} KB, available ${available_kb} KB in $DB_DIR"
if [ "$needed_kb" -ge "$available_kb" ]; then
    echo "Not enough free space for the copy; nothing was copied." >&2
    exit 1
fi

for suffix in "" "-wal" "-shm"; do
    source_file="$DB_PATH$suffix"
    target_file="$BACKUP_PATH$suffix"
    [ -f "$source_file" ] || continue
    if [ -e "$target_file" ]; then
        echo "Refusing to overwrite existing copy: $target_file" >&2
        exit 1
    fi
    cp -p "$source_file" "$target_file"
    echo "Copied $source_file -> $target_file"
done

echo "=== COPIES IN $DB_DIR (none are deleted) ==="
ls -la "$DB_DIR"
