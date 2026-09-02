"""SQLite persistence for Translation Workbench domain entities."""

from __future__ import annotations

import base64
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

from PIL import Image, ImageOps


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
    translation_rules TEXT NOT NULL DEFAULT '',
    ai_configuration TEXT NOT NULL DEFAULT '{}',
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

CREATE TABLE IF NOT EXISTS project_translation_glossaries (
    glossary_rule_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES book_projects(project_id) ON DELETE CASCADE,
    rule_type TEXT NOT NULL DEFAULT 'glossary' CHECK(rule_type = 'glossary'),
    source_language TEXT NOT NULL,
    target_language TEXT NOT NULL,
    entries TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    current_version_id TEXT REFERENCES project_translation_glossary_versions(version_id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, source_language, target_language)
);

CREATE TABLE IF NOT EXISTS project_translation_glossary_versions (
    version_id TEXT PRIMARY KEY,
    glossary_rule_id TEXT NOT NULL REFERENCES project_translation_glossaries(glossary_rule_id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(glossary_rule_id, version_number)
);

CREATE TABLE IF NOT EXISTS project_translation_glossary_version_items (
    version_id TEXT NOT NULL REFERENCES project_translation_glossary_versions(version_id) ON DELETE CASCADE,
    glossary_entry_id TEXT NOT NULL REFERENCES glossary_entries(glossary_entry_id) ON DELETE RESTRICT,
    position INTEGER NOT NULL,
    PRIMARY KEY (version_id, glossary_entry_id),
    UNIQUE(version_id, position)
);

CREATE TABLE IF NOT EXISTS provider_glossary_sync (
    glossary_rule_id TEXT NOT NULL REFERENCES project_translation_glossaries(glossary_rule_id) ON DELETE CASCADE,
    connection_id TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    remote_glossary_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    synced_at TEXT NOT NULL,
    PRIMARY KEY (glossary_rule_id, connection_id)
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
    title TEXT,
    translation_title TEXT,
    title_reviewed INTEGER NOT NULL DEFAULT 0,
    word_count INTEGER NOT NULL DEFAULT 0,
    paragraph_count INTEGER NOT NULL DEFAULT 0,
    ai_analysis_results TEXT NOT NULL DEFAULT '{}',
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

CREATE TABLE IF NOT EXISTS book_inline_images (
    image_id TEXT PRIMARY KEY,
    book_id TEXT NOT NULL REFERENCES book_documents(book_id) ON DELETE CASCADE,
    source_path TEXT,
    mime_type TEXT NOT NULL,
    image_data BLOB NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS book_chapter_elements (
    chapter_id TEXT NOT NULL REFERENCES book_chapters(chapter_id) ON DELETE CASCADE,
    element_index INTEGER NOT NULL,
    element_type TEXT NOT NULL CHECK(element_type IN ('paragraph', 'image')),
    element_id TEXT NOT NULL,
    PRIMARY KEY (chapter_id, element_index)
);

CREATE TABLE IF NOT EXISTS project_brief_entries (
    entry_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES book_projects(project_id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    agreed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS integration_connections (
    connection_id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    credentials_ciphertext BLOB NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    test_status TEXT NOT NULL DEFAULT 'untested',
    status_code TEXT,
    status_message TEXT,
    provider_metadata TEXT,
    last_tested_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS integration_connections_provider_idx
    ON integration_connections(provider_id);
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
            if "translation_rules" not in columns:
                connection.execute("ALTER TABLE book_projects ADD COLUMN translation_rules TEXT NOT NULL DEFAULT ''")
            if "ai_configuration" not in columns:
                connection.execute("ALTER TABLE book_projects ADD COLUMN ai_configuration TEXT NOT NULL DEFAULT '{}'")
            paragraph_columns = {row["name"] for row in connection.execute("PRAGMA table_info(book_paragraphs)")}
            if "translation_text" not in paragraph_columns:
                connection.execute("ALTER TABLE book_paragraphs ADD COLUMN translation_text TEXT")
            if "reviewed" not in paragraph_columns:
                connection.execute("ALTER TABLE book_paragraphs ADD COLUMN reviewed INTEGER NOT NULL DEFAULT 0")
            book_doc_columns = {row["name"] for row in connection.execute("PRAGMA table_info(book_documents)")}
            if "cover_image" not in book_doc_columns:
                connection.execute("ALTER TABLE book_documents ADD COLUMN cover_image BLOB")
            if "cover_uploaded_by_user" not in book_doc_columns:
                connection.execute("ALTER TABLE book_documents ADD COLUMN cover_uploaded_by_user INTEGER NOT NULL DEFAULT 0")
            chapter_columns = {row["name"]: row for row in connection.execute("PRAGMA table_info(book_chapters)")}
            if chapter_columns["title"]["notnull"]:
                self._migrate_chapter_titles_nullable(connection)
                chapter_columns = {row["name"]: row for row in connection.execute("PRAGMA table_info(book_chapters)")}
            if "translation_title" not in chapter_columns:
                connection.execute("ALTER TABLE book_chapters ADD COLUMN translation_title TEXT")
            if "title_reviewed" not in chapter_columns:
                connection.execute("ALTER TABLE book_chapters ADD COLUMN title_reviewed INTEGER NOT NULL DEFAULT 0")
            if "ai_analysis_results" not in chapter_columns:
                connection.execute("ALTER TABLE book_chapters ADD COLUMN ai_analysis_results TEXT NOT NULL DEFAULT '{}'")
            translation_glossary_columns = {row["name"] for row in connection.execute("PRAGMA table_info(project_translation_glossaries)")}
            if "current_version_id" not in translation_glossary_columns:
                connection.execute("ALTER TABLE project_translation_glossaries ADD COLUMN current_version_id TEXT")
            self._migrate_translation_glossary_versions(connection)
            self._backfill_chapter_elements(connection)
            cover_rows = connection.execute("SELECT book_id, cover_image FROM book_documents WHERE cover_image IS NOT NULL").fetchall()
            for row in cover_rows:
                if self._cover_needs_normalization(row["cover_image"]):
                    connection.execute(
                        "UPDATE book_documents SET cover_image = ? WHERE book_id = ?",
                        (self._normalize_cover_image(row["cover_image"]), row["book_id"]),
                    )

    @staticmethod
    def _integration_connection(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "connectionId": row["connection_id"],
            "providerId": row["provider_id"],
            "displayName": row["display_name"],
            "enabled": _bool(row["enabled"]),
            "testStatus": row["test_status"],
            "statusCode": row["status_code"],
            "statusMessage": row["status_message"],
            "providerMetadata": _json(row["provider_metadata"]) or {},
            "lastTestedAt": row["last_tested_at"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }

    def list_integration_connections(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM integration_connections ORDER BY provider_id, display_name"
            ).fetchall()
        return [self._integration_connection(row) for row in rows]

    def get_integration_connection(self, connection_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM integration_connections WHERE connection_id = ?",
                (connection_id,),
            ).fetchone()
        return self._integration_connection(row) if row else None

    def get_integration_connection_record(self, connection_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM integration_connections WHERE connection_id = ?",
                (connection_id,),
            ).fetchone()
        if not row:
            return None
        record = self._integration_connection(row)
        record["credentialsCiphertext"] = bytes(row["credentials_ciphertext"])
        return record

    def create_integration_connection(
        self,
        provider_id: str,
        display_name: str,
        credentials_ciphertext: bytes,
    ) -> dict[str, Any]:
        connection_id = _new_id("connection")
        timestamp = _now()
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO integration_connections(connection_id, provider_id, display_name, credentials_ciphertext, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (connection_id, provider_id, display_name, credentials_ciphertext, timestamp, timestamp),
            )
        return self.get_integration_connection(connection_id)

    def update_integration_connection(
        self,
        connection_id: str,
        display_name: str,
        enabled: bool,
        credentials_ciphertext: bytes | None = None,
    ) -> dict[str, Any] | None:
        timestamp = _now()
        assignments = ["display_name = ?", "enabled = ?", "updated_at = ?"]
        values: list[Any] = [display_name, int(enabled), timestamp]
        if credentials_ciphertext is not None:
            assignments.extend([
                "credentials_ciphertext = ?",
                "test_status = 'untested'",
                "status_code = NULL",
                "status_message = NULL",
                "provider_metadata = NULL",
                "last_tested_at = NULL",
            ])
            values.append(credentials_ciphertext)
        values.append(connection_id)
        with self.connection() as connection:
            cursor = connection.execute(
                f"UPDATE integration_connections SET {', '.join(assignments)} WHERE connection_id = ?",
                values,
            )
            if cursor.rowcount == 0:
                return None
        return self.get_integration_connection(connection_id)

    def update_integration_connection_status(
        self,
        connection_id: str,
        test_status: str,
        status_code: str | None,
        status_message: str | None,
        provider_metadata: dict[str, Any],
    ) -> dict[str, Any] | None:
        timestamp = _now()
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE integration_connections SET test_status = ?, status_code = ?, status_message = ?, provider_metadata = ?, last_tested_at = ?, updated_at = ? WHERE connection_id = ?",
                (test_status, status_code, status_message, json.dumps(provider_metadata), timestamp, timestamp, connection_id),
            )
            if cursor.rowcount == 0:
                return None
        return self.get_integration_connection(connection_id)

    def delete_integration_connection(self, connection_id: str) -> bool:
        with self.connection() as connection:
            return connection.execute(
                "DELETE FROM integration_connections WHERE connection_id = ?",
                (connection_id,),
            ).rowcount > 0

    @staticmethod
    def _migrate_chapter_titles_nullable(connection: sqlite3.Connection) -> None:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("CREATE TABLE book_chapters_new (chapter_id TEXT PRIMARY KEY, book_id TEXT NOT NULL REFERENCES book_documents(book_id) ON DELETE CASCADE, chapter_index INTEGER NOT NULL, title TEXT, word_count INTEGER NOT NULL DEFAULT 0, paragraph_count INTEGER NOT NULL DEFAULT 0, UNIQUE(book_id, chapter_index))")
        connection.execute("INSERT INTO book_chapters_new(chapter_id, book_id, chapter_index, title, word_count, paragraph_count) SELECT chapter_id, book_id, chapter_index, NULLIF(title, ''), word_count, paragraph_count FROM book_chapters")
        connection.execute("DROP TABLE book_chapters")
        connection.execute("ALTER TABLE book_chapters_new RENAME TO book_chapters")
        connection.execute("PRAGMA foreign_keys = ON")

    @staticmethod
    def _normalize_inline_image(image_data: bytes) -> tuple[bytes, int, int]:
        try:
            with Image.open(BytesIO(image_data)) as image:
                normalized = ImageOps.exif_transpose(image).convert("RGBA")
                normalized.thumbnail((800, 800), Image.Resampling.LANCZOS)
                output = BytesIO()
                normalized.save(output, format="WEBP", quality=78, method=6)
                return output.getvalue(), normalized.width, normalized.height
        except (Image.UnidentifiedImageError, OSError) as error:
            raise ValueError("Некоректне зображення всередині EPUB.") from error

    @staticmethod
    def _backfill_chapter_elements(connection: sqlite3.Connection) -> None:
        chapters = connection.execute("SELECT chapter_id FROM book_chapters").fetchall()
        for chapter in chapters:
            existing = connection.execute("SELECT 1 FROM book_chapter_elements WHERE chapter_id = ?", (chapter["chapter_id"],)).fetchone()
            if existing:
                continue
            rows = connection.execute("SELECT paragraph_id FROM book_paragraphs WHERE chapter_id = ? ORDER BY paragraph_index", (chapter["chapter_id"],)).fetchall()
            connection.executemany(
                "INSERT INTO book_chapter_elements(chapter_id, element_index, element_type, element_id) VALUES (?, ?, 'paragraph', ?)",
                [(chapter["chapter_id"], index, row["paragraph_id"]) for index, row in enumerate(rows)],
            )

    @staticmethod
    def _translation_glossary_content_hash(source_language: str, target_language: str, entries: list[dict[str, str]]) -> str:
        payload = {
            "sourceLanguage": source_language,
            "targetLanguage": target_language,
            "entries": [{"source": item["source"], "target": item["target"]} for item in entries],
        }
        return hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _resolve_or_create_glossary_item(connection: sqlite3.Connection, source: str, target: str, context: str) -> str:
        row = connection.execute(
            "SELECT glossary_entry_id FROM glossary_entries "
            "WHERE source = ? AND target = ? AND COALESCE(note, '') = ? "
            "ORDER BY updated_at ASC, glossary_entry_id ASC LIMIT 1",
            (source, target, context),
        ).fetchone()
        if row:
            return row["glossary_entry_id"]

        glossary_entry_id = _new_id("glossary")
        connection.execute(
            "INSERT INTO glossary_entries(glossary_entry_id, source, target, note, active, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (glossary_entry_id, source, target, context, 1, _now()),
        )
        return glossary_entry_id

    def _migrate_translation_glossary_versions(self, connection: sqlite3.Connection) -> None:
        rows = connection.execute(
            "SELECT glossary_rule_id, source_language, target_language, entries, content_hash, created_at, current_version_id "
            "FROM project_translation_glossaries ORDER BY created_at"
        ).fetchall()

        for row in rows:
            current_version_id = row["current_version_id"]
            if current_version_id:
                current = connection.execute(
                    "SELECT 1 FROM project_translation_glossary_versions WHERE version_id = ?",
                    (current_version_id,),
                ).fetchone()
                if current:
                    continue

            try:
                legacy_entries = json.loads(row["entries"])
            except (TypeError, json.JSONDecodeError):
                legacy_entries = []
            if not isinstance(legacy_entries, list):
                legacy_entries = []

            normalized_entries: list[dict[str, str]] = []
            item_ids: list[str] = []
            for item in legacy_entries:
                if not isinstance(item, dict):
                    continue
                source = str(item.get("source", "")).strip()
                target = str(item.get("target", "")).strip()
                context = str(item.get("context", "")).strip()
                if not source or not target:
                    continue
                glossary_entry_id = self._resolve_or_create_glossary_item(connection, source, target, context)
                normalized_entries.append({"source": source, "target": target, "context": context})
                item_ids.append(glossary_entry_id)

            rebuilt_hash = self._translation_glossary_content_hash(
                row["source_language"],
                row["target_language"],
                normalized_entries,
            )
            if rebuilt_hash != row["content_hash"]:
                raise RuntimeError(
                    f"Glossary hash mismatch during migration for {row['glossary_rule_id']}: "
                    f"stored={row['content_hash']} rebuilt={rebuilt_hash}"
                )

            existing_match = connection.execute(
                "SELECT version_id FROM project_translation_glossary_versions "
                "WHERE glossary_rule_id = ? AND content_hash = ? ORDER BY version_number ASC LIMIT 1",
                (row["glossary_rule_id"], row["content_hash"]),
            ).fetchone()
            if existing_match:
                version_id = existing_match["version_id"]
            else:
                max_row = connection.execute(
                    "SELECT COALESCE(MAX(version_number), 0) AS max_version FROM project_translation_glossary_versions WHERE glossary_rule_id = ?",
                    (row["glossary_rule_id"],),
                ).fetchone()
                version_id = _new_id("translation-glossary-version")
                connection.execute(
                    "INSERT INTO project_translation_glossary_versions(version_id, glossary_rule_id, version_number, content_hash, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        version_id,
                        row["glossary_rule_id"],
                        int(max_row["max_version"]) + 1,
                        row["content_hash"],
                        row["created_at"],
                    ),
                )

            existing_items = connection.execute(
                "SELECT 1 FROM project_translation_glossary_version_items WHERE version_id = ? LIMIT 1",
                (version_id,),
            ).fetchone()
            if not existing_items:
                for position, glossary_entry_id in enumerate(item_ids):
                    connection.execute(
                        "INSERT INTO project_translation_glossary_version_items(version_id, glossary_entry_id, position) VALUES (?, ?, ?)",
                        (version_id, glossary_entry_id, position),
                    )

            connection.execute(
                "UPDATE project_translation_glossaries SET current_version_id = ? WHERE glossary_rule_id = ?",
                (version_id, row["glossary_rule_id"]),
            )

    @staticmethod
    def _cover_needs_normalization(image_data: bytes) -> bool:
        with Image.open(BytesIO(image_data)) as image:
            return image.format != "WEBP" or image.width > 400 or image.height > 600

    @staticmethod
    def _normalize_cover_image(image_data: bytes) -> bytes:
        try:
            with Image.open(BytesIO(image_data)) as image:
                normalized = ImageOps.exif_transpose(image).convert("RGBA")
                normalized.thumbnail((400, 600), Image.Resampling.LANCZOS)
                output = BytesIO()
                normalized.save(output, format="WEBP", quality=82, method=6)
                return output.getvalue()
        except (Image.UnidentifiedImageError, OSError) as error:
            raise ValueError("Підтримуються коректні зображення JPEG, PNG, GIF або WebP.") from error

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
            rows = connection.execute(
                "SELECT project_id, title, author_id, series_id, status "
                "FROM book_projects ORDER BY created_at"
            ).fetchall()
        return [self._project_summary_from_row(row) for row in rows]

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

    def update_project_translation_rules(self, project_id: str, translation_rules: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE book_projects SET translation_rules = ?, updated_at = ? WHERE project_id = ?",
                (translation_rules, _now(), project_id),
            )
            if cursor.rowcount == 0:
                return None
        return self.get_project(project_id)

    def list_project_translation_glossaries(self, project_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM project_translation_glossaries WHERE project_id = ? ORDER BY created_at",
                (project_id,),
            ).fetchall()
            sync_rows = connection.execute(
                "SELECT sync.* FROM provider_glossary_sync sync "
                "JOIN project_translation_glossaries glossary ON glossary.glossary_rule_id = sync.glossary_rule_id "
                "WHERE glossary.project_id = ?",
                (project_id,),
            ).fetchall()
        sync_by_rule = {row["glossary_rule_id"]: row for row in sync_rows}
        return [self._translation_glossary(row, sync_by_rule.get(row["glossary_rule_id"])) for row in rows]

    def get_project_translation_glossary(self, glossary_rule_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM project_translation_glossaries WHERE glossary_rule_id = ?",
                (glossary_rule_id,),
            ).fetchone()
            sync = connection.execute(
                "SELECT * FROM provider_glossary_sync WHERE glossary_rule_id = ?",
                (glossary_rule_id,),
            ).fetchone()
        return self._translation_glossary(row, sync) if row else None

    def get_or_create_project_translation_glossary(
        self,
        project_id: str,
        source_language: str,
        target_language: str,
        glossary_rule_id: str | None = None,
    ) -> dict[str, Any]:
        source = source_language.strip().upper()
        target = target_language.strip().upper()
        if not source or not target:
            raise ValueError("Вкажіть мови глосарію.")

        with self.connection() as connection:
            project = connection.execute(
                "SELECT 1 FROM book_projects WHERE project_id = ?",
                (project_id,),
            ).fetchone()
            if project is None:
                raise ValueError("Project not found.")

            row = None
            if glossary_rule_id:
                row = connection.execute(
                    "SELECT * FROM project_translation_glossaries WHERE glossary_rule_id = ? AND project_id = ?",
                    (glossary_rule_id, project_id),
                ).fetchone()
            if row is None:
                row = connection.execute(
                    "SELECT * FROM project_translation_glossaries WHERE project_id = ? AND source_language = ? AND target_language = ?",
                    (project_id, source, target),
                ).fetchone()

            if row is None:
                timestamp = _now()
                resolved_glossary_rule_id = glossary_rule_id or _new_id("translation-glossary")
                empty_hash = self._translation_glossary_content_hash(source, target, [])
                connection.execute(
                    "INSERT INTO project_translation_glossaries(glossary_rule_id, project_id, source_language, target_language, entries, content_hash, current_version_id, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?)",
                    (
                        resolved_glossary_rule_id,
                        project_id,
                        source,
                        target,
                        json.dumps([], ensure_ascii=False),
                        empty_hash,
                        timestamp,
                        timestamp,
                    ),
                )
                row = connection.execute(
                    "SELECT * FROM project_translation_glossaries WHERE glossary_rule_id = ?",
                    (resolved_glossary_rule_id,),
                ).fetchone()

            sync = connection.execute(
                "SELECT * FROM provider_glossary_sync WHERE glossary_rule_id = ?",
                (row["glossary_rule_id"],),
            ).fetchone()

        return self._translation_glossary(row, sync)

    def get_translation_glossary_current_version(self, glossary_rule_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            glossary = connection.execute(
                "SELECT * FROM project_translation_glossaries WHERE glossary_rule_id = ?",
                (glossary_rule_id,),
            ).fetchone()
            if glossary is None or not glossary["current_version_id"]:
                return None
            version = connection.execute(
                "SELECT * FROM project_translation_glossary_versions WHERE version_id = ?",
                (glossary["current_version_id"],),
            ).fetchone()
            if version is None:
                return None
            item_rows = connection.execute(
                "SELECT glossary_entry_id FROM project_translation_glossary_version_items WHERE version_id = ? ORDER BY position",
                (version["version_id"],),
            ).fetchall()
        return {
            "glossaryRuleId": glossary["glossary_rule_id"],
            "projectId": glossary["project_id"],
            "sourceLanguage": glossary["source_language"],
            "targetLanguage": glossary["target_language"],
            "versionId": version["version_id"],
            "versionNumber": version["version_number"],
            "contentHash": version["content_hash"],
            "createdAt": version["created_at"],
            "glossaryEntryIds": [row["glossary_entry_id"] for row in item_rows],
        }

    def materialize_translation_glossary_version(self, version_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            version = connection.execute(
                "SELECT version.*, glossary.source_language, glossary.target_language, glossary.project_id "
                "FROM project_translation_glossary_versions version "
                "JOIN project_translation_glossaries glossary ON glossary.glossary_rule_id = version.glossary_rule_id "
                "WHERE version.version_id = ?",
                (version_id,),
            ).fetchone()
            if version is None:
                return None
            item_rows = connection.execute(
                "SELECT glossary_entry_id FROM project_translation_glossary_version_items WHERE version_id = ? ORDER BY position",
                (version_id,),
            ).fetchall()
            item_ids = [row["glossary_entry_id"] for row in item_rows]
            entries = self._materialize_glossary_entries(connection, item_ids)
            rebuilt_hash = self._translation_glossary_content_hash(
                version["source_language"],
                version["target_language"],
                entries,
            )
        return {
            "versionId": version["version_id"],
            "glossaryRuleId": version["glossary_rule_id"],
            "projectId": version["project_id"],
            "versionNumber": version["version_number"],
            "sourceLanguage": version["source_language"],
            "targetLanguage": version["target_language"],
            "contentHash": version["content_hash"],
            "materializedContentHash": rebuilt_hash,
            "glossaryEntryIds": item_ids,
            "entries": entries,
            "createdAt": version["created_at"],
        }

    def commit_translation_glossary_version(self, glossary_rule_id: str, glossary_entry_ids: list[str]) -> dict[str, Any]:
        if not isinstance(glossary_entry_ids, list) or not glossary_entry_ids:
            raise ValueError("Вкажіть щонайменше один GlossaryItem.")
        if not all(isinstance(item_id, str) and item_id.strip() for item_id in glossary_entry_ids):
            raise ValueError("Некоректний glossary_entry_id.")
        normalized_ids = [item_id.strip() for item_id in glossary_entry_ids]
        if len(set(normalized_ids)) != len(normalized_ids):
            raise ValueError("GlossaryItem не повинні дублюватися у версії.")

        with self.connection() as connection:
            glossary = connection.execute(
                "SELECT * FROM project_translation_glossaries WHERE glossary_rule_id = ?",
                (glossary_rule_id,),
            ).fetchone()
            if glossary is None:
                raise ValueError("Glossary not found.")

            current_ids: list[str] = []
            current_version_id = glossary["current_version_id"]
            if current_version_id:
                current_rows = connection.execute(
                    "SELECT glossary_entry_id FROM project_translation_glossary_version_items WHERE version_id = ? ORDER BY position",
                    (current_version_id,),
                ).fetchall()
                current_ids = [row["glossary_entry_id"] for row in current_rows]

            if current_ids == normalized_ids:
                current = self.get_translation_glossary_current_version(glossary_rule_id)
                if current is None:
                    raise ValueError("Current glossary version is unavailable.")
                return {**current, "createdNewVersion": False}

            materialized_entries = self._materialize_glossary_entries(connection, normalized_ids)
            content_hash = self._translation_glossary_content_hash(
                glossary["source_language"],
                glossary["target_language"],
                materialized_entries,
            )

            max_version = connection.execute(
                "SELECT COALESCE(MAX(version_number), 0) AS max_version FROM project_translation_glossary_versions WHERE glossary_rule_id = ?",
                (glossary_rule_id,),
            ).fetchone()["max_version"]
            version_id = _new_id("translation-glossary-version")
            version_number = int(max_version) + 1
            timestamp = _now()

            connection.execute(
                "INSERT INTO project_translation_glossary_versions(version_id, glossary_rule_id, version_number, content_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                (version_id, glossary_rule_id, version_number, content_hash, timestamp),
            )
            connection.executemany(
                "INSERT INTO project_translation_glossary_version_items(version_id, glossary_entry_id, position) VALUES (?, ?, ?)",
                [(version_id, item_id, position) for position, item_id in enumerate(normalized_ids)],
            )
            connection.execute(
                "UPDATE project_translation_glossaries SET current_version_id = ?, entries = ?, content_hash = ?, updated_at = ? WHERE glossary_rule_id = ?",
                (
                    version_id,
                    json.dumps(materialized_entries, ensure_ascii=False),
                    content_hash,
                    timestamp,
                    glossary_rule_id,
                ),
            )

        created = self.get_translation_glossary_current_version(glossary_rule_id)
        if created is None:
            raise ValueError("Failed to load created glossary version.")
        return {**created, "createdNewVersion": True}

    @staticmethod
    def _materialize_glossary_entries(connection: sqlite3.Connection, glossary_entry_ids: list[str]) -> list[dict[str, str]]:
        entries: list[dict[str, str]] = []
        for glossary_entry_id in glossary_entry_ids:
            row = connection.execute(
                "SELECT source, target, note FROM glossary_entries WHERE glossary_entry_id = ?",
                (glossary_entry_id,),
            ).fetchone()
            if row is None:
                raise ValueError(f"GlossaryItem not found: {glossary_entry_id}")
            entries.append({
                "source": row["source"],
                "target": row["target"],
                "context": row["note"] or "",
            })
        return entries

    def upsert_project_translation_glossary(self, project_id: str, data: dict[str, Any]) -> dict[str, Any]:
        timestamp = _now()
        with self.connection() as connection:
            matching_pair = connection.execute(
                "SELECT glossary_rule_id FROM project_translation_glossaries WHERE project_id = ? AND source_language = ? AND target_language = ?",
                (project_id, data["sourceLanguage"], data["targetLanguage"]),
            ).fetchone()
            glossary_rule_id = data.get("glossaryRuleId") or (matching_pair["glossary_rule_id"] if matching_pair else _new_id("translation-glossary"))
            existing = connection.execute(
                "SELECT created_at FROM project_translation_glossaries WHERE glossary_rule_id = ?",
                (glossary_rule_id,),
            ).fetchone()
            connection.execute(
                "INSERT INTO project_translation_glossaries(glossary_rule_id, project_id, source_language, target_language, entries, content_hash, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(glossary_rule_id) DO UPDATE SET source_language = excluded.source_language, target_language = excluded.target_language, entries = excluded.entries, content_hash = excluded.content_hash, updated_at = excluded.updated_at",
                (
                    glossary_rule_id,
                    project_id,
                    data["sourceLanguage"],
                    data["targetLanguage"],
                    json.dumps(data["entries"], ensure_ascii=False),
                    data["contentHash"],
                    existing["created_at"] if existing else timestamp,
                    timestamp,
                ),
            )
        return self.get_project_translation_glossary(glossary_rule_id)

    def save_provider_glossary_sync(self, glossary_rule_id: str, connection_id: str, provider_id: str, remote_glossary_id: str, content_hash: str) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO provider_glossary_sync(glossary_rule_id, connection_id, provider_id, remote_glossary_id, content_hash, synced_at) "
                "VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(glossary_rule_id, connection_id) DO UPDATE SET provider_id = excluded.provider_id, remote_glossary_id = excluded.remote_glossary_id, content_hash = excluded.content_hash, synced_at = excluded.synced_at",
                (glossary_rule_id, connection_id, provider_id, remote_glossary_id, content_hash, _now()),
            )

    def delete_provider_glossary_sync(self, glossary_rule_id: str, connection_id: str) -> bool:
        with self.connection() as connection:
            return connection.execute(
                "DELETE FROM provider_glossary_sync WHERE glossary_rule_id = ? AND connection_id = ?",
                (glossary_rule_id, connection_id),
            ).rowcount > 0

    def resolve_glossary_item_ids(self, entries: list[dict[str, str]]) -> list[str]:
        item_ids: list[str] = []
        with self.connection() as connection:
            for entry in entries:
                source = str(entry.get("source", "")).strip()
                target = str(entry.get("target", "")).strip()
                context = str(entry.get("context", "")).strip()
                if not source or not target:
                    raise ValueError("Оригінал і переклад терміна обов’язкові.")
                item_ids.append(self._resolve_or_create_glossary_item(connection, source, target, context))
        return item_ids

    def find_synced_project_glossary(self, project_id: str, connection_id: str, target_language: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT glossary.*, sync.remote_glossary_id, sync.provider_id, sync.synced_at, sync.content_hash "
                "FROM project_translation_glossaries glossary "
                "JOIN provider_glossary_sync sync ON sync.glossary_rule_id = glossary.glossary_rule_id "
                "WHERE glossary.project_id = ? AND sync.connection_id = ? AND glossary.target_language = ? AND sync.content_hash = glossary.content_hash "
                "ORDER BY glossary.updated_at DESC LIMIT 1",
                (project_id, connection_id, target_language),
            ).fetchone()
        return self._translation_glossary(row, row) if row else None

    @staticmethod
    def _translation_glossary(row: sqlite3.Row, sync: sqlite3.Row | None) -> dict[str, Any]:
        sync_state = "unsynced"
        synced_content_hash = None
        if sync:
            synced_content_hash = sync["content_hash"] if "content_hash" in sync.keys() else row["content_hash"]
            sync_state = "synced" if synced_content_hash == row["content_hash"] else "stale"
        result = {
            "glossaryRuleId": row["glossary_rule_id"],
            "projectId": row["project_id"],
            "type": row["rule_type"],
            "sourceLanguage": row["source_language"],
            "targetLanguage": row["target_language"],
            "entries": json.loads(row["entries"]),
            "contentHash": row["content_hash"],
            "currentVersionId": row["current_version_id"] if "current_version_id" in row.keys() else None,
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
            "syncState": sync_state,
            "providerSync": None,
        }
        if sync:
            result["providerSync"] = {
                "providerId": sync["provider_id"],
                "remoteGlossaryId": sync["remote_glossary_id"],
                "syncedAt": sync["synced_at"],
                "contentHash": synced_content_hash,
                "isCurrent": sync_state == "synced",
            }
        return result

    def delete_project(self, project_id: str) -> bool:
        with self.connection() as connection:
            connection.execute("DELETE FROM book_documents WHERE project_id = ?", (project_id,))
            return connection.execute("DELETE FROM book_projects WHERE project_id = ?", (project_id,)).rowcount > 0

    def save_book_structure(self, project_id: str, filename: str, mime_type: str, content: bytes, analysis: dict[str, Any]) -> dict[str, Any]:
        timestamp = _now()
        book_id = _new_id("book")
        checksum = hashlib.sha256(content).hexdigest()
        chapters = analysis.get("chapters", [])

        cover_image = None
        cover_image_base64 = analysis.get("coverImage")
        if cover_image_base64:
            try:
                cover_image = self._normalize_cover_image(base64.b64decode(cover_image_base64))
            except (ValueError, base64.binascii.Error):
                cover_image = None

        with self.connection() as connection:
            project = connection.execute("SELECT project_id FROM book_projects WHERE project_id = ?", (project_id,)).fetchone()
            if project is None:
                raise ValueError("BookProject not found.")

            existing_book = connection.execute(
                "SELECT cover_image, cover_uploaded_by_user FROM book_documents WHERE project_id = ?",
                (project_id,),
            ).fetchone()
            if existing_book and existing_book["cover_uploaded_by_user"]:
                cover_image = existing_book["cover_image"]
                cover_uploaded_by_user = 1
            else:
                cover_uploaded_by_user = 0

            connection.execute("DELETE FROM book_documents WHERE project_id = ?", (project_id,))
            connection.execute(
                "INSERT INTO book_documents(book_id, project_id, file_name, mime_type, file_size, checksum, source_content, title, author, language, word_count, chapter_count, analysis_status, analyzed_at, created_at, updated_at, cover_image, cover_uploaded_by_user) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (book_id, project_id, filename, mime_type, len(content), checksum, content, analysis.get("title"), analysis.get("author"), analysis.get("language"), analysis.get("wordCount", 0), len(chapters), "completed", timestamp, timestamp, timestamp, cover_image, cover_uploaded_by_user),
            )
            for chapter_index, chapter in enumerate(chapters, 1):
                chapter_id = _new_id("chapter")
                elements = chapter.get("elements", [])
                paragraphs = [element for element in elements if element.get("type") == "paragraph"]
                connection.execute(
                    "INSERT INTO book_chapters(chapter_id, book_id, chapter_index, title, word_count, paragraph_count) VALUES (?, ?, ?, ?, ?, ?)",
                    (chapter_id, book_id, chapter_index, chapter.get("title"), chapter.get("wordCount", 0), len(paragraphs)),
                )
                for element_index, element in enumerate(elements):
                    if element.get("type") == "paragraph":
                        paragraph_id = _new_id("paragraph")
                        text = element.get("text") or ""
                        connection.execute(
                            "INSERT INTO book_paragraphs(paragraph_id, chapter_id, paragraph_index, original_text, word_count) VALUES (?, ?, ?, ?, ?)",
                            (paragraph_id, chapter_id, element_index, text, len(text.split())),
                        )
                        connection.execute(
                            "INSERT INTO book_chapter_elements(chapter_id, element_index, element_type, element_id) VALUES (?, ?, 'paragraph', ?)",
                            (chapter_id, element_index, paragraph_id),
                        )
                    elif element.get("type") == "image" and element.get("imageData"):
                        image_id = _new_id("inline-image")
                        image_data, width, height = self._normalize_inline_image(base64.b64decode(element["imageData"]))
                        connection.execute(
                            "INSERT INTO book_inline_images(image_id, book_id, source_path, mime_type, image_data, width, height) VALUES (?, ?, ?, 'image/webp', ?, ?, ?)",
                            (image_id, book_id, element.get("source"), image_data, width, height),
                        )
                        connection.execute(
                            "INSERT INTO book_chapter_elements(chapter_id, element_index, element_type, element_id) VALUES (?, ?, 'image', ?)",
                            (chapter_id, element_index, image_id),
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
                elements = []
                element_rows = connection.execute("SELECT * FROM book_chapter_elements WHERE chapter_id = ? ORDER BY element_index", (chapter["chapter_id"],)).fetchall()
                for element in element_rows:
                    if element["element_type"] == "paragraph":
                        row = connection.execute("SELECT paragraph_id, original_text, translation_text, reviewed FROM book_paragraphs WHERE paragraph_id = ?", (element["element_id"],)).fetchone()
                        if row:
                            paragraph_count += 1
                            elements.append({"type": "paragraph", "paragraphId": row["paragraph_id"], "originalText": row["original_text"], "translationText": row["translation_text"], "reviewed": bool(row["reviewed"])})
                    else:
                        row = connection.execute("SELECT image_id, width, height FROM book_inline_images WHERE image_id = ?", (element["element_id"],)).fetchone()
                        if row:
                            elements.append({"type": "image", "imageId": row["image_id"], "width": row["width"], "height": row["height"]})
                chapters.append({
                    "chapterId": chapter["chapter_id"],
                    "title": chapter["title"], "translationTitle": chapter["translation_title"], "titleReviewed": bool(chapter["title_reviewed"]),
                    "wordCount": chapter["word_count"],
                    "aiAnalysisResults": _json(chapter["ai_analysis_results"]) or {},
                    "elements": elements,
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

    def get_paragraph(self, paragraph_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM book_paragraphs WHERE paragraph_id = ?", (paragraph_id,)).fetchone()
        if row is None:
            return None
        return {"paragraphId": row["paragraph_id"], "originalText": row["original_text"], "translationText": row["translation_text"], "reviewed": bool(row["reviewed"])}

    def get_translation_rules_for_paragraph(self, paragraph_id: str) -> str:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT project.translation_rules FROM book_paragraphs paragraph "
                "JOIN book_chapters chapter ON chapter.chapter_id = paragraph.chapter_id "
                "JOIN book_documents book ON book.book_id = chapter.book_id "
                "JOIN book_projects project ON project.project_id = book.project_id "
                "WHERE paragraph.paragraph_id = ?",
                (paragraph_id,),
            ).fetchone()
        return row["translation_rules"] if row else ""

    def get_project_id_for_paragraph(self, paragraph_id: str) -> str | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT book.project_id FROM book_paragraphs paragraph "
                "JOIN book_chapters chapter ON chapter.chapter_id = paragraph.chapter_id "
                "JOIN book_documents book ON book.book_id = chapter.book_id "
                "WHERE paragraph.paragraph_id = ?",
                (paragraph_id,),
            ).fetchone()
        return row["project_id"] if row else None

    def get_chapter(self, chapter_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM book_chapters WHERE chapter_id = ?", (chapter_id,)).fetchone()
        if row is None:
            return None
        return {
            "chapterId": row["chapter_id"],
            "bookId": row["book_id"],
            "title": row["title"],
            "aiAnalysisResults": _json(row["ai_analysis_results"]) or {},
        }

    def save_chapter_ai_analysis(self, chapter_id: str, provider_id: str, result: dict[str, Any]) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT ai_analysis_results FROM book_chapters WHERE chapter_id = ?", (chapter_id,)).fetchone()
            if row is None:
                return None
            results = _json(row["ai_analysis_results"]) or {}
            results[provider_id] = result
            connection.execute(
                "UPDATE book_chapters SET ai_analysis_results = ? WHERE chapter_id = ?",
                (json.dumps(results, ensure_ascii=False), chapter_id),
            )
        return self.get_chapter(chapter_id)

    def update_chapter_title(self, chapter_id: str, translation_title: str | None, reviewed: bool) -> dict[str, Any] | None:
        with self.connection() as connection:
            cursor = connection.execute("UPDATE book_chapters SET translation_title = ?, title_reviewed = ? WHERE chapter_id = ? AND title IS NOT NULL", (translation_title, int(reviewed), chapter_id))
            if cursor.rowcount == 0:
                return None
            row = connection.execute("SELECT chapter_id, title, translation_title, title_reviewed FROM book_chapters WHERE chapter_id = ?", (chapter_id,)).fetchone()
        return {"chapterId": row["chapter_id"], "title": row["title"], "translationTitle": row["translation_title"], "titleReviewed": bool(row["title_reviewed"])}

    def get_inline_image(self, image_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT image_data, mime_type FROM book_inline_images WHERE image_id = ?", (image_id,)).fetchone()
        return {"data": row["image_data"], "mimeType": row["mime_type"]} if row else None

    def list_project_brief_entries(self, project_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM project_brief_entries WHERE project_id = ? ORDER BY created_at",
                (project_id,),
            ).fetchall()
        return [self._brief_entry_from_row(row) for row in rows]

    def create_project_brief_entry(self, project_id: str, data: dict[str, Any]) -> dict[str, Any]:
        text = str(data.get("text", "")).strip()
        if not text:
            raise ValueError("Текст повідомлення є обов'язковим.")
        timestamp = _now()
        entry_id = _new_id("brief")
        with self.connection() as connection:
            project = connection.execute("SELECT project_id FROM book_projects WHERE project_id = ?", (project_id,)).fetchone()
            if project is None:
                raise ValueError("BookProject not found.")
            connection.execute(
                "INSERT INTO project_brief_entries(entry_id, project_id, text, agreed, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (entry_id, project_id, text, 0, timestamp, timestamp),
            )
            row = connection.execute("SELECT * FROM project_brief_entries WHERE entry_id = ?", (entry_id,)).fetchone()
        return self._brief_entry_from_row(row)

    def update_project_brief_entry(self, entry_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        with self.connection() as connection:
            existing = connection.execute("SELECT * FROM project_brief_entries WHERE entry_id = ?", (entry_id,)).fetchone()
            if existing is None:
                return None
            text = str(data.get("text", existing["text"])).strip()
            if not text:
                raise ValueError("Текст повідомлення є обов'язковим.")
            agreed = bool(data.get("agreed", _bool(existing["agreed"])))
            timestamp = _now()
            connection.execute(
                "UPDATE project_brief_entries SET text = ?, agreed = ?, updated_at = ? WHERE entry_id = ?",
                (text, int(agreed), timestamp, entry_id),
            )
            row = connection.execute("SELECT * FROM project_brief_entries WHERE entry_id = ?", (entry_id,)).fetchone()
        return self._brief_entry_from_row(row)

    @staticmethod
    def _brief_entry_from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "entryId": row["entry_id"],
            "projectId": row["project_id"],
            "text": row["text"],
            "agreed": _bool(row["agreed"]),
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }

    @staticmethod
    def _project_summary_from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "projectId": row["project_id"],
            "title": row["title"],
            "authorId": row["author_id"],
            "seriesId": row["series_id"],
            "status": row["status"],
        }

    @staticmethod
    def _project_input(data: dict[str, Any], project_id: str, created_at: str, updated_at: str, existing: dict[str, Any] | None = None) -> dict[str, Any]:
        source = existing or {}
        analysis_result = data.get("analysisResult", source.get("analysisResult"))
        ai_configuration = data.get("aiConfiguration", source.get("aiConfiguration", {}))
        if not isinstance(ai_configuration, dict):
            raise ValueError("AI configuration must be an object.")
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
            "translationRules": str(data.get("translationRules", source.get("translationRules", ""))),
            "aiConfiguration": ai_configuration,
            "chapterCount": data.get("chapterCount", source.get("chapterCount", 0)),
            "createdAt": created_at,
            "updatedAt": updated_at,
            "projectRuleIds": data.get("projectRuleIds", source.get("projectRuleIds", [])),
            "projectGlossaryEntryIds": data.get("projectGlossaryEntryIds", source.get("projectGlossaryEntryIds", [])),
            "inheritedRules": data.get("inheritedRules", source.get("inheritedRules", [])),
            "inheritedGlossary": data.get("inheritedGlossary", source.get("inheritedGlossary", [])),
        }

    @staticmethod
    def _write_project(connection: sqlite3.Connection, project: dict[str, Any], replace: bool) -> None:
        if not project["title"]:
            raise ValueError("Project title is required.")
        operation = "INSERT OR REPLACE" if replace else "INSERT"
        connection.execute(
            f"{operation} INTO book_projects(project_id, title, author_id, series_id, status, file_name, file_format, file_size, book_number, analysis_result, translation_rules, ai_configuration, chapter_count, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (project["projectId"], project["title"], project["authorId"], project["seriesId"], project["status"], project["fileName"], project["fileFormat"], project["fileSize"], project["bookNumber"], json.dumps(project["analysisResult"], ensure_ascii=False) if project["analysisResult"] is not None else None, project["translationRules"], json.dumps(project["aiConfiguration"], ensure_ascii=False), project["chapterCount"], project["createdAt"], project["updatedAt"]),
        )
        connection.execute("DELETE FROM project_rules WHERE project_id = ?", (project["projectId"],))
        inherited_rule_ids = {item["ruleId"] for item in project["inheritedRules"]}
        connection.executemany(
            "INSERT INTO project_rules(project_id, rule_id) VALUES (?, ?)",
            [(project["projectId"], rule_id) for rule_id in project["projectRuleIds"] if rule_id not in inherited_rule_ids],
        )
        connection.executemany(
            "INSERT INTO project_rules(project_id, rule_id, inherited, confirmed, confirmed_at) VALUES (?, ?, 1, ?, ?)",
            [
                (project["projectId"], item["ruleId"], int(bool(item.get("confirmed"))), item.get("confirmedAt"))
                for item in project["inheritedRules"]
            ],
        )
        connection.execute("DELETE FROM project_glossary WHERE project_id = ?", (project["projectId"],))
        inherited_glossary_ids = {item["glossaryEntryId"] for item in project["inheritedGlossary"]}
        connection.executemany(
            "INSERT INTO project_glossary(project_id, glossary_entry_id) VALUES (?, ?)",
            [(project["projectId"], entry_id) for entry_id in project["projectGlossaryEntryIds"] if entry_id not in inherited_glossary_ids],
        )
        connection.executemany(
            "INSERT INTO project_glossary(project_id, glossary_entry_id, inherited, confirmed, confirmed_at) VALUES (?, ?, 1, ?, ?)",
            [
                (project["projectId"], item["glossaryEntryId"], int(bool(item.get("confirmed"))), item.get("confirmedAt"))
                for item in project["inheritedGlossary"]
            ],
        )

    def _project_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        project_id = row["project_id"]
        with self.connection() as connection:
            rule_rows = connection.execute("SELECT rule_id, inherited, confirmed, confirmed_at FROM project_rules WHERE project_id = ?", (project_id,)).fetchall()
            glossary_rows = connection.execute("SELECT glossary_entry_id, inherited, confirmed, confirmed_at FROM project_glossary WHERE project_id = ?", (project_id,)).fetchall()
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
            "translationRules": row["translation_rules"],
            "aiConfiguration": _json(row["ai_configuration"]) or {},
            "chapterCount": row["chapter_count"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
            "projectRuleIds": [item["rule_id"] for item in rule_rows if not _bool(item["inherited"])],
            "projectGlossaryEntryIds": [item["glossary_entry_id"] for item in glossary_rows if not _bool(item["inherited"])],
            "inheritedRules": [
                {"ruleId": item["rule_id"], "confirmed": _bool(item["confirmed"]), "confirmedAt": item["confirmed_at"]}
                for item in rule_rows if _bool(item["inherited"])
            ],
            "inheritedGlossary": [
                {"glossaryEntryId": item["glossary_entry_id"], "confirmed": _bool(item["confirmed"]), "confirmedAt": item["confirmed_at"]}
                for item in glossary_rows if _bool(item["inherited"])
            ],
        }

    def get_project_cover(self, project_id: str) -> bytes | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT cover_image FROM book_documents WHERE project_id = ?",
                (project_id,)
            ).fetchone()
        return row["cover_image"] if row and row["cover_image"] else None

    def set_project_cover(self, project_id: str, image_data: bytes) -> bool:
        timestamp = _now()
        normalized_cover = self._normalize_cover_image(image_data)
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE book_documents SET cover_image = ?, cover_uploaded_by_user = 1, updated_at = ? WHERE project_id = ?",
                (normalized_cover, timestamp, project_id),
            )
            return cursor.rowcount > 0

    def clear_project_cover(self, project_id: str) -> bool:
        timestamp = _now()
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE book_documents SET cover_image = NULL, cover_uploaded_by_user = 0, updated_at = ? WHERE project_id = ?",
                (timestamp, project_id),
            )
            return cursor.rowcount > 0
