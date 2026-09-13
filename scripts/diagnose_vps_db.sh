#!/usr/bin/env bash
set -x

echo "=== 1. DATABASE PATH FROM CODE ==="
cd /opt/translation-workbench
source .venv/bin/activate
python -c 'from backend.storage import DATABASE_PATH; print("Resolved DATABASE_PATH:", DATABASE_PATH)'

echo "=== 2. DIRECTORY AND FILE PERMISSIONS ==="
ls -ld /opt/translation-workbench
ls -ld /opt/translation-workbench/database
ls -la /opt/translation-workbench/database/

echo "=== 3. SYSTEMD SERVICE CONFIGURATION ==="
systemctl show translation-workbench -p User -p Group -p FragmentPath -p ExecStart -p WorkingDirectory -p ProtectSystem -p ReadWritePaths
FRAG_PATH="$(systemctl show translation-workbench -p FragmentPath --value 2>/dev/null || true)"
if [ -n "$FRAG_PATH" ] && [ -f "$FRAG_PATH" ]; then
    cat "$FRAG_PATH"
elif [ -f /etc/systemd/system/translation-workbench.service ]; then
    cat /etc/systemd/system/translation-workbench.service
fi

echo "=== 4. RUNNING PROCESS & DEPLOY USER ==="
ps aux | grep -E "python.*server" | grep -v grep || true
id
groups

echo "=== 5. DISK SPACE & INODES ==="
df -h /opt/translation-workbench/database/
df -i /opt/translation-workbench/database/

echo "=== 6. FILESYSTEM MOUNT OPTIONS ==="
mount | grep -E " on / | on /opt " || mount

echo "=== 7. SQLITE PRAGMAS & TEST WRITE ==="
python -c '
import sqlite3
from pathlib import Path
db_path = Path("/opt/translation-workbench/database/workbench.sqlite3")
print("File exists:", db_path.exists())
try:
    con = sqlite3.connect(str(db_path))
    print("journal_mode:", con.execute("PRAGMA journal_mode;").fetchall())
    print("locking_mode:", con.execute("PRAGMA locking_mode;").fetchall())
    print("foreign_keys:", con.execute("PRAGMA foreign_keys;").fetchall())
    try:
        con.execute("CREATE TABLE IF NOT EXISTS _diag_test (id INT)")
        con.commit()
        con.execute("DROP TABLE IF EXISTS _diag_test")
        con.commit()
        print("SQLite write test: SUCCESS")
    except Exception as e:
        print("SQLite write test FAILED:", type(e), e)
    con.close()
except Exception as e:
    print("Error connecting to SQLite:", type(e), e)
'

echo "=== 8. TEST PERMISSIONS AS DEPLOY USER ==="
if touch /opt/translation-workbench/database/.test_write 2>&1; then
    rm -f /opt/translation-workbench/database/.test_write
    echo "Deploy user CAN write to database directory"
else
    echo "Deploy user CANNOT write to database directory"
fi

echo "=== 9. RECENT JOURNAL LOGS ==="
journalctl -u translation-workbench --since "15 minutes ago" --no-pager || true
