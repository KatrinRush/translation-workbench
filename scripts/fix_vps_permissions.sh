#!/usr/bin/env bash
set -x

echo "=== Applying database permission fix ==="
sudo -n chown -R workbench:workbench /opt/translation-workbench/database 2>/dev/null || chown -R workbench:workbench /opt/translation-workbench/database 2>/dev/null || true
sudo -n chmod -R 775 /opt/translation-workbench/database 2>/dev/null || chmod -R 775 /opt/translation-workbench/database 2>/dev/null || true
sudo -n chmod 664 /opt/translation-workbench/database/workbench.sqlite3* 2>/dev/null || chmod 664 /opt/translation-workbench/database/workbench.sqlite3* 2>/dev/null || true

echo "=== Restarting translation-workbench service ==="
sudo -n /usr/bin/systemctl restart translation-workbench

sleep 2

echo "=== Verifying permissions after fix ==="
ls -ld /opt/translation-workbench/database
ls -la /opt/translation-workbench/database/

echo "=== Testing write capability as workbench user / python ==="
cd /opt/translation-workbench
source .venv/bin/activate
python -c '
import sqlite3
from pathlib import Path
db_path = Path("/opt/translation-workbench/database/workbench.sqlite3")
print("File exists:", db_path.exists())
try:
    con = sqlite3.connect(str(db_path))
    con.execute("CREATE TABLE IF NOT EXISTS _diag_test (id INT)")
    con.commit()
    con.execute("DROP TABLE IF EXISTS _diag_test")
    con.commit()
    print("SQLite write test: SUCCESS!")
    con.close()
except Exception as e:
    print("SQLite write test FAILED:", type(e), e)
'

echo "=== Service Status ==="
systemctl status translation-workbench --no-pager || true
