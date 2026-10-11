#!/usr/bin/env bash
# Read-only report: per chapter, how many paragraphs there are, how many rows
# paragraph_translation_variants has per engine, and how many paragraphs have a
# selected_variant_id. Prints counts only -- never book or translation text.
# The database is opened with mode=ro, so nothing can be changed.
#
# Usage (on the VPS):  bash scripts/diagnose_variants_db.sh [path/to/workbench.sqlite3]
# Or from this checkout over stdin, like the other diagnostics:
#   WORKBENCH_DB=/opt/translation-workbench/database/workbench.sqlite3 bash -s < scripts/diagnose_variants_db.sh
set -euo pipefail

DB_PATH="${1:-${WORKBENCH_DB:-/opt/translation-workbench/database/workbench.sqlite3}}"

python3 - "$DB_PATH" <<'PY'
import sqlite3
import sys
from pathlib import Path
from urllib.parse import quote

ENGINES = ("current", "deepl", "claude", "openai", "gemini", "manual")
db_path = Path(sys.argv[1])
print(f"=== VARIANTS REPORT (read-only): {db_path} ===")
if not db_path.exists():
    sys.exit(f"Database not found: {db_path}")

connection = sqlite3.connect(f"file:{quote(str(db_path.resolve()))}?mode=ro", uri=True, timeout=30)
connection.row_factory = sqlite3.Row
connection.execute("PRAGMA query_only = ON")
try:
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    if "paragraph_translation_variants" not in tables:
        sys.exit("Table paragraph_translation_variants does not exist (migration has not run yet).")
    paragraph_columns = {row["name"] for row in connection.execute("PRAGMA table_info(book_paragraphs)")}
    has_selected = "selected_variant_id" in paragraph_columns

    projects = connection.execute(
        "SELECT p.project_id, p.title, d.book_id FROM book_projects p "
        "LEFT JOIN book_documents d ON d.project_id = p.project_id ORDER BY p.created_at"
    ).fetchall()
    totals = {engine: 0 for engine in ENGINES}
    for project in projects:
        print(f"\n--- project {project['project_id']} · {project['title']!r} · "
              f"{'book ' + project['book_id'] if project['book_id'] else 'no book uploaded'}")
        if not project["book_id"]:
            continue
        print(f"{'ch':>3}  {'title':<30} {'paras':>5} {'transl':>6} {'sel':>4} {'dangl':>5}  "
              + " ".join(f"{engine:>7}" for engine in ENGINES) + "  other")
        for chapter in connection.execute(
            "SELECT chapter_id, chapter_index, title FROM book_chapters WHERE book_id = ? ORDER BY chapter_index",
            (project["book_id"],),
        ):
            paragraphs = connection.execute(
                "SELECT COUNT(*) AS total, "
                "SUM(CASE WHEN TRIM(COALESCE(translation_text, '')) != '' THEN 1 ELSE 0 END) AS translated, "
                + ("SUM(CASE WHEN selected_variant_id IS NOT NULL THEN 1 ELSE 0 END) AS selected, "
                   "SUM(CASE WHEN selected_variant_id IS NOT NULL AND NOT EXISTS "
                   "(SELECT 1 FROM paragraph_translation_variants v WHERE v.variant_id = book_paragraphs.selected_variant_id) "
                   "THEN 1 ELSE 0 END) AS dangling "
                   if has_selected else "0 AS selected, 0 AS dangling ")
                + "FROM book_paragraphs WHERE chapter_id = ?",
                (chapter["chapter_id"],),
            ).fetchone()
            counts = dict(connection.execute(
                "SELECT v.engine, COUNT(*) FROM paragraph_translation_variants v "
                "JOIN book_paragraphs p ON p.paragraph_id = v.paragraph_id WHERE p.chapter_id = ? GROUP BY v.engine",
                (chapter["chapter_id"],),
            ).fetchall())
            other = sum(count for engine, count in counts.items() if engine not in ENGINES)
            for engine in ENGINES:
                totals[engine] += counts.get(engine, 0)
            title = (chapter["title"] or "").replace("\n", " ")[:28]
            print(f"{chapter['chapter_index']:>3}  {title:<30} {paragraphs['total']:>5} {paragraphs['translated'] or 0:>6} "
                  f"{paragraphs['selected'] or 0:>4} {paragraphs['dangling'] or 0:>5}  "
                  + " ".join(f"{counts.get(engine, 0):>7}" for engine in ENGINES) + f"  {other}")
    orphans = connection.execute(
        "SELECT COUNT(*) FROM paragraph_translation_variants v "
        "WHERE NOT EXISTS (SELECT 1 FROM book_paragraphs p WHERE p.paragraph_id = v.paragraph_id)"
    ).fetchone()[0]
    print("\n=== TOTALS ===")
    print("variants per engine:", ", ".join(f"{engine}={totals[engine]}" for engine in ENGINES))
    print("variant rows whose paragraph no longer exists:", orphans)
    print("columns: transl = paragraphs with a chosen translation; sel = paragraphs with selected_variant_id; "
          "dangl = selected_variant_id pointing at a missing variant")
finally:
    connection.close()
PY
