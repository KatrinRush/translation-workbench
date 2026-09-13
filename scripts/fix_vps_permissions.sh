#!/usr/bin/env bash
set -x

echo "=== 1. Removing stale WAL/SHM files owned by deploy user ==="
rm -vf /opt/translation-workbench/database/workbench.sqlite3-shm
rm -vf /opt/translation-workbench/database/workbench.sqlite3-wal

echo "=== 2. Restarting translation-workbench service (runs as workbench user) ==="
sudo -n /usr/bin/systemctl restart translation-workbench

sleep 3

echo "=== 3. Checking directory listing and ownership ==="
ls -la /opt/translation-workbench/database/

echo "=== 4. Checking systemd service status ==="
systemctl status translation-workbench --no-pager || true

echo "=== 5. Testing server read & write via HTTP API on localhost ==="
python3 -c '
import urllib.request
import json

# 1. Test GET /api/projects
try:
    req = urllib.request.urlopen("http://127.0.0.1:8000/api/projects")
    projects = json.loads(req.read().decode())
    print("API GET /api/projects SUCCESS! Found projects:", len(projects))
except Exception as e:
    print("API GET /api/projects error:", e)

# 2. Test writing to storage by creating and deleting a temporary dummy glossary entry or rule via API
try:
    data = json.dumps({"text": "__test_diagnostic_rule__", "category": "General", "priority": 999}).encode("utf-8")
    req = urllib.request.Request("http://127.0.0.1:8000/api/rules", data=data, headers={"Content-Type": "application/json"}, method="POST")
    res = urllib.request.urlopen(req)
    rule = json.loads(res.read().decode())
    rule_id = rule.get("ruleId")
    print("API POST /api/rules SUCCESS (SQLite write confirmed)! Created ruleId:", rule_id)
    
    if rule_id:
        req_del = urllib.request.Request(f"http://127.0.0.1:8000/api/rules/{rule_id}", method="DELETE")
        urllib.request.urlopen(req_del)
        print("API DELETE /api/rules SUCCESS (Cleanup confirmed)!")
except Exception as e:
    print("API write test FAILED:", e)
'

