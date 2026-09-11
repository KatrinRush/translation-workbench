"""Patch 21: footnotes, part 1 — backend (storage.py + server.py).

Data model: footnote *position* lives inline in translation_text as an
invisible marker token (Private Use Area delimiters wrapping the footnote_id).
It travels with the text through edit/save/undo like any other character, so
no separate "anchor" bookkeeping is needed. Footnote *content* (the note text)
lives in a new paragraph_footnotes table.

Numbering is project-wide and continuous, computed in get_book_structure
(which already loads the whole book in reading order) by scanning each
paragraph's translation_text for markers, left to right, chapter by chapter.

Frontend (app.js/api.js) and DOCX export (export_service.py) are separate
follow-up patches once those files are available.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
STORAGE_PATH = REPO_ROOT / "backend" / "storage.py"
SERVER_PATH = REPO_ROOT / "backend" / "server.py"


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"{label}: expected text not found — file may have changed, aborting.")
    if text.count(old) > 1:
        raise SystemExit(f"{label}: expected text is not unique — aborting to avoid a wrong edit.")
    return text.replace(old, new, 1)


def patch_storage() -> None:
    text = STORAGE_PATH.read_text(encoding="utf-8")

    # 1. New table, right after book_paragraphs.
    text = _replace_once(
        text,
        '''CREATE TABLE IF NOT EXISTS book_inline_images (''',
        '''CREATE TABLE IF NOT EXISTS paragraph_footnotes (
    footnote_id TEXT PRIMARY KEY,
    paragraph_id TEXT NOT NULL REFERENCES book_paragraphs(paragraph_id) ON DELETE CASCADE,
    note_text TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_paragraph_footnotes_paragraph ON paragraph_footnotes(paragraph_id);

CREATE TABLE IF NOT EXISTS book_inline_images (''',
        "schema (paragraph_footnotes table)",
    )

    # 2. Footnote marker token + regex, next to the other small module-level helpers.
    text = _replace_once(
        text,
        '''def _bool(value: int) -> bool:
    return bool(value)
''',
        '''def _bool(value: int) -> bool:
    return bool(value)


# Footnote position marker embedded directly inside translation_text:
# \\uE000<footnote_id>\\uE000. Private-Use-Area characters so they never
# collide with real text, survive plain-text editing/undo like any other
# character, and are invisible until the frontend renders them as markers.
FOOTNOTE_TOKEN_RE = re.compile("\\uE000([0-9a-zA-Z_-]+)\\uE000")
''',
        "FOOTNOTE_TOKEN_RE helper",
    )

    # 3. get_book_structure: preload footnote note text + assign continuous numbering.
    text = _replace_once(
        text,
        '''    def get_book_structure(self, project_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            book = connection.execute("SELECT * FROM book_documents WHERE project_id = ?", (project_id,)).fetchone()
            if book is None:
                return None
            chapter_rows = connection.execute("SELECT * FROM book_chapters WHERE book_id = ? ORDER BY chapter_index", (book["book_id"],)).fetchall()
            chapters = []
            paragraph_count = 0
            for chapter in chapter_rows:
                elements = []
                element_rows = connection.execute("SELECT * FROM book_chapter_elements WHERE chapter_id = ? ORDER BY element_index", (chapter["chapter_id"],)).fetchall()
                for element in element_rows:
                    if element["element_type"] == "paragraph":
                        row = connection.execute("SELECT paragraph_id, original_text, translation_text, reviewed, is_service FROM book_paragraphs WHERE paragraph_id = ?", (element["element_id"],)).fetchone()
                        if row:
                            paragraph_count += 1
                            elements.append({"type": "paragraph", "paragraphId": row["paragraph_id"], "originalText": row["original_text"], "translationText": row["translation_text"], "reviewed": bool(row["reviewed"]), "isService": bool(row["is_service"])})
                    else:''',
        '''    def get_book_structure(self, project_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            book = connection.execute("SELECT * FROM book_documents WHERE project_id = ?", (project_id,)).fetchone()
            if book is None:
                return None
            footnote_note_rows = connection.execute(
                "SELECT pf.footnote_id, pf.note_text FROM paragraph_footnotes pf "
                "JOIN book_paragraphs bp ON bp.paragraph_id = pf.paragraph_id "
                "JOIN book_chapters bch ON bch.chapter_id = bp.chapter_id "
                "WHERE bch.book_id = ?",
                (book["book_id"],),
            ).fetchall()
            footnote_notes_by_id = {row["footnote_id"]: row["note_text"] for row in footnote_note_rows}
            footnote_number = 0
            chapter_rows = connection.execute("SELECT * FROM book_chapters WHERE book_id = ? ORDER BY chapter_index", (book["book_id"],)).fetchall()
            chapters = []
            paragraph_count = 0
            for chapter in chapter_rows:
                elements = []
                element_rows = connection.execute("SELECT * FROM book_chapter_elements WHERE chapter_id = ? ORDER BY element_index", (chapter["chapter_id"],)).fetchall()
                for element in element_rows:
                    if element["element_type"] == "paragraph":
                        row = connection.execute("SELECT paragraph_id, original_text, translation_text, reviewed, is_service FROM book_paragraphs WHERE paragraph_id = ?", (element["element_id"],)).fetchone()
                        if row:
                            paragraph_count += 1
                            footnotes = []
                            for footnote_id in FOOTNOTE_TOKEN_RE.findall(row["translation_text"] or ""):
                                note_text = footnote_notes_by_id.get(footnote_id)
                                if note_text is None:
                                    continue
                                footnote_number += 1
                                footnotes.append({"footnoteId": footnote_id, "noteText": note_text, "number": footnote_number})
                            elements.append({"type": "paragraph", "paragraphId": row["paragraph_id"], "originalText": row["original_text"], "translationText": row["translation_text"], "reviewed": bool(row["reviewed"]), "isService": bool(row["is_service"]), "footnotes": footnotes})
                    else:''',
        "get_book_structure numbering",
    )

    # 4. update_paragraph: drop footnote rows whose marker got deleted from the text.
    text = _replace_once(
        text,
        '''    def update_paragraph(self, paragraph_id: str, translation_text: str | None, reviewed: bool, is_service: bool | None = None) -> dict[str, Any] | None:
        with self.connection() as connection:
            if is_service is None:
                cursor = connection.execute("UPDATE book_paragraphs SET translation_text = ?, reviewed = ? WHERE paragraph_id = ?", (translation_text, int(reviewed), paragraph_id))
            else:
                cursor = connection.execute("UPDATE book_paragraphs SET translation_text = ?, reviewed = ?, is_service = ? WHERE paragraph_id = ?", (translation_text, int(reviewed), int(is_service), paragraph_id))
            if cursor.rowcount == 0:
                return None
            row = connection.execute("SELECT * FROM book_paragraphs WHERE paragraph_id = ?", (paragraph_id,)).fetchone()
        return {"paragraphId": row["paragraph_id"], "originalText": row["original_text"], "translationText": row["translation_text"], "reviewed": bool(row["reviewed"]), "isService": bool(row["is_service"])}''',
        '''    def update_paragraph(self, paragraph_id: str, translation_text: str | None, reviewed: bool, is_service: bool | None = None) -> dict[str, Any] | None:
        with self.connection() as connection:
            if is_service is None:
                cursor = connection.execute("UPDATE book_paragraphs SET translation_text = ?, reviewed = ? WHERE paragraph_id = ?", (translation_text, int(reviewed), paragraph_id))
            else:
                cursor = connection.execute("UPDATE book_paragraphs SET translation_text = ?, reviewed = ?, is_service = ? WHERE paragraph_id = ?", (translation_text, int(reviewed), int(is_service), paragraph_id))
            if cursor.rowcount == 0:
                return None
            remaining_footnote_ids = set(FOOTNOTE_TOKEN_RE.findall(translation_text or ""))
            existing_footnote_ids = {
                existing_row["footnote_id"]
                for existing_row in connection.execute(
                    "SELECT footnote_id FROM paragraph_footnotes WHERE paragraph_id = ?", (paragraph_id,)
                ).fetchall()
            }
            orphaned_ids = existing_footnote_ids - remaining_footnote_ids
            if orphaned_ids:
                connection.executemany(
                    "DELETE FROM paragraph_footnotes WHERE footnote_id = ?",
                    [(footnote_id,) for footnote_id in orphaned_ids],
                )
            row = connection.execute("SELECT * FROM book_paragraphs WHERE paragraph_id = ?", (paragraph_id,)).fetchone()
        return {"paragraphId": row["paragraph_id"], "originalText": row["original_text"], "translationText": row["translation_text"], "reviewed": bool(row["reviewed"]), "isService": bool(row["is_service"])}''',
        "update_paragraph orphan cleanup",
    )

    # 5. CRUD for footnote content, placed right after get_paragraph.
    text = _replace_once(
        text,
        '''    def get_paragraph(self, paragraph_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM book_paragraphs WHERE paragraph_id = ?", (paragraph_id,)).fetchone()
        if row is None:
            return None
        return {"paragraphId": row["paragraph_id"], "originalText": row["original_text"], "translationText": row["translation_text"], "reviewed": bool(row["reviewed"]), "isService": bool(row["is_service"])}
''',
        '''    def get_paragraph(self, paragraph_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM book_paragraphs WHERE paragraph_id = ?", (paragraph_id,)).fetchone()
        if row is None:
            return None
        return {"paragraphId": row["paragraph_id"], "originalText": row["original_text"], "translationText": row["translation_text"], "reviewed": bool(row["reviewed"]), "isService": bool(row["is_service"])}

    def list_paragraph_footnotes(self, paragraph_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT footnote_id, paragraph_id, note_text, created_at FROM paragraph_footnotes "
                "WHERE paragraph_id = ? ORDER BY created_at",
                (paragraph_id,),
            ).fetchall()
        return [self._footnote_from_row(row) for row in rows]

    def create_paragraph_footnote(self, paragraph_id: str, data: dict[str, Any]) -> dict[str, Any]:
        note_text = (data.get("noteText") or "").strip()
        if not note_text:
            raise ValueError("Текст зноски не може бути порожнім.")
        footnote_id = _new_id("footnote")
        timestamp = _now()
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO paragraph_footnotes(footnote_id, paragraph_id, note_text, created_at) VALUES (?, ?, ?, ?)",
                (footnote_id, paragraph_id, note_text, timestamp),
            )
        return {"footnoteId": footnote_id, "paragraphId": paragraph_id, "noteText": note_text, "createdAt": timestamp}

    def update_paragraph_footnote(self, footnote_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        note_text = (data.get("noteText") or "").strip()
        if not note_text:
            raise ValueError("Текст зноски не може бути порожнім.")
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE paragraph_footnotes SET note_text = ? WHERE footnote_id = ?",
                (note_text, footnote_id),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute("SELECT * FROM paragraph_footnotes WHERE footnote_id = ?", (footnote_id,)).fetchone()
        return self._footnote_from_row(row)

    def delete_paragraph_footnote(self, footnote_id: str) -> bool:
        with self.connection() as connection:
            cursor = connection.execute("DELETE FROM paragraph_footnotes WHERE footnote_id = ?", (footnote_id,))
        return cursor.rowcount > 0

    @staticmethod
    def _footnote_from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "footnoteId": row["footnote_id"],
            "paragraphId": row["paragraph_id"],
            "noteText": row["note_text"],
            "createdAt": row["created_at"],
        }
''',
        "footnote CRUD methods",
    )

    STORAGE_PATH.write_text(text, encoding="utf-8")
    print(f"Patched {STORAGE_PATH}")


def patch_server() -> None:
    text = SERVER_PATH.read_text(encoding="utf-8")

    text = _replace_once(
        text,
        '''        if len(parts) == 3 and parts[:2] == ["api", "paragraphs"] and method in {"PUT", "PATCH"}:''',
        '''        if len(parts) == 4 and parts[:2] == ["api", "paragraphs"] and parts[3] == "footnotes":
            paragraph_id = parts[2]
            if method == "GET":
                return 200, storage.list_paragraph_footnotes(paragraph_id)
            if method == "POST":
                try:
                    return 201, storage.create_paragraph_footnote(paragraph_id, self.read_json())
                except ValueError as error:
                    return 400, {"error": str(error)}
        if len(parts) == 5 and parts[:2] == ["api", "paragraphs"] and parts[3] == "footnotes":
            footnote_id = parts[4]
            if method in {"PUT", "PATCH"}:
                try:
                    footnote = storage.update_paragraph_footnote(footnote_id, self.read_json())
                except ValueError as error:
                    return 400, {"error": str(error)}
                return (200, footnote) if footnote else (404, {"error": "Footnote not found."})
            if method == "DELETE":
                if not storage.delete_paragraph_footnote(footnote_id):
                    return 404, {"error": "Footnote not found."}
                return 204, None
        if len(parts) == 3 and parts[:2] == ["api", "paragraphs"] and method in {"PUT", "PATCH"}:''',
        "server.py footnote routes",
    )

    SERVER_PATH.write_text(text, encoding="utf-8")
    print(f"Patched {SERVER_PATH}")


if __name__ == "__main__":
    patch_storage()
    patch_server()
