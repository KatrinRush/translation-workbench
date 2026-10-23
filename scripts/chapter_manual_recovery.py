"""Look at one chapter's paragraphs and, if asked, put the manual edits back as the chosen text.

Read-only by default: it opens the database with mode=ro and prints, per paragraph, the marks, the chosen
variant and every stored version. «Вручну» is the single variant a manual edit is kept in.

    python scripts/chapter_manual_recovery.py database/workbench.sqlite3 --chapter 7
    python scripts/chapter_manual_recovery.py database/workbench.sqlite3 --chapter 7 --restore-manual          # shows the plan
    python scripts/chapter_manual_recovery.py database/workbench.sqlite3 --chapter 7 --restore-manual --apply  # writes

--chapter is the number in the book's chapter list (1 = first), or a part of the title. --restore-manual only changes paragraphs
whose chosen text is not the «Вручну» text; it writes translation_text and selected_variant_id, nothing else.
The marks «Перевірено»/«Вичитано» are not stored anywhere but in the paragraph row, so this script cannot bring
them back (restore them from a backup or set them again in the editor). With --apply a copy of the database
is written next to it first.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


def short(text: str | None, limit: int = 70) -> str:
    plain = " ".join((text or "").split())
    return plain if len(plain) <= limit else plain[: limit - 1] + "…"


def find_chapters(connection: sqlite3.Connection, selector: str) -> list[sqlite3.Row]:
    if selector.isdigit():  # the n-th chapter of the book, as numbered in the list
        return connection.execute("SELECT * FROM book_chapters ORDER BY chapter_index LIMIT 1 OFFSET ?", (max(int(selector) - 1, 0),)).fetchall()
    return connection.execute(
        "SELECT * FROM book_chapters WHERE title LIKE ? ORDER BY chapter_index", (f"%{selector}%",)
    ).fetchall()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("database")
    parser.add_argument("--chapter", required=True, help="chapter number or a part of its title")
    parser.add_argument("--restore-manual", action="store_true", help="plan to choose the «Вручну» text again")
    parser.add_argument("--apply", action="store_true", help="with --restore-manual: write it (after a backup copy)")
    args = parser.parse_args()

    path = Path(args.database)
    if not path.is_file():
        print(f"No such database: {path}", file=sys.stderr)
        return 2
    connection = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row

    chapters = find_chapters(connection, args.chapter)
    if len(chapters) != 1:
        print("Pick exactly one chapter; candidates (chapter_index, title):", file=sys.stderr)
        for chapter in chapters or connection.execute("SELECT * FROM book_chapters ORDER BY chapter_index LIMIT 60").fetchall():
            print(f"  {chapter['chapter_index']}: {chapter['title']}", file=sys.stderr)
        return 2
    chapter = chapters[0]
    print(f"Chapter index {chapter['chapter_index']}: {chapter['title']}")

    plan = []
    marked = 0
    for paragraph in connection.execute(
        "SELECT * FROM book_paragraphs WHERE chapter_id = ? ORDER BY paragraph_index", (chapter["chapter_id"],)
    ):
        variants = connection.execute(
            "SELECT * FROM paragraph_translation_variants WHERE paragraph_id = ? ORDER BY engine, created_at", (paragraph["paragraph_id"],)
        ).fetchall()
        marked += 1 if paragraph["reviewed"] or paragraph["proofread"] else 0
        selected = next((v for v in variants if v["variant_id"] == paragraph["selected_variant_id"]), None)
        print(
            f"\n#{paragraph['paragraph_index']} reviewed={bool(paragraph['reviewed'])} proofread={bool(paragraph['proofread'])} "
            f"chosen={selected['engine'] if selected else None}\n  file:   {short(paragraph['translation_text'])}"
        )
        for variant in variants:
            flag = "*" if selected is not None and variant["variant_id"] == selected["variant_id"] else " "
            print(f"  {flag}{variant['engine']:<7} {variant['updated_at']}  {short(variant['text'])}")
        manual = next((v for v in variants if v["engine"] == "manual"), None)
        if manual and manual["text"] and manual["text"] != (paragraph["translation_text"] or ""):
            plan.append((paragraph, manual))
    print(f"\nParagraphs with a mark now: {marked}. Manual text differing from the chosen one: {len(plan)}.")

    if not args.restore_manual:
        return 0
    for paragraph, manual in plan:
        print(f"WOULD SET #{paragraph['paragraph_index']}: {short(paragraph['translation_text'], 40)!r} -> {short(manual['text'], 40)!r}")
    if not args.apply or not plan:
        print("Nothing written." if plan else "Nothing to restore.")
        return 0

    backup = path.with_name(f"{path.name}.{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.bak")
    with sqlite3.connect(backup) as target:
        connection.backup(target)
    connection.close()
    print(f"Backup: {backup}")
    with sqlite3.connect(path) as writable:  # one transaction: all or nothing
        for paragraph, manual in plan:
            writable.execute(
                "UPDATE book_paragraphs SET translation_text = ?, selected_variant_id = ? WHERE paragraph_id = ?",
                (manual["text"], manual["variant_id"], paragraph["paragraph_id"]),
            )
    print(f"Restored {len(plan)} paragraphs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
