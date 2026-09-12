"""
Read-only diagnostic: lists every project_translation_glossaries row,
grouped by project and language pair (case-insensitively), and flags any
project that has more than one row for what should be the same
EN->UK-style pair. That's the signature of the case-mismatch bug patch 40
fixes going forward -- this script finds any damage that already
happened before the fix landed.

Makes no changes to the database. Safe to run anytime.

Run from the repo root:
    python find_duplicate_glossaries.py
"""
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

DB_PATH = Path("database/workbench.sqlite3")


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found at {DB_PATH} — run this from the repo root.")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    projects = {
        row["project_id"]: row["title"]
        for row in connection.execute("SELECT project_id, title FROM book_projects")
    }

    rows = connection.execute(
        "SELECT glossary_rule_id, project_id, source_language, target_language, "
        "entries, current_version_id, updated_at "
        "FROM project_translation_glossaries ORDER BY project_id, updated_at"
    ).fetchall()

    print(f"Total project_translation_glossaries rows: {len(rows)}\n")

    grouped = defaultdict(list)
    for row in rows:
        key = (
            row["project_id"],
            (row["source_language"] or "").strip().upper(),
            (row["target_language"] or "").strip().upper(),
        )
        grouped[key].append(row)

    found_duplicates = False
    for (project_id, source, target), group in grouped.items():
        if len(group) <= 1:
            continue
        found_duplicates = True
        title = projects.get(project_id, "<unknown project>")
        print(f"=== DUPLICATE: '{title}' ({project_id}), {source} -> {target} — {len(group)} rows ===")
        for row in group:
            entry_count = len(json.loads(row["entries"] or "[]"))
            print(
                f"  glossary_rule_id={row['glossary_rule_id']}  "
                f"stored_case=({row['source_language']!r} -> {row['target_language']!r})  "
                f"entries={entry_count}  "
                f"current_version_id={row['current_version_id']}  "
                f"updated_at={row['updated_at']}"
            )
        print()

    if not found_duplicates:
        print("No duplicate glossary rows found for any project/language pair.")

    connection.close()


if __name__ == "__main__":
    main()
