"""SQLite persistence for Translation Workbench domain entities."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sqlite3
from zipfile import ZIP_DEFLATED, ZipFile
from typing import Any, Iterator
from uuid import uuid4


DATABASE_PATH = Path(__file__).resolve().parent.parent / "database" / "workbench.sqlite3"


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS authors (
    author_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS series (
    series_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rules (
    rule_id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    category TEXT,
    priority INTEGER,
    active INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS glossary_entries (
    glossary_entry_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    target TEXT NOT NULL,
    note TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS series_author_contexts (
    series_id TEXT NOT NULL REFERENCES series(series_id) ON DELETE CASCADE,
    author_id TEXT NOT NULL REFERENCES authors(author_id) ON DELETE CASCADE,
    PRIMARY KEY (series_id, author_id)
);

CREATE TABLE IF NOT EXISTS series_author_rules (
    series_id TEXT NOT NULL,
    author_id TEXT NOT NULL,
    rule_id TEXT NOT NULL REFERENCES rules(rule_id) ON DELETE CASCADE,
    PRIMARY KEY (series_id, author_id, rule_id),
    FOREIGN KEY (series_id, author_id)
        REFERENCES series_author_contexts(series_id, author_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS series_author_glossary (
    series_id TEXT NOT NULL,
    author_id TEXT NOT NULL,
    glossary_entry_id TEXT NOT NULL REFERENCES glossary_entries(glossary_entry_id) ON DELETE CASCADE,
    PRIMARY KEY (series_id, author_id, glossary_entry_id),
    FOREIGN KEY (series_id, author_id)
        REFERENCES series_author_contexts(series_id, author_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS book_projects (
    project_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author_id TEXT REFERENCES authors(author_id),
    series_id TEXT REFERENCES series(series_id),
    status TEXT NOT NULL,
    file_name TEXT,
    file_format TEXT,
    file_size INTEGER,
    book_number INTEGER,
    analysis_result TEXT,
    chapter_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_rules (
    project_id TEXT NOT NULL REFERENCES book_projects(project_id) ON DELETE CASCADE,
    rule_id TEXT NOT NULL REFERENCES rules(rule_id) ON DELETE CASCADE,
    inherited INTEGER NOT NULL DEFAULT 0,
    confirmed INTEGER NOT NULL DEFAULT 0,
    confirmed_at TEXT,
    PRIMARY KEY (project_id, rule_id)
);

CREATE TABLE IF NOT EXISTS project_glossary (
    project_id TEXT NOT NULL REFERENCES book_projects(project_id) ON DELETE CASCADE,
    glossary_entry_id TEXT NOT NULL REFERENCES glossary_entries(glossary_entry_id) ON DELETE CASCADE,
    inherited INTEGER NOT NULL DEFAULT 0,
    confirmed INTEGER NOT NULL DEFAULT 0,
    confirmed_at TEXT,
    PRIMARY KEY (project_id, glossary_entry_id)
);

CREATE TABLE IF NOT EXISTS book_documents (
    book_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL UNIQUE REFERENCES book_projects(project_id),
    file_name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    checksum TEXT NOT NULL,
    source_content BLOB NOT NULL,
    title TEXT,
    author TEXT,
    language TEXT,
    word_count INTEGER NOT NULL DEFAULT 0,
    chapter_count INTEGER NOT NULL DEFAULT 0,
    analysis_status TEXT NOT NULL,
    analyzed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS book_chapters (
    chapter_id TEXT PRIMARY KEY,
    book_id TEXT NOT NULL REFERENCES book_documents(book_id) ON DELETE CASCADE,
    chapter_index INTEGER NOT NULL,
    title TEXT NOT NULL,
    word_count INTEGER NOT NULL DEFAULT 0,
    paragraph_count INTEGER NOT NULL DEFAULT 0,
    UNIQUE(book_id, chapter_index)
);

CREATE TABLE IF NOT EXISTS book_paragraphs (
    paragraph_id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL REFERENCES book_chapters(chapter_id) ON DELETE CASCADE,
    paragraph_index INTEGER NOT NULL,
    original_text TEXT NOT NULL,
    word_count INTEGER NOT NULL DEFAULT 0,
    translation_text TEXT,
    reviewed INTEGER NOT NULL DEFAULT 0,
    UNIQUE(chapter_id, paragraph_index)
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4()}"


def _json(value: str | None) -> Any:
    return json.loads(value) if value else None


def _bool(value: int) -> bool:
    return bool(value)


class Storage:
    def __init__(self, database_path: str | Path = DATABASE_PATH):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connection() as connection:
            connection.executescript(SCHEMA)
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(book_projects)")}
            if "book_number" not in columns:
                connection.execute("ALTER TABLE book_projects ADD COLUMN book_number INTEGER")
            paragraph_columns = {row["name"] for row in connection.execute("PRAGMA table_info(book_paragraphs)")}
            if "translation_text" not in paragraph_columns:
                connection.execute("ALTER TABLE book_paragraphs ADD COLUMN translation_text TEXT")
            if "reviewed" not in paragraph_columns:
                connection.execute("ALTER TABLE book_paragraphs ADD COLUMN reviewed INTEGER NOT NULL DEFAULT 0")

    def list_authors(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM authors ORDER BY name").fetchall()
        return [
            {
                "authorId": row["author_id"],
                "name": row["name"],
                "createdAt": row["created_at"],
                "updatedAt": row["updated_at"],
            }
            for row in rows
        ]

    def create_author(self, data: dict[str, Any]) -> dict[str, Any]:
        timestamp = _now()
        author = {
            "authorId": data.get("authorId") or _new_id("author"),
            "name": str(data.get("name", "")).strip(),
            "createdAt": timestamp,
            "updatedAt": timestamp,
        }
        if not author["name"]:
            raise ValueError("Author name is required.")
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO authors(author_id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (author["authorId"], author["name"], timestamp, timestamp),
            )
        return author

    def update_author(self, author_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        name = str(data.get("name", "")).strip()
        if not name:
            raise ValueError("Author name is required.")
        timestamp = _now()
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE authors SET name = ?, updated_at = ? WHERE author_id = ?",
                (name, timestamp, author_id),
            )
            if cursor.rowcount == 0:
                return None
        return next((item for item in self.list_authors() if item["authorId"] == author_id), None)

    def delete_author(self, author_id: str) -> bool:
        with self.connection() as connection:
            dependencies = connection.execute(
                "SELECT (SELECT COUNT(*) FROM book_projects WHERE author_id = ?) + "
                "(SELECT COUNT(*) FROM series_author_contexts WHERE author_id = ?)",
                (author_id, author_id),
            ).fetchone()[0]
            if dependencies:
                raise ValueError("Авторку не можна видалити. Вона використовується в одному або кількох книжкових проєктах. Спочатку змініть авторку в пов’язаних проєктах.")
            return connection.execute("DELETE FROM authors WHERE author_id = ?", (author_id,)).rowcount > 0

    def list_series(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM series ORDER BY name").fetchall()
        return [
            {
                "seriesId": row["series_id"],
                "name": row["name"],
                "createdAt": row["created_at"],
                "updatedAt": row["updated_at"],
            }
            for row in rows
        ]

    def create_series(self, data: dict[str, Any]) -> dict[str, Any]:
        timestamp = _now()
        series = {
            "seriesId": data.get("seriesId") or _new_id("series"),
            "name": str(data.get("name", "")).strip(),
            "createdAt": timestamp,
            "updatedAt": timestamp,
        }
        if not series["name"]:
            raise ValueError("Series name is required.")
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO series(series_id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (series["seriesId"], series["name"], timestamp, timestamp),
            )
        return series

    def update_series(self, series_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        name = str(data.get("name", "")).strip()
        if not name:
            raise ValueError("Series name is required.")
        timestamp = _now()
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE series SET name = ?, updated_at = ? WHERE series_id = ?",
                (name, timestamp, series_id),
            )
            if cursor.rowcount == 0:
                return None
        return next((item for item in self.list_series() if item["seriesId"] == series_id), None)

    def delete_series(self, series_id: str) -> bool:
        with self.connection() as connection:
            dependencies = connection.execute(
                "SELECT (SELECT COUNT(*) FROM book_projects WHERE series_id = ?) + "
                "(SELECT COUNT(*) FROM series_author_contexts WHERE series_id = ?)",
                (series_id, series_id),
            ).fetchone()[0]
            if dependencies:
                raise ValueError("Серію не можна видалити. Вона використовується в одному або кількох книжкових проєктах. Спочатку змініть серію в пов’язаних проєктах.")
            return connection.execute("DELETE FROM series WHERE series_id = ?", (series_id,)).rowcount > 0

    def list_rules(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM rules ORDER BY text").fetchall()
        return [self._rule_from_row(row) for row in rows]

    def create_rule(self, data: dict[str, Any]) -> dict[str, Any]:
        rule = {
            "ruleId": data.get("ruleId") or _new_id("rule"),
            "text": str(data.get("text", "")).strip(),
            "category": data.get("category"),
            "priority": data.get("priority"),
            "active": bool(data.get("active", True)),
            "updatedAt": _now(),
        }
        if not rule["text"]:
            raise ValueError("Rule text is required.")
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO rules(rule_id, text, category, priority, active, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (rule["ruleId"], rule["text"], rule["category"], rule["priority"], int(rule["active"]), rule["updatedAt"]),
            )
        return rule

    def update_rule(self, rule_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        updated = {
            "text": str(data.get("text", "")).strip(),
            "category": data.get("category"),
            "priority": data.get("priority"),
            "active": bool(data.get("active", True)),
            "updatedAt": _now(),
        }
        if not updated["text"]:
            raise ValueError("Rule text is required.")
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE rules SET text = ?, category = ?, priority = ?, active = ?, updated_at = ? WHERE rule_id = ?",
                (updated["text"], updated["category"], updated["priority"], int(updated["active"]), updated["updatedAt"], rule_id),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute("SELECT * FROM rules WHERE rule_id = ?", (rule_id,)).fetchone()
        return self._rule_from_row(row)

    def delete_rule(self, rule_id: str) -> bool:
        with self.connection() as connection:
            dependencies = connection.execute(
                "SELECT (SELECT COUNT(*) FROM project_rules WHERE rule_id = ?) + "
                "(SELECT COUNT(*) FROM series_author_rules WHERE rule_id = ?)",
                (rule_id, rule_id),
            ).fetchone()[0]
            if dependencies:
                raise ValueError("Rule cannot be deleted: it is referenced by a project or series-author context.")
            return connection.execute("DELETE FROM rules WHERE rule_id = ?", (rule_id,)).rowcount > 0

    @staticmethod
    def _rule_from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "ruleId": row["rule_id"],
            "text": row["text"],
            "category": row["category"],
            "priority": row["priority"],
            "active": _bool(row["active"]),
            "updatedAt": row["updated_at"],
        }

    def list_glossary(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM glossary_entries ORDER BY source").fetchall()
        return [self._glossary_from_row(row) for row in rows]

    def create_glossary_entry(self, data: dict[str, Any]) -> dict[str, Any]:
        entry = {
            "glossaryEntryId": data.get("glossaryEntryId") or _new_id("glossary"),
            "source": str(data.get("source", "")).strip(),
            "target": str(data.get("target", "")).strip(),
            "note": data.get("note"),
            "active": bool(data.get("active", True)),
            "updatedAt": _now(),
        }
        if not entry["source"] or not entry["target"]:
            raise ValueError("Glossary source and target are required.")
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO glossary_entries(glossary_entry_id, source, target, note, active, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (entry["glossaryEntryId"], entry["source"], entry["target"], entry["note"], int(entry["active"]), entry["updatedAt"]),
            )
        return entry

    def update_glossary_entry(self, entry_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        updated = {
            "source": str(data.get("source", "")).strip(),
            "target": str(data.get("target", "")).strip(),
            "note": data.get("note"),
            "active": bool(data.get("active", True)),
            "updatedAt": _now(),
        }
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE glossary_entries SET source = ?, target = ?, note = ?, active = ?, updated_at = ? WHERE glossary_entry_id = ?",
                (updated["source"], updated["target"], updated["note"], int(updated["active"]), updated["updatedAt"], entry_id),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute("SELECT * FROM glossary_entries WHERE glossary_entry_id = ?", (entry_id,)).fetchone()
        return self._glossary_from_row(row)

    def delete_glossary_entry(self, entry_id: str) -> bool:
        with self.connection() as connection:
            dependencies = connection.execute(
                "SELECT (SELECT COUNT(*) FROM project_glossary WHERE glossary_entry_id = ?) + "
                "(SELECT COUNT(*) FROM series_author_glossary WHERE glossary_entry_id = ?)",
                (entry_id, entry_id),
            ).fetchone()[0]
            if dependencies:
                raise ValueError("Glossary entry cannot be deleted: it is referenced by a project or series-author context.")
            return connection.execute("DELETE FROM glossary_entries WHERE glossary_entry_id = ?", (entry_id,)).rowcount > 0

    @staticmethod
    def _glossary_from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "glossaryEntryId": row["glossary_entry_id"],
            "source": row["source"],
            "target": row["target"],
            "note": row["note"],
            "active": _bool(row["active"]),
            "updatedAt": row["updated_at"],
        }

    def get_series_author_context(self, series_id: str, author_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            context = connection.execute(
                "SELECT series_id, author_id FROM series_author_contexts WHERE series_id = ? AND author_id = ?",
                (series_id, author_id),
            ).fetchone()
            if context is None:
                return None
            rule_rows = connection.execute(
                "SELECT rule_id FROM series_author_rules WHERE series_id = ? AND author_id = ? ORDER BY rule_id",
                (series_id, author_id),
            ).fetchall()
            glossary_rows = connection.execute(
                "SELECT glossary_entry_id FROM series_author_glossary WHERE series_id = ? AND author_id = ? ORDER BY glossary_entry_id",
                (series_id, author_id),
            ).fetchall()
        return {
            "seriesId": context["series_id"],
            "authorId": context["author_id"],
            "ruleIds": [row["rule_id"] for row in rule_rows],
            "glossaryEntryIds": [row["glossary_entry_id"] for row in glossary_rows],
        }

    def upsert_series_author_context(self, series_id: str, author_id: str, data: dict[str, Any]) -> dict[str, Any]:
        rule_ids = list(dict.fromkeys(data.get("ruleIds", [])))
        glossary_ids = list(dict.fromkeys(data.get("glossaryEntryIds", [])))
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO series_author_contexts(series_id, author_id) VALUES (?, ?) ON CONFLICT DO NOTHING",
                (series_id, author_id),
            )
            connection.execute(
                "DELETE FROM series_author_rules WHERE series_id = ? AND author_id = ?",
                (series_id, author_id),
            )
            connection.executemany(
                "INSERT INTO series_author_rules(series_id, author_id, rule_id) VALUES (?, ?, ?)",
                [(series_id, author_id, rule_id) for rule_id in rule_ids],
            )
            connection.execute(
                "DELETE FROM series_author_glossary WHERE series_id = ? AND author_id = ?",
                (series_id, author_id),
            )
            connection.executemany(
                "INSERT INTO series_author_glossary(series_id, author_id, glossary_entry_id) VALUES (?, ?, ?)",
                [(series_id, author_id, entry_id) for entry_id in glossary_ids],
            )
        return self.get_series_author_context(series_id, author_id) or {
            "seriesId": series_id,
            "authorId": author_id,
            "ruleIds": rule_ids,
            "glossaryEntryIds": glossary_ids,
        }

    def list_projects(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM book_projects ORDER BY created_at").fetchall()
        return [self._project_from_row(row) for row in rows]

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM book_projects WHERE project_id = ?", (project_id,)).fetchone()
        return self._project_from_row(row) if row else None

    def create_project(self, data: dict[str, Any]) -> dict[str, Any]:
        project_id = data.get("projectId") or _new_id("project")
        timestamp = _now()
        project = self._project_input(data, project_id, timestamp, timestamp)
        with self.connection() as connection:
            self._write_project(connection, project, replace=False)
        return self.get_project(project_id) or project

    def update_project(self, project_id: str, data: dict[str, Any]) -> dict[str, Any]:
        existing = self.get_project(project_id)
        if existing is None:
            return None
        project = self._project_input(data, project_id, existing["createdAt"], _now(), existing)
        with self.connection() as connection:
            self._write_project(connection, project, replace=True)
        return self.get_project(project_id)

    def delete_project(self, project_id: str) -> bool:
        with self.connection() as connection:
            return connection.execute("DELETE FROM book_projects WHERE project_id = ?", (project_id,)).rowcount > 0

    def save_book_structure(self, project_id: str, filename: str, mime_type: str, content: bytes, analysis: dict[str, Any]) -> dict[str, Any]:
        timestamp = _now()
        book_id = _new_id("book")
        checksum = hashlib.sha256(content).hexdigest()
        chapters = analysis.get("chapters", [])
        with self.connection() as connection:
            project = connection.execute("SELECT project_id FROM book_projects WHERE project_id = ?", (project_id,)).fetchone()
            if project is None:
                raise ValueError("BookProject not found.")
            connection.execute("DELETE FROM book_documents WHERE project_id = ?", (project_id,))
            connection.execute(
                "INSERT INTO book_documents(book_id, project_id, file_name, mime_type, file_size, checksum, source_content, title, author, language, word_count, chapter_count, analysis_status, analyzed_at, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (book_id, project_id, filename, mime_type, len(content), checksum, content, analysis.get("title"), analysis.get("author"), analysis.get("language"), analysis.get("wordCount", 0), len(chapters), "completed", timestamp, timestamp, timestamp),
            )
            for chapter_index, chapter in enumerate(chapters, 1):
                chapter_id = _new_id("chapter")
                paragraphs = chapter.get("paragraphs", [])
                connection.execute(
                    "INSERT INTO book_chapters(chapter_id, book_id, chapter_index, title, word_count, paragraph_count) VALUES (?, ?, ?, ?, ?, ?)",
                    (chapter_id, book_id, chapter_index, chapter.get("title") or "", chapter.get("wordCount", 0), len(paragraphs)),
                )
                connection.executemany(
                    "INSERT INTO book_paragraphs(paragraph_id, chapter_id, paragraph_index, original_text, word_count) VALUES (?, ?, ?, ?, ?)",
                    [(_new_id("paragraph"), chapter_id, paragraph_index, paragraph, len(str(paragraph).split())) for paragraph_index, paragraph in enumerate(paragraphs, 1)],
                )
            connection.execute(
                "UPDATE book_projects SET file_name = ?, file_format = ?, file_size = ?, analysis_result = ?, chapter_count = ?, updated_at = ? WHERE project_id = ?",
                (filename, "epub", len(content), json.dumps(analysis, ensure_ascii=False), len(chapters), timestamp, project_id),
            )
        return self.get_book_structure(project_id) or {}

    def get_book_structure(self, project_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            book = connection.execute("SELECT * FROM book_documents WHERE project_id = ?", (project_id,)).fetchone()
            if book is None:
                return None
            chapter_rows = connection.execute("SELECT * FROM book_chapters WHERE book_id = ? ORDER BY chapter_index", (book["book_id"],)).fetchall()
            chapters = []
            paragraph_count = 0
            for chapter in chapter_rows:
                paragraphs = connection.execute("SELECT paragraph_id, original_text, translation_text, reviewed FROM book_paragraphs WHERE chapter_id = ? ORDER BY paragraph_index", (chapter["chapter_id"],)).fetchall()
                paragraph_count += len(paragraphs)
                chapters.append({
                    "title": chapter["title"],
                    "wordCount": chapter["word_count"],
                    "paragraphs": [{
                        "paragraphId": row["paragraph_id"],
                        "originalText": row["original_text"],
                        "translationText": row["translation_text"],
                        "reviewed": bool(row["reviewed"]),
                    } for row in paragraphs],
                })
        return {
            "bookId": book["book_id"],
            "projectId": project_id,
            "filename": book["file_name"],
            "title": book["title"],
            "author": book["author"],
            "language": book["language"],
            "wordCount": book["word_count"],
            "sections": book["chapter_count"],
            "paragraphCount": paragraph_count,
            "analysisStatus": book["analysis_status"],
            "analyzedAt": book["analyzed_at"],
            "chapters": chapters,
        }

    def create_book_archive(self, project_id: str, translations: dict[str, Any] | None = None) -> tuple[str, bytes]:
        with self.connection() as connection:
            project = connection.execute("SELECT * FROM book_projects WHERE project_id = ?", (project_id,)).fetchone()
            book = connection.execute("SELECT * FROM book_documents WHERE project_id = ?", (project_id,)).fetchone()
            if project is None or book is None:
                raise ValueError("Збережену книгу для цього проєкту не знайдено.")
            author = connection.execute("SELECT name FROM authors WHERE author_id = ?", (project["author_id"],)).fetchone()
            series = connection.execute("SELECT name FROM series WHERE series_id = ?", (project["series_id"],)).fetchone()
            chapter_rows = connection.execute("SELECT * FROM book_chapters WHERE book_id = ? ORDER BY chapter_index", (book["book_id"],)).fetchall()
            chapters = []
            paragraphs = []
            for chapter in chapter_rows:
                chapters.append({"chapterId": chapter["chapter_id"], "chapterIndex": chapter["chapter_index"], "title": chapter["title"], "wordCount": chapter["word_count"], "paragraphCount": chapter["paragraph_count"]})
                rows = connection.execute("SELECT * FROM book_paragraphs WHERE chapter_id = ? ORDER BY paragraph_index", (chapter["chapter_id"],)).fetchall()
                paragraphs.extend({"paragraphId": row["paragraph_id"], "chapterId": chapter["chapter_id"], "paragraphIndex": row["paragraph_index"], "originalText": row["original_text"], "wordCount": row["word_count"], "translationText": row["translation_text"], "reviewed": bool(row["reviewed"])} for row in rows)
        project_json = {
            "projectId": project["project_id"], "title": project["title"], "authorId": project["author_id"], "author": author["name"] if author else None,
            "seriesId": project["series_id"], "series": series["name"] if series else None, "bookNumber": project["book_number"], "status": project["status"],
            "createdAt": project["created_at"], "updatedAt": project["updated_at"], "bookVersion": {"filename": book["file_name"], "checksum": book["checksum"], "analyzedAt": book["analyzed_at"]}
        }
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M")
        safe_title = "".join(character if character.isalnum() or character in "-_" else "_" for character in project["title"]).strip("_") or "book"
        filename = f"{safe_title}_{timestamp}_archive.zip"
        output = BytesIO()
        with ZipFile(output, "w", ZIP_DEFLATED) as archive:
            archive.writestr("project.json", json.dumps(project_json, ensure_ascii=False, indent=2))
            archive.writestr("source/original.epub", book["source_content"])
            archive.writestr("structure/chapters.json", json.dumps(chapters, ensure_ascii=False, indent=2))
            archive.writestr("structure/paragraphs.json", json.dumps(paragraphs, ensure_ascii=False, indent=2))
            archive.writestr("translation/translations.json", json.dumps(translations or {}, ensure_ascii=False, indent=2))
        return filename, output.getvalue()

    def update_paragraph(self, paragraph_id: str, translation_text: str | None, reviewed: bool) -> dict[str, Any] | None:
        with self.connection() as connection:
            cursor = connection.execute("UPDATE book_paragraphs SET translation_text = ?, reviewed = ? WHERE paragraph_id = ?", (translation_text, int(reviewed), paragraph_id))
            if cursor.rowcount == 0:
                return None
            row = connection.execute("SELECT * FROM book_paragraphs WHERE paragraph_id = ?", (paragraph_id,)).fetchone()
        return {"paragraphId": row["paragraph_id"], "originalText": row["original_text"], "translationText": row["translation_text"], "reviewed": bool(row["reviewed"])}

    @staticmethod
    def _project_input(data: dict[str, Any], project_id: str, created_at: str, updated_at: str, existing: dict[str, Any] | None = None) -> dict[str, Any]:
        source = existing or {}
        analysis_result = data.get("analysisResult", source.get("analysisResult"))
        return {
            "projectId": project_id,
            "title": data.get("title", source.get("title", "")),
            "authorId": data.get("authorId", source.get("authorId")),
            "seriesId": data.get("seriesId", source.get("seriesId")),
            "status": data.get("status", source.get("status", "new")),
            "fileName": data.get("fileName", source.get("fileName")),
            "fileFormat": data.get("fileFormat", source.get("fileFormat")),
            "fileSize": data.get("fileSize", source.get("fileSize")),
            "bookNumber": data.get("bookNumber", source.get("bookNumber")),
            "analysisResult": analysis_result,
            "chapterCount": data.get("chapterCount", source.get("chapterCount", 0)),
            "createdAt": created_at,
            "updatedAt": updated_at,
            "projectRuleIds": data.get("projectRuleIds", source.get("projectRuleIds", [])),
            "projectGlossaryEntryIds": data.get("projectGlossaryEntryIds", source.get("projectGlossaryEntryIds", [])),
        }

    @staticmethod
    def _write_project(connection: sqlite3.Connection, project: dict[str, Any], replace: bool) -> None:
        if not project["title"]:
            raise ValueError("Project title is required.")
        operation = "INSERT OR REPLACE" if replace else "INSERT"
        connection.execute(
            f"{operation} INTO book_projects(project_id, title, author_id, series_id, status, file_name, file_format, file_size, book_number, analysis_result, chapter_count, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (project["projectId"], project["title"], project["authorId"], project["seriesId"], project["status"], project["fileName"], project["fileFormat"], project["fileSize"], project["bookNumber"], json.dumps(project["analysisResult"], ensure_ascii=False) if project["analysisResult"] is not None else None, project["chapterCount"], project["createdAt"], project["updatedAt"]),
        )
        connection.execute("DELETE FROM project_rules WHERE project_id = ?", (project["projectId"],))
        connection.executemany(
            "INSERT INTO project_rules(project_id, rule_id) VALUES (?, ?)",
            [(project["projectId"], rule_id) for rule_id in project["projectRuleIds"]],
        )
        connection.execute("DELETE FROM project_glossary WHERE project_id = ?", (project["projectId"],))
        connection.executemany(
            "INSERT INTO project_glossary(project_id, glossary_entry_id) VALUES (?, ?)",
            [(project["projectId"], entry_id) for entry_id in project["projectGlossaryEntryIds"]],
        )

    def _project_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        project_id = row["project_id"]
        with self.connection() as connection:
            rule_rows = connection.execute("SELECT rule_id FROM project_rules WHERE project_id = ?", (project_id,)).fetchall()
            glossary_rows = connection.execute("SELECT glossary_entry_id FROM project_glossary WHERE project_id = ?", (project_id,)).fetchall()
        return {
            "projectId": project_id,
            "title": row["title"],
            "authorId": row["author_id"],
            "seriesId": row["series_id"],
            "status": row["status"],
            "fileName": row["file_name"],
            "fileFormat": row["file_format"],
            "fileSize": row["file_size"],
            "bookNumber": row["book_number"],
            "analysisResult": _json(row["analysis_result"]),
            "chapterCount": row["chapter_count"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
            "projectRuleIds": [item["rule_id"] for item in rule_rows],
            "projectGlossaryEntryIds": [item["glossary_entry_id"] for item in glossary_rows],
        }
