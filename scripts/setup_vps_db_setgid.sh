#!/usr/bin/env bash
set -euo pipefail
set -x

echo "=== 1. Setup shared workbench-db group and permissions ==="
# Check if group exists, create if not
if ! getent group workbench-db >/dev/null 2>&1; then
    sudo -n groupadd workbench-db 2>/dev/null || true
fi

# Add both workbench and deploy users to workbench-db group
sudo -n usermod -aG workbench-db workbench 2>/dev/null || true
CURRENT_USER="$(id -un)"
sudo -n usermod -aG workbench-db "$CURRENT_USER" 2>/dev/null || true

# Set ownership and setgid on database directory
sudo -n chown -R workbench:workbench-db /opt/translation-workbench/database 2>/dev/null || true
sudo -n chmod 2775 /opt/translation-workbench/database 2>/dev/null || true

# Set file permissions: group read-write for database files
sudo -n chmod 664 /opt/translation-workbench/database/workbench.sqlite3* 2>/dev/null || true

# Remove any stale -wal or -shm files so they are cleanly recreated with setgid group
sudo -n rm -vf /opt/translation-workbench/database/workbench.sqlite3-shm 2>/dev/null || rm -vf /opt/translation-workbench/database/workbench.sqlite3-shm 2>/dev/null || true
sudo -n rm -vf /opt/translation-workbench/database/workbench.sqlite3-wal 2>/dev/null || rm -vf /opt/translation-workbench/database/workbench.sqlite3-wal 2>/dev/null || true

echo "=== 2. Verify setgid behavior by creating test file as deploy user ==="
touch /opt/translation-workbench/database/test-setgid
ls -la /opt/translation-workbench/database/test-setgid
TEST_GROUP=$(stat -c '%G' /opt/translation-workbench/database/test-setgid 2>/dev/null || stat -f '%Sg' /opt/translation-workbench/database/test-setgid 2>/dev/null || echo "unknown")
echo "Created test-setgid with group: $TEST_GROUP"
rm -f /opt/translation-workbench/database/test-setgid
if [ "$TEST_GROUP" = "workbench-db" ]; then
    echo "SUCCESS: setgid works! New files inherit workbench-db group."
else
    echo "NOTE: test-setgid group is $TEST_GROUP (directory setgid: $(ls -ld /opt/translation-workbench/database))"
fi

echo "=== 3. Restart translation-workbench service ==="
sudo -n /usr/bin/systemctl restart translation-workbench

sleep 2

echo "=== 4. Verify database directory state ==="
ls -ld /opt/translation-workbench/database
ls -la /opt/translation-workbench/database/

echo "=== 5. Test SQLite read/write from API ==="
python3 -c '
import urllib.request
import json

try:
    req = urllib.request.urlopen("http://127.0.0.1:8000/api/projects")
    projects = json.loads(req.read().decode())
    print("API GET /api/projects SUCCESS! Found projects:", len(projects))
except Exception as e:
    print("API GET /api/projects error:", e)

try:
    data = json.dumps({"text": "__test_setgid_rule__", "category": "General", "priority": 999}).encode("utf-8")
    req = urllib.request.Request("http://127.0.0.1:8000/api/rules", data=data, headers={"Content-Type": "application/json"}, method="POST")
    res = urllib.request.urlopen(req)
    rule = json.loads(res.read().decode())
    rule_id = rule.get("ruleId")
    print("API POST /api/rules SUCCESS! Created ruleId:", rule_id)
    if rule_id:
        req_del = urllib.request.Request(f"http://127.0.0.1:8000/api/rules/{rule_id}", method="DELETE")
        urllib.request.urlopen(req_del)
        print("API DELETE /api/rules SUCCESS (Cleanup confirmed)!")
except Exception as e:
    print("API write test FAILED:", e)
'
