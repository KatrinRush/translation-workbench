"""SQLite persistence for Translation Workbench domain entities."""

from __future__ import annotations

import base64
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import sqlite3
from zipfile import ZIP_DEFLATED, ZipFile
from typing import Any, Iterator, Mapping
from uuid import uuid4

from PIL import Image, ImageOps

from .text_replace import MAX_QUERY_CHARS, MAX_REPLACEMENT_CHARS, MODES as REPLACE_MODES, Matcher, context as replace_context
from .usage import (
    DEFAULT_MODEL_PRICES, DEFAULT_TIMEZONE, PRICE_KEYS, resolve_timezone, row_from_record as usage_row_from_record,
)


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parent.parent / "database" / "workbench.sqlite3"


def database_path_from_environment(environ: Mapping[str, str] | None = None) -> Path:
    """The database file: WORKBENCH_DATABASE_PATH when it is set (the e2e server sets it to a throwaway file),
    otherwise the application's own database/workbench.sqlite3. It is not set in production."""
    configured = (os.environ if environ is None else environ).get("WORKBENCH_DATABASE_PATH", "").strip()
    return Path(configured) if configured else DEFAULT_DATABASE_PATH


DATABASE_PATH = database_path_from_environment()

_CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")


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
    character_gender TEXT,
    speech_register TEXT,
    indeclinable INTEGER NOT NULL DEFAULT 0,
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
    narrator_gender TEXT,
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
    source_language TEXT NOT NULL,
    target_language TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    remote_glossary_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    synced_at TEXT NOT NULL,
    PRIMARY KEY (connection_id, source_language, target_language)
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
    exclude_from_export INTEGER NOT NULL DEFAULT 0,
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
    proofread INTEGER NOT NULL DEFAULT 0,
    is_service INTEGER NOT NULL DEFAULT 0,
    queued_for_qa INTEGER NOT NULL DEFAULT 0,
    narrator_change TEXT,
    UNIQUE(chapter_id, paragraph_index)
);

-- Translations of one paragraph by different engines, kept side by side for comparison.
-- book_paragraphs.translation_text stays the chosen text (export, QA, search read it);
-- book_paragraphs.selected_variant_id says which variant it came from.
CREATE TABLE IF NOT EXISTS paragraph_translation_variants (
    variant_id TEXT PRIMARY KEY,
    paragraph_id TEXT NOT NULL REFERENCES book_paragraphs(paragraph_id) ON DELETE CASCADE,
    engine TEXT NOT NULL CHECK(engine IN ('current', 'deepl', 'claude', 'openai', 'gemini', 'manual')),
    text TEXT NOT NULL,
    model TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_translation_variants_paragraph ON paragraph_translation_variants(paragraph_id, engine);

CREATE TABLE IF NOT EXISTS paragraph_footnotes (
    footnote_id TEXT PRIMARY KEY,
    paragraph_id TEXT NOT NULL REFERENCES book_paragraphs(paragraph_id) ON DELETE CASCADE,
    note_text TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_paragraph_footnotes_paragraph ON paragraph_footnotes(paragraph_id);

-- AI QA findings pending review. A finding is deleted outright (not
-- flagged resolved) once accepted or dismissed in the UI -- only
-- not-yet-decided findings are worth keeping around.
CREATE TABLE IF NOT EXISTS chapter_qa_findings (
    finding_id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL REFERENCES book_chapters(chapter_id) ON DELETE CASCADE,
    paragraph_id TEXT NOT NULL,
    category TEXT NOT NULL,
    quote TEXT NOT NULL,
    explanation TEXT,
    suggestion TEXT,
    source_model TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(chapter_id, paragraph_id, category, quote, source_model)
);

CREATE INDEX IF NOT EXISTS idx_chapter_qa_findings_chapter ON chapter_qa_findings(chapter_id);

CREATE TABLE IF NOT EXISTS qa_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id TEXT NOT NULL REFERENCES book_chapters(chapter_id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qa_runs_chapter_provider ON qa_runs(chapter_id, provider);

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

-- One row per LLM API call that returned token counts (translation batches, retries, failed
-- batches, AI QA, analysis, chat). Kept apart from variants; the cost is computed from model_prices.
CREATE TABLE IF NOT EXISTS translation_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL REFERENCES book_projects(project_id) ON DELETE CASCADE,
    chapter_id TEXT,
    engine TEXT NOT NULL,
    model TEXT NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('translate', 'retry', 'qa', 'analysis', 'chat', 'dictionary')),
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cache_read_tokens INTEGER NOT NULL DEFAULT 0,
    cache_write_tokens INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    queue_id TEXT,
    source_chars INTEGER
);

CREATE INDEX IF NOT EXISTS idx_translation_usage_project ON translation_usage(project_id, chapter_id);

-- Active working time: one row is one minute in which the translator was active in the open project.
-- Identifiers and the UTC minute only, never book text. chapter_id stays plain text like in translation_usage
-- (a re-imported book has new chapters; the minutes of the old ones keep counting for the project).
CREATE TABLE IF NOT EXISTS activity_minutes (
    project_id TEXT NOT NULL REFERENCES book_projects(project_id) ON DELETE CASCADE,
    chapter_id TEXT,
    minute_utc TEXT NOT NULL,
    PRIMARY KEY (project_id, minute_utc)
);

CREATE INDEX IF NOT EXISTS idx_activity_minutes_minute ON activity_minutes(minute_utc);

-- Dictionary lookups already answered by the model. The key has no book text: a normalized term
-- and a hash of the sentence it stood in. mode is word, phrase or moreN (the Nth «Ще значення»).
CREATE TABLE IF NOT EXISTS dictionary_cache (
    term_key TEXT NOT NULL,
    sentence_hash TEXT NOT NULL,
    model TEXT NOT NULL,
    mode TEXT NOT NULL,
    response TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (term_key, sentence_hash, model, mode)
);

-- A multi-chapter translation queue: a server-side job that survives restarts. The plan of every
-- chapter is a JSON list of paragraph ids (no book text), so a batch can be resumed exactly.
CREATE TABLE IF NOT EXISTS translation_queues (
    queue_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES book_projects(project_id) ON DELETE CASCADE,
    engine TEXT NOT NULL,
    connection_id TEXT NOT NULL,
    model TEXT,
    reasoning TEXT,
    options TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL CHECK(status IN ('running', 'paused', 'completed', 'stopped', 'budget_reached', 'failed')),
    budget_usd REAL,
    estimate_usd REAL,
    error TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    undone_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_translation_queues_project ON translation_queues(project_id, created_at);

CREATE TABLE IF NOT EXISTS translation_queue_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    queue_id TEXT NOT NULL REFERENCES translation_queues(queue_id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    chapter_id TEXT NOT NULL,
    chapter_index INTEGER NOT NULL,
    title TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'running', 'done', 'partial', 'error', 'skipped')),
    plan TEXT NOT NULL DEFAULT '[]',
    paragraphs_total INTEGER NOT NULL DEFAULT 0,
    paragraphs_done INTEGER NOT NULL DEFAULT 0,
    batches_total INTEGER NOT NULL DEFAULT 0,
    batches_done INTEGER NOT NULL DEFAULT 0,
    chars_total INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    started_at TEXT,
    finished_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_translation_queue_items_queue ON translation_queue_items(queue_id, position);

-- Variants a queue created (auto_selected: they became the chosen text because the paragraph had none),
-- so "Скасувати перекладене чергою" removes exactly these and nothing else.
CREATE TABLE IF NOT EXISTS translation_queue_variants (
    queue_id TEXT NOT NULL REFERENCES translation_queues(queue_id) ON DELETE CASCADE,
    variant_id TEXT NOT NULL,
    paragraph_id TEXT NOT NULL,
    auto_selected INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (queue_id, variant_id)
);

-- Editable price table, USD per 1M tokens; NULL = not set (a row with no price at all is
-- never stored). source: seed (initial value), manual (edited by the user), list (public list).
CREATE TABLE IF NOT EXISTS model_prices (
    model TEXT PRIMARY KEY,
    input_per_mtok REAL,
    output_per_mtok REAL,
    cache_read_per_mtok REAL,
    cache_write_per_mtok REAL,
    updated_at TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'manual' CHECK(source IN ('seed', 'manual', 'list'))
);

-- Small key-value settings: time zone for the daily usage view, when/where prices were updated.
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Own translation instructions per LLM engine: scope 'global' (all projects, project_id '') and
-- scope 'project' (an addition for one project). Plain text, at most ENGINE_INSTRUCTIONS_LIMIT characters.
CREATE TABLE IF NOT EXISTS engine_instructions (
    engine TEXT NOT NULL CHECK(engine IN ('claude', 'openai', 'gemini')),
    scope TEXT NOT NULL CHECK(scope IN ('global', 'project')),
    project_id TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (engine, scope, project_id)
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


# Footnote position marker embedded directly inside translation_text:
# \uE000<footnote_id>\uE000. Private-Use-Area characters so they never
# collide with real text, survive plain-text editing/undo like any other
# character, and are invisible until the frontend renders them as markers.
FOOTNOTE_TOKEN_RE = re.compile("\uE000([0-9a-zA-Z_-]+)\uE000")

TRANSLATION_ENGINES = ("current", "deepl", "claude", "openai", "gemini", "manual")
# Every engine run adds a new version of the variant for (paragraph, engine); this many of
# the newest versions are kept per pair, plus the selected variant even when it is older.
VARIANT_VERSIONS_KEPT = 10
ENGINE_INSTRUCTION_ENGINES = ("claude", "openai", "gemini")
ENGINE_INSTRUCTIONS_LIMIT = 4000


# Progress. The denominator is the paragraphs that have original text, are not service text and are in a chapter
# that is not «Не експортувати»; the same figures are counted in words of the original. «Перекладено» = a chosen
# translation exists, «Перевірено» = reviewed, «Вичитано» = proofread; «Загальне» = the mean of the three percents.
_PROGRESS_FILTER = "bp.is_service = 0 AND TRIM(COALESCE(bp.original_text, '')) != ''"
_PROGRESS_TRANSLATED = "TRIM(COALESCE(bp.translation_text, '')) != ''"
_PROGRESS_KEYS = (
    "p_total", "p_translated", "p_reviewed", "p_proofread", "w_total", "w_translated", "w_reviewed", "w_proofread",
)
_PROGRESS_COLUMNS = (
    "COUNT(bp.paragraph_id) AS p_total, "
    f"COALESCE(SUM(CASE WHEN {_PROGRESS_TRANSLATED} THEN 1 ELSE 0 END), 0) AS p_translated, "
    "COALESCE(SUM(CASE WHEN bp.reviewed = 1 THEN 1 ELSE 0 END), 0) AS p_reviewed, "
    "COALESCE(SUM(CASE WHEN bp.proofread = 1 THEN 1 ELSE 0 END), 0) AS p_proofread, "
    "COALESCE(SUM(bp.word_count), 0) AS w_total, "
    f"COALESCE(SUM(CASE WHEN {_PROGRESS_TRANSLATED} THEN bp.word_count ELSE 0 END), 0) AS w_translated, "
    "COALESCE(SUM(CASE WHEN bp.reviewed = 1 THEN bp.word_count ELSE 0 END), 0) AS w_reviewed, "
    "COALESCE(SUM(CASE WHEN bp.proofread = 1 THEN bp.word_count ELSE 0 END), 0) AS w_proofread"
)


def _progress_block(total: int, translated: int, reviewed: int, proofread: int) -> dict[str, Any]:
    percents = [(count / total * 100) if total else 0.0 for count in (translated, reviewed, proofread)]
    overall = sum(percents) / 3
    return {
        "total": total, "translated": translated, "reviewed": reviewed, "proofread": proofread,
        "percent": {
            "translated": round(percents[0], 1), "reviewed": round(percents[1], 1), "proofread": round(percents[2], 1),
            "overall": round(overall, 1),
        },
    }


def _progress_summary(row: Any) -> dict[str, Any]:
    """{"paragraphs": block, "words": block} from an aggregate row (or the dict of summed keys); zeros for None."""
    def value(key: str) -> int:
        if row is None:
            return 0
        return int((row[key] if not isinstance(row, dict) else row.get(key)) or 0)
    return {
        "paragraphs": _progress_block(value("p_total"), value("p_translated"), value("p_reviewed"), value("p_proofread")),
        "words": _progress_block(value("w_total"), value("w_translated"), value("w_reviewed"), value("w_proofread")),
    }


def normalize_engine_instructions(text: Any) -> str:
    """Plain text: line breaks are LF, the ends are trimmed."""
    return str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()


# Engines the whole-chapter «Обрати для файлу» offers ("manual" is the editor, not an engine run).
BULK_SELECTION_ENGINES = ("claude", "openai", "gemini", "deepl", "current")
BULK_SELECTION_MAX_ITEMS = 5000
BULK_EXAMPLE_COUNT = 3
BULK_EXAMPLE_CHARS = 80


def normalize_translation_text(text: str | None) -> str | None:
    """Line breaks of a translation are kept (one original paragraph may be several Ukrainian ones):
    CR/CRLF become LF, spaces at the edges of every line go, and blank lines (also several in a row)
    are dropped so a break is a single LF. A text without a line break is returned untouched."""
    if not text or ("\n" not in text and "\r" not in text):
        return text
    lines = (line.strip(" \t") for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"))
    return "\n".join(line for line in lines if line)


def _without_footnote_markers(text: str | None) -> str:
    return FOOTNOTE_TOKEN_RE.sub("", text or "")


def _with_carried_footnote_markers(new_text: str, previous_text: str | None) -> tuple[str, list[str]]:
    """Footnotes live as markers inside the chosen text, and a marker that disappears
    deletes its footnote. Engine variants are translated from the original and carry no
    markers, so any marker the previous text had is appended to the end instead of lost."""
    present = set(FOOTNOTE_TOKEN_RE.findall(new_text))
    missing = [footnote_id for footnote_id in dict.fromkeys(FOOTNOTE_TOKEN_RE.findall(previous_text or "")) if footnote_id not in present]
    return new_text + "".join(f"\uE000{footnote_id}\uE000" for footnote_id in missing), missing


def _validated_character_gender(value):
    if value is None:
        return None
    if value not in ("masc", "femn", "plur"):
        raise ValueError("Character gender must be 'masc', 'femn', 'plur', or omitted.")
    return value


# Narrator's own gender/person in first-person narration, or 'third' when the
# narrator doesn't refer to themselves at all. Used both as the project-wide
# default and as the value stamped on a paragraph that starts a POV switch.
NARRATOR_GENDERS = ("masc", "femn", "third")


def _validated_narrator_gender(value):
    if value is None:
        return None
    if value not in NARRATOR_GENDERS:
        raise ValueError("Narrator gender must be 'masc', 'femn', 'third', or omitted.")
    return value


def _deduped_ids(values):
    """Order-preserving de-dup for a plain list of ids (e.g. projectRuleIds).
    Re-adding an id that's already in the list must be a no-op, not a
    duplicate project_rules/project_glossary row — those tables key on
    (project_id, rule_id)/(project_id, glossary_entry_id), so an undeduped
    repeat would crash the whole save with a UNIQUE constraint violation."""
    return list(dict.fromkeys(values))


def _deduped_by_key(items, key):
    """Order-preserving de-dup for a list of {key: ..., ...} dicts (e.g.
    inheritedRules), keyed on `key`. The later occurrence wins, so a repeat
    "add"/confirm action overwrites the earlier one instead of colliding
    with it on insert."""
    deduped: dict[Any, dict[str, Any]] = {}
    for item in items:
        deduped[item.get(key)] = item
    return list(deduped.values())


def _cleaned_speech_register(value):
    """Free-text note on how a character speaks (e.g. profanity level,
    formality) — no fixed vocabulary, just trimmed to None-or-text so a
    blank string doesn't get stored as a meaningless empty note."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


class Storage:
    def __init__(self, database_path: str | Path = DATABASE_PATH):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA journal_mode = WAL")
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
            if "narrator_gender" not in columns:
                connection.execute("ALTER TABLE book_projects ADD COLUMN narrator_gender TEXT")
            paragraph_columns = {row["name"] for row in connection.execute("PRAGMA table_info(book_paragraphs)")}
            if "translation_text" not in paragraph_columns:
                connection.execute("ALTER TABLE book_paragraphs ADD COLUMN translation_text TEXT")
            if "reviewed" not in paragraph_columns:
                connection.execute("ALTER TABLE book_paragraphs ADD COLUMN reviewed INTEGER NOT NULL DEFAULT 0")
            if "proofread" not in paragraph_columns:
                # The second stage after «Перевірено» (reviewed): «Вичитано». Independent of reviewed.
                connection.execute("ALTER TABLE book_paragraphs ADD COLUMN proofread INTEGER NOT NULL DEFAULT 0")
            if "is_service" not in paragraph_columns:
                connection.execute("ALTER TABLE book_paragraphs ADD COLUMN is_service INTEGER NOT NULL DEFAULT 0")
            if "queued_for_qa" not in paragraph_columns:
                connection.execute("ALTER TABLE book_paragraphs ADD COLUMN queued_for_qa INTEGER NOT NULL DEFAULT 0")
            if "narrator_change" not in paragraph_columns:
                connection.execute("ALTER TABLE book_paragraphs ADD COLUMN narrator_change TEXT")
            if "selected_variant_id" not in paragraph_columns:
                connection.execute("ALTER TABLE book_paragraphs ADD COLUMN selected_variant_id TEXT")
            variant_columns = {row["name"] for row in connection.execute("PRAGMA table_info(paragraph_translation_variants)")}
            if "warnings" not in variant_columns:
                # JSON list of checks the engine output failed (e.g. a glossary term not used).
                connection.execute("ALTER TABLE paragraph_translation_variants ADD COLUMN warnings TEXT")
            if "prompt_hash" not in variant_columns:
                # 8 hex characters of the engine-instructions block the version was made with (NULL: unknown / none).
                connection.execute("ALTER TABLE paragraph_translation_variants ADD COLUMN prompt_hash TEXT")
            self._migrate_translation_variants(connection)
            self._migrate_model_prices(connection)
            self._migrate_usage_columns(connection)
            self._migrate_usage_kinds(connection)
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
            glossary_entry_columns = {row["name"] for row in connection.execute("PRAGMA table_info(glossary_entries)")}
            if "character_gender" not in glossary_entry_columns:
                connection.execute("ALTER TABLE glossary_entries ADD COLUMN character_gender TEXT")
            if "speech_register" not in glossary_entry_columns:
                connection.execute("ALTER TABLE glossary_entries ADD COLUMN speech_register TEXT")
            if "indeclinable" not in glossary_entry_columns:
                connection.execute("ALTER TABLE glossary_entries ADD COLUMN indeclinable INTEGER NOT NULL DEFAULT 0")
            self._migrate_provider_glossary_sync_slots(connection)
            self._migrate_translation_glossary_versions(connection)
            self._migrate_project_chat_messages(connection)
            self._migrate_chapter_export_flag(connection)
            self._migrate_qa_runs(connection)
            self._migrate_search_index(connection)
            self._backfill_chapter_elements(connection)
            cover_rows = connection.execute("SELECT book_id, cover_image FROM book_documents WHERE cover_image IS NOT NULL").fetchall()
            for row in cover_rows:
                if self._cover_needs_normalization(row["cover_image"]):
                    connection.execute(
                        "UPDATE book_documents SET cover_image = ? WHERE book_id = ?",
                        (self._normalize_cover_image(row["cover_image"]), row["book_id"]),
                    )

    @staticmethod
    def _migrate_chapter_export_flag(connection: sqlite3.Connection) -> None:
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(book_chapters)")}
        if "exclude_from_export" not in columns:
            connection.execute("ALTER TABLE book_chapters ADD COLUMN exclude_from_export INTEGER NOT NULL DEFAULT 0")

    @staticmethod
    def _migrate_qa_runs(connection: sqlite3.Connection) -> None:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS qa_runs ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "chapter_id TEXT NOT NULL REFERENCES book_chapters(chapter_id) ON DELETE CASCADE, "
            "provider TEXT NOT NULL, "
            "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_qa_runs_chapter_provider "
            "ON qa_runs(chapter_id, provider)"
        )

    @staticmethod
    def _migrate_provider_glossary_sync_slots(connection: sqlite3.Connection) -> None:
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(provider_glossary_sync)")}
        if {"source_language", "target_language"}.issubset(columns):
            return

        connection.execute("ALTER TABLE provider_glossary_sync RENAME TO provider_glossary_sync_legacy")
        connection.execute(
            "CREATE TABLE provider_glossary_sync ("
            "glossary_rule_id TEXT NOT NULL REFERENCES project_translation_glossaries(glossary_rule_id) ON DELETE CASCADE, "
            "connection_id TEXT NOT NULL, source_language TEXT NOT NULL, target_language TEXT NOT NULL, "
            "provider_id TEXT NOT NULL, remote_glossary_id TEXT NOT NULL, content_hash TEXT NOT NULL, synced_at TEXT NOT NULL, "
            "PRIMARY KEY (connection_id, source_language, target_language))"
        )
        rows = connection.execute(
            "SELECT legacy.*, glossary.source_language, glossary.target_language "
            "FROM provider_glossary_sync_legacy legacy "
            "JOIN project_translation_glossaries glossary ON glossary.glossary_rule_id = legacy.glossary_rule_id "
            "ORDER BY legacy.synced_at"
        ).fetchall()
        for row in rows:
            connection.execute(
                "INSERT INTO provider_glossary_sync(glossary_rule_id, connection_id, source_language, target_language, provider_id, remote_glossary_id, content_hash, synced_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(connection_id, source_language, target_language) DO UPDATE SET glossary_rule_id = excluded.glossary_rule_id, provider_id = excluded.provider_id, remote_glossary_id = excluded.remote_glossary_id, content_hash = excluded.content_hash, synced_at = excluded.synced_at",
                (
                    row["glossary_rule_id"], row["connection_id"], row["source_language"],
                    row["target_language"], row["provider_id"], row["remote_glossary_id"],
                    row["content_hash"], row["synced_at"],
                ),
            )
        connection.execute("DROP TABLE provider_glossary_sync_legacy")

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
    def _migrate_project_chat_messages(connection: sqlite3.Connection) -> None:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS project_chat_messages ("
            "message_id TEXT PRIMARY KEY, "
            "project_id TEXT NOT NULL REFERENCES book_projects(project_id) ON DELETE CASCADE, "
            "role TEXT NOT NULL, "
            "content TEXT NOT NULL, "
            "provider_id TEXT, "
            "created_at TEXT NOT NULL)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS project_chat_messages_project_idx "
            "ON project_chat_messages(project_id, created_at)"
        )

    @staticmethod
    def _migrate_search_index(connection: sqlite3.Connection) -> None:
        fts_exists = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'book_paragraphs_fts'"
        ).fetchone()
        if fts_exists is None:
            connection.execute(
                "CREATE VIRTUAL TABLE book_paragraphs_fts USING fts5("
                "original_text, translation_text, "
                "content='book_paragraphs', content_rowid='rowid', "
                "tokenize='unicode61 remove_diacritics 2'"
                ")"
            )
            connection.execute(
                "INSERT INTO book_paragraphs_fts(rowid, original_text, translation_text) "
                "SELECT rowid, original_text, translation_text FROM book_paragraphs"
            )
        connection.execute(
            "CREATE TRIGGER IF NOT EXISTS book_paragraphs_fts_ai AFTER INSERT ON book_paragraphs BEGIN "
            "INSERT INTO book_paragraphs_fts(rowid, original_text, translation_text) "
            "VALUES (new.rowid, new.original_text, new.translation_text); "
            "END"
        )
        connection.execute(
            "CREATE TRIGGER IF NOT EXISTS book_paragraphs_fts_ad AFTER DELETE ON book_paragraphs BEGIN "
            "INSERT INTO book_paragraphs_fts(book_paragraphs_fts, rowid, original_text, translation_text) "
            "VALUES ('delete', old.rowid, old.original_text, old.translation_text); "
            "END"
        )
        connection.execute(
            "CREATE TRIGGER IF NOT EXISTS book_paragraphs_fts_au AFTER UPDATE ON book_paragraphs BEGIN "
            "INSERT INTO book_paragraphs_fts(book_paragraphs_fts, rowid, original_text, translation_text) "
            "VALUES ('delete', old.rowid, old.original_text, old.translation_text); "
            "INSERT INTO book_paragraphs_fts(rowid, original_text, translation_text) "
            "VALUES (new.rowid, new.original_text, new.translation_text); "
            "END"
        )

    @staticmethod
    def _fts_escape(text: str) -> str:
        return text.replace('"', '""')

    def search_paragraphs(
        self,
        query: str,
        scope: str = "all",
        chapter_id: str | None = None,
        project_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
        match_mode: str = "partial",
    ) -> dict[str, Any]:
        query = query.strip()
        if not query:
            return {"results": [], "total": 0, "field": None}
        if match_mode not in ("exact", "partial"):
            raise ValueError(f"unknown match_mode: {match_mode}")

        field = "translation_text" if _CYRILLIC_RE.search(query) else "original_text"
        column_index = 1 if field == "translation_text" else 0

        conditions = ["bp.is_service = 0"]
        scope_params: list[Any] = []
        if scope == "chapter":
            if not chapter_id:
                raise ValueError("chapter_id required for scope='chapter'")
            conditions.append("bp.chapter_id = ?")
            scope_params.append(chapter_id)
        elif scope == "project":
            if not project_id:
                raise ValueError("project_id required for scope='project'")
            conditions.append("doc.project_id = ?")
            scope_params.append(project_id)
        elif scope != "all":
            raise ValueError(f"unknown scope: {scope}")
        where_clause = " AND ".join(conditions)

        if match_mode == "partial":
            return self._search_paragraphs_partial(query, field, where_clause, scope_params, limit, offset)

        match_query = f'{field}:"{self._fts_escape(query)}"'
        params: list[Any] = [match_query] + scope_params
        params_with_paging = params + [limit, offset]

        with self.connection() as connection:
            count_row = connection.execute(
                "SELECT COUNT(*) AS total "
                "FROM book_paragraphs_fts "
                "JOIN book_paragraphs bp ON bp.rowid = book_paragraphs_fts.rowid "
                "JOIN book_chapters ch ON ch.chapter_id = bp.chapter_id "
                "JOIN book_documents doc ON doc.book_id = ch.book_id "
                f"WHERE book_paragraphs_fts MATCH ? AND {where_clause}",
                params,
            ).fetchone()
            rows = connection.execute(
                "SELECT bp.paragraph_id, bp.chapter_id, bp.paragraph_index, "
                "ch.chapter_index, ch.title AS chapter_title, ch.translation_title, "
                "ch.paragraph_count AS chapter_paragraph_count, "
                "doc.project_id, proj.title AS project_title, "
                f"snippet(book_paragraphs_fts, {column_index}, '⟦', '⟧', '…', 12) AS snippet, "
                "bm25(book_paragraphs_fts) AS rank "
                "FROM book_paragraphs_fts "
                "JOIN book_paragraphs bp ON bp.rowid = book_paragraphs_fts.rowid "
                "JOIN book_chapters ch ON ch.chapter_id = bp.chapter_id "
                "JOIN book_documents doc ON doc.book_id = ch.book_id "
                "JOIN book_projects proj ON proj.project_id = doc.project_id "
                f"WHERE book_paragraphs_fts MATCH ? AND {where_clause} "
                "ORDER BY proj.title, ch.chapter_index, bp.paragraph_index LIMIT ? OFFSET ?",
                params_with_paging,
            ).fetchall()

        results = []
        for row in rows:
            chapter_paragraph_count = row["chapter_paragraph_count"] or 1
            position_percent = round(
                (row["paragraph_index"] + 1) / chapter_paragraph_count * 100, 1
            )
            results.append({
                "paragraphId": row["paragraph_id"],
                "chapterId": row["chapter_id"],
                "chapterIndex": row["chapter_index"],
                "chapterTitle": row["translation_title"] or row["chapter_title"],
                "projectId": row["project_id"],
                "projectTitle": row["project_title"],
                "snippet": row["snippet"],
                "positionPercent": position_percent,
                "field": field,
            })

        return {"results": results, "total": count_row["total"], "field": field}

    def _search_paragraphs_partial(
        self,
        query: str,
        field: str,
        where_clause: str,
        scope_params: list[Any],
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        # SQLite's LIKE only case-folds ASCII, so a case-insensitive substring match
        # over Cyrillic translation text has to be done in Python instead of SQL.
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT bp.paragraph_id, bp.chapter_id, bp.paragraph_index, "
                f"bp.{field} AS matched_text, "
                "ch.chapter_index, ch.title AS chapter_title, ch.translation_title, "
                "ch.paragraph_count AS chapter_paragraph_count, "
                "doc.project_id, proj.title AS project_title "
                "FROM book_paragraphs bp "
                "JOIN book_chapters ch ON ch.chapter_id = bp.chapter_id "
                "JOIN book_documents doc ON doc.book_id = ch.book_id "
                "JOIN book_projects proj ON proj.project_id = doc.project_id "
                f"WHERE {where_clause} "
                "ORDER BY proj.title, ch.chapter_index, bp.paragraph_index",
                scope_params,
            ).fetchall()

        needle = query.lower()
        matched_rows = [row for row in rows if needle in (row["matched_text"] or "").lower()]
        total = len(matched_rows)

        results = []
        for row in matched_rows[offset:offset + limit]:
            chapter_paragraph_count = row["chapter_paragraph_count"] or 1
            position_percent = round(
                (row["paragraph_index"] + 1) / chapter_paragraph_count * 100, 1
            )
            results.append({
                "paragraphId": row["paragraph_id"],
                "chapterId": row["chapter_id"],
                "chapterIndex": row["chapter_index"],
                "chapterTitle": row["translation_title"] or row["chapter_title"],
                "projectId": row["project_id"],
                "projectTitle": row["project_title"],
                "snippet": self._build_like_snippet(row["matched_text"] or "", query),
                "positionPercent": position_percent,
                "field": field,
            })

        return {"results": results, "total": total, "field": field}

    @staticmethod
    def _build_like_snippet(text: str, query: str, radius: int = 60) -> str:
        lowered = text.lower()
        index = lowered.find(query.lower())
        if index == -1:
            # The row matched via a Python substring check above, so this shouldn't
            # happen; fall back to a plain excerpt rather than failing the request.
            return text[: radius * 2]
        match_end = index + len(query)
        start_ctx = max(0, index - radius)
        end_ctx = min(len(text), match_end + radius)
        prefix = "…" if start_ctx > 0 else ""
        suffix = "…" if end_ctx < len(text) else ""
        return f"{prefix}{text[start_ctx:index]}⟦{text[index:match_end]}⟧{text[match_end:end_ctx]}{suffix}"

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
        """Every entry also carries `usedIn`: the projects (with their series/
        author, when set) that currently reference it via project_glossary.
        There is no stored "origin" for a catalog entry — a term is shared,
        many-to-many, across whatever projects have picked it up — so this is
        derived from the live project_glossary rows on every call rather than
        a denormalized column."""
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM glossary_entries ORDER BY source").fetchall()
            context_rows = connection.execute(
                "SELECT pg.glossary_entry_id, bp.project_id, bp.title AS project_title, "
                "bp.series_id, s.name AS series_name, bp.author_id, a.name AS author_name "
                "FROM project_glossary pg "
                "JOIN book_projects bp ON bp.project_id = pg.project_id "
                "LEFT JOIN series s ON s.series_id = bp.series_id "
                "LEFT JOIN authors a ON a.author_id = bp.author_id "
                "ORDER BY bp.title"
            ).fetchall()
        used_in_by_entry: dict[str, list[dict[str, Any]]] = {}
        for row in context_rows:
            used_in_by_entry.setdefault(row["glossary_entry_id"], []).append({
                "projectId": row["project_id"],
                "projectTitle": row["project_title"],
                "seriesId": row["series_id"],
                "seriesName": row["series_name"],
                "authorId": row["author_id"],
                "authorName": row["author_name"],
            })
        return [
            {**self._glossary_from_row(row), "usedIn": used_in_by_entry.get(row["glossary_entry_id"], [])}
            for row in rows
        ]

    def create_glossary_entry(self, data: dict[str, Any]) -> dict[str, Any]:
        entry = {
            "glossaryEntryId": data.get("glossaryEntryId") or _new_id("glossary"),
            "source": str(data.get("source", "")).strip(),
            "target": str(data.get("target", "")).strip(),
            "note": data.get("note"),
            "characterGender": _validated_character_gender(data.get("characterGender")),
            "speechRegister": _cleaned_speech_register(data.get("speechRegister")),
            "indeclinable": bool(data.get("indeclinable", False)),
            "active": bool(data.get("active", True)),
            "updatedAt": _now(),
        }
        if not entry["source"] or not entry["target"]:
            raise ValueError("Glossary source and target are required.")
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO glossary_entries(glossary_entry_id, source, target, note, character_gender, speech_register, indeclinable, active, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (entry["glossaryEntryId"], entry["source"], entry["target"], entry["note"], entry["characterGender"], entry["speechRegister"], int(entry["indeclinable"]), int(entry["active"]), entry["updatedAt"]),
            )
        return entry

    def update_glossary_entry(self, entry_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        updated = {
            "source": str(data.get("source", "")).strip(),
            "target": str(data.get("target", "")).strip(),
            "note": data.get("note"),
            "characterGender": _validated_character_gender(data.get("characterGender")),
            "speechRegister": _cleaned_speech_register(data.get("speechRegister")),
            "indeclinable": bool(data.get("indeclinable", False)),
            "active": bool(data.get("active", True)),
            "updatedAt": _now(),
        }
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE glossary_entries SET source = ?, target = ?, note = ?, character_gender = ?, speech_register = ?, indeclinable = ?, active = ?, updated_at = ? WHERE glossary_entry_id = ?",
                (updated["source"], updated["target"], updated["note"], updated["characterGender"], updated["speechRegister"], int(updated["indeclinable"]), int(updated["active"]), updated["updatedAt"], entry_id),
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
            "characterGender": row["character_gender"],
            "speechRegister": row["speech_register"],
            "indeclinable": _bool(row["indeclinable"]),
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
        rule_ids = _deduped_ids(data.get("ruleIds", []))
        glossary_ids = _deduped_ids(data.get("glossaryEntryIds", []))
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
            progress_rows = connection.execute(
                "SELECT doc.project_id AS project_id, " + _PROGRESS_COLUMNS + " "
                "FROM book_paragraphs bp "
                "JOIN book_chapters ch ON ch.chapter_id = bp.chapter_id "
                "JOIN book_documents doc ON doc.book_id = ch.book_id "
                "WHERE " + _PROGRESS_FILTER + " AND ch.exclude_from_export = 0 "
                "GROUP BY doc.project_id"
            ).fetchall()
        progress_by_project = {row["project_id"]: _progress_summary(row) for row in progress_rows}
        return [
            self._project_summary_from_row(row, progress_by_project.get(row["project_id"]) or _progress_summary(None))
            for row in rows
        ]

    def project_progress(self, project_id: str) -> dict[str, Any] | None:
        """Progress of one project from SQL aggregates (no book text): the project totals and every chapter.
        «Не експортувати» chapters are listed (`excluded`) but are not part of the totals."""
        with self.connection() as connection:
            if connection.execute("SELECT 1 FROM book_projects WHERE project_id = ?", (project_id,)).fetchone() is None:
                return None
            rows = connection.execute(
                "SELECT ch.chapter_id AS chapter_id, ch.chapter_index AS chapter_index, ch.exclude_from_export AS excluded, "
                + _PROGRESS_COLUMNS + " "
                "FROM book_chapters ch JOIN book_documents doc ON doc.book_id = ch.book_id "
                "LEFT JOIN book_paragraphs bp ON bp.chapter_id = ch.chapter_id AND " + _PROGRESS_FILTER + " "
                "WHERE doc.project_id = ? GROUP BY ch.chapter_id ORDER BY ch.chapter_index",
                (project_id,),
            ).fetchall()
        chapters = []
        totals = {key: 0 for key in _PROGRESS_KEYS}
        for row in rows:
            summary = _progress_summary(row)
            chapters.append({"chapterId": row["chapter_id"], "chapterIndex": row["chapter_index"], "excluded": bool(row["excluded"]), **summary})
            if not row["excluded"]:
                for key in _PROGRESS_KEYS:
                    totals[key] += row[key] or 0
        return {"projectId": project_id, **_progress_summary(totals), "chapters": chapters}

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM book_projects WHERE project_id = ?", (project_id,)).fetchone()
        return self._project_from_row(row) if row else None

    def create_project(self, data: dict[str, Any]) -> dict[str, Any]:
        project_id = data.get("projectId") or _new_id("project")
        timestamp = _now()
        project = self._project_input(data, project_id, timestamp, timestamp)
        with self.connection() as connection:
            self._write_project(connection, project, replace=False, raw_data=data)
        return self.get_project(project_id) or project

    def update_project(self, project_id: str, data: dict[str, Any]) -> dict[str, Any]:
        existing = self.get_project(project_id)
        if existing is None:
            return None
        project = self._project_input(data, project_id, existing["createdAt"], _now(), existing)
        with self.connection() as connection:
            self._write_project(connection, project, replace=True, raw_data=data)
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

    def list_project_translation_glossaries(self, project_id: str, connection_id: str | None = None) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM project_translation_glossaries WHERE project_id = ? ORDER BY created_at",
                (project_id,),
            ).fetchall()
            sync_query = (
                "SELECT sync.*, owner.project_id AS owner_project_id FROM provider_glossary_sync sync "
                "JOIN project_translation_glossaries owner ON owner.glossary_rule_id = sync.glossary_rule_id "
                "WHERE EXISTS (SELECT 1 FROM project_translation_glossaries local "
                "WHERE local.project_id = ? AND local.source_language = sync.source_language AND local.target_language = sync.target_language)"
            )
            params: list[Any] = [project_id]
            if connection_id is not None:
                # Scoping to the connection that will actually be used means the sync status
                # shown here can never lie: a stale sync row left behind by a connection the
                # project isn't using anymore (e.g. after switching to a different DeepL
                # account) is correctly reported as unsynced instead of shadowing it.
                sync_query += " AND sync.connection_id = ?"
                params.append(connection_id)
            sync_rows = connection.execute(sync_query, params).fetchall()
        sync_by_pair = {(row["source_language"], row["target_language"]): row for row in sync_rows}
        return [self._translation_glossary(row, sync_by_pair.get((row["source_language"], row["target_language"]))) for row in rows]

    def get_project_translation_glossary(self, glossary_rule_id: str, connection_id: str | None = None) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM project_translation_glossaries WHERE glossary_rule_id = ?",
                (glossary_rule_id,),
            ).fetchone()
            sync = None
            if row:
                sync_query = (
                    "SELECT sync.*, owner.project_id AS owner_project_id FROM provider_glossary_sync sync "
                    "JOIN project_translation_glossaries owner ON owner.glossary_rule_id = sync.glossary_rule_id "
                    "WHERE sync.source_language = ? AND sync.target_language = ?"
                )
                params: list[Any] = [row["source_language"], row["target_language"]]
                if connection_id is not None:
                    # Pin the sync status to the connection that will actually translate next,
                    # rather than whichever connection happened to sync most recently — otherwise
                    # a glossary can display "synced" purely because some other DeepL account
                    # once synced this same language pair.
                    sync_query += " AND sync.connection_id = ?"
                    params.append(connection_id)
                else:
                    sync_query += " ORDER BY sync.synced_at DESC LIMIT 1"
                sync = connection.execute(sync_query, params).fetchone()
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
                "SELECT sync.*, owner.project_id AS owner_project_id FROM provider_glossary_sync sync "
                "JOIN project_translation_glossaries owner ON owner.glossary_rule_id = sync.glossary_rule_id "
                "WHERE sync.source_language = ? AND sync.target_language = ? ORDER BY sync.synced_at DESC LIMIT 1",
                (row["source_language"], row["target_language"]),
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
                "SELECT source, target, note, character_gender, indeclinable FROM glossary_entries WHERE glossary_entry_id = ?",
                (glossary_entry_id,),
            ).fetchone()
            if row is None:
                raise ValueError(f"GlossaryItem not found: {glossary_entry_id}")
            entries.append({
                "source": row["source"],
                "target": row["target"],
                "context": row["note"] or "",
                "characterGender": row["character_gender"],
                "indeclinable": _bool(row["indeclinable"]),
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
            glossary = connection.execute(
                "SELECT source_language, target_language FROM project_translation_glossaries WHERE glossary_rule_id = ?",
                (glossary_rule_id,),
            ).fetchone()
            if glossary is None:
                raise ValueError("Glossary not found.")
            connection.execute(
                "INSERT INTO provider_glossary_sync(glossary_rule_id, connection_id, source_language, target_language, provider_id, remote_glossary_id, content_hash, synced_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(connection_id, source_language, target_language) DO UPDATE SET glossary_rule_id = excluded.glossary_rule_id, provider_id = excluded.provider_id, remote_glossary_id = excluded.remote_glossary_id, content_hash = excluded.content_hash, synced_at = excluded.synced_at",
                (
                    glossary_rule_id, connection_id, glossary["source_language"], glossary["target_language"],
                    provider_id, remote_glossary_id, content_hash, _now(),
                ),
            )

    def delete_provider_glossary_sync(self, glossary_rule_id: str, connection_id: str) -> bool:
        with self.connection() as connection:
            return connection.execute(
                "DELETE FROM provider_glossary_sync WHERE connection_id = ? AND glossary_rule_id = ? "
                "AND (source_language, target_language) = (SELECT source_language, target_language "
                "FROM project_translation_glossaries WHERE glossary_rule_id = ?)",
                (connection_id, glossary_rule_id, glossary_rule_id),
            ).rowcount > 0

    def list_provider_glossary_sync_for_connection(self, connection_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT sync.*, owner.project_id AS owner_project_id FROM provider_glossary_sync sync "
                "JOIN project_translation_glossaries owner ON owner.glossary_rule_id = sync.glossary_rule_id "
                "WHERE sync.connection_id = ?",
                (connection_id,),
            ).fetchall()
        return [self._provider_glossary_sync(row) for row in rows]

    def delete_provider_glossary_sync_for_connection(self, connection_id: str) -> None:
        with self.connection() as connection:
            connection.execute(
                "DELETE FROM provider_glossary_sync WHERE connection_id = ?",
                (connection_id,),
            )

    def delete_provider_glossary_sync_by_remote_id(self, provider_id: str, remote_glossary_id: str) -> None:
        """Drop any local tracking row for a remote glossary that was deleted directly on the provider.

        Used during takeover recovery: a sync row pointing at this remote_glossary_id may still
        exist under a connection_id other than the one we resolved (e.g. a connection that was
        since deleted and re-created), so it must be matched by remote id rather than connection_id.
        """
        with self.connection() as connection:
            connection.execute(
                "DELETE FROM provider_glossary_sync WHERE provider_id = ? AND remote_glossary_id = ?",
                (provider_id, remote_glossary_id),
            )

    def get_provider_glossary_sync(self, connection_id: str, source_language: str, target_language: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT sync.*, glossary.project_id AS owner_project_id FROM provider_glossary_sync sync "
                "JOIN project_translation_glossaries glossary ON glossary.glossary_rule_id = sync.glossary_rule_id "
                "WHERE sync.connection_id = ? AND sync.source_language = ? AND sync.target_language = ?",
                (connection_id, source_language, target_language),
            ).fetchone()
        return self._provider_glossary_sync(row) if row else None

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
                "SELECT glossary.*, sync.connection_id, sync.remote_glossary_id, sync.provider_id, sync.synced_at, sync.content_hash, glossary.project_id AS owner_project_id "
                "FROM project_translation_glossaries glossary "
                "JOIN provider_glossary_sync sync ON sync.glossary_rule_id = glossary.glossary_rule_id "
                "WHERE glossary.project_id = ? AND sync.connection_id = ? AND glossary.target_language = ? AND sync.content_hash = glossary.content_hash "
                "ORDER BY glossary.updated_at DESC LIMIT 1",
                (project_id, connection_id, target_language),
            ).fetchone()
        return self._translation_glossary(row, row) if row else None

    @staticmethod
    def _provider_glossary_sync(sync: sqlite3.Row) -> dict[str, Any]:
        return {
            "glossaryRuleId": sync["glossary_rule_id"],
            "projectId": sync["owner_project_id"],
            "connectionId": sync["connection_id"],
            "providerId": sync["provider_id"],
            "remoteGlossaryId": sync["remote_glossary_id"],
            "contentHash": sync["content_hash"],
            "syncedAt": sync["synced_at"],
        }

    @staticmethod
    def _translation_glossary(row: sqlite3.Row, sync: sqlite3.Row | None) -> dict[str, Any]:
        sync_state = "unsynced"
        synced_content_hash = None
        if sync:
            synced_content_hash = sync["content_hash"] if "content_hash" in sync.keys() else row["content_hash"]
            owns_slot = sync["glossary_rule_id"] == row["glossary_rule_id"]
            sync_state = "synced" if owns_slot and synced_content_hash == row["content_hash"] else ("stale" if owns_slot else "unsynced")
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
                "glossaryRuleId": sync["glossary_rule_id"],
                "projectId": sync["owner_project_id"] if "owner_project_id" in sync.keys() else row["project_id"],
                "connectionId": sync["connection_id"],
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
            connection.execute("DELETE FROM engine_instructions WHERE scope = 'project' AND project_id = ?", (project_id,))
            return connection.execute("DELETE FROM book_projects WHERE project_id = ?", (project_id,)).rowcount > 0

    # --- own instructions per LLM engine ------------------------------------------------------------------

    def get_engine_instructions(self, engine: str, project_id: str | None = None) -> str:
        """The saved text of one scope: the project's addition when `project_id` is given, else the global text."""
        scope, owner = ("project", project_id) if project_id else ("global", "")
        with self.connection() as connection:
            row = connection.execute(
                "SELECT text FROM engine_instructions WHERE engine = ? AND scope = ? AND project_id = ?", (engine, scope, owner)
            ).fetchone()
        return row["text"] if row else ""

    @staticmethod
    def validate_engine_instructions(text: Any) -> str:
        """The normalized text, or ValueError for a non-string or a text above the limit."""
        if not isinstance(text, str):
            raise ValueError("Текст інструкцій має бути рядком.")
        text = normalize_engine_instructions(text)
        if len(text) > ENGINE_INSTRUCTIONS_LIMIT:
            raise ValueError(f"Інструкції завдовжки {len(text)} символів: ліміт — {ENGINE_INSTRUCTIONS_LIMIT}.")
        return text

    def set_engine_instructions(self, engine: str, text: str, project_id: str | None = None) -> str:
        """Save (or, for an empty text, remove) one scope's instructions. Returns the saved text."""
        if engine not in ENGINE_INSTRUCTION_ENGINES:
            raise ValueError("Інструкції можна задати лише для Claude, GPT і Gemini.")
        text = self.validate_engine_instructions(text)
        scope, owner = ("project", project_id) if project_id else ("global", "")
        with self.connection() as connection:
            if project_id and connection.execute("SELECT 1 FROM book_projects WHERE project_id = ?", (project_id,)).fetchone() is None:
                raise ValueError("Проєкт не знайдено.")
            if not text:
                connection.execute("DELETE FROM engine_instructions WHERE engine = ? AND scope = ? AND project_id = ?", (engine, scope, owner))
            else:
                connection.execute(
                    "INSERT INTO engine_instructions(engine, scope, project_id, text, updated_at) VALUES (?, ?, ?, ?, ?) "
                    "ON CONFLICT(engine, scope, project_id) DO UPDATE SET text = excluded.text, updated_at = excluded.updated_at",
                    (engine, scope, owner, text, _now()),
                )
        return text

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
                # A manually uploaded cover is a deliberate choice — it always wins,
                # regardless of what (if anything) this re-import's own EPUB carries.
                cover_image = existing_book["cover_image"]
                cover_uploaded_by_user = 1
            elif cover_image is None and existing_book and existing_book["cover_image"] is not None:
                # This re-import didn't carry its own cover (extraction failed, or the
                # replacement file simply has none embedded). Don't discard a perfectly
                # good cover that was auto-extracted from an earlier import just because
                # this particular one came up empty.
                cover_image = existing_book["cover_image"]
                cover_uploaded_by_user = 0
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
            variants_by_paragraph: dict[str, list[dict[str, Any]]] = {}
            for variant_row in connection.execute(
                "SELECT v.* FROM paragraph_translation_variants v "
                "JOIN book_paragraphs p ON p.paragraph_id = v.paragraph_id "
                "JOIN book_chapters c ON c.chapter_id = p.chapter_id "
                "WHERE c.book_id = ? ORDER BY v.created_at, v.rowid",
                (book["book_id"],),
            ).fetchall():
                variants_by_paragraph.setdefault(variant_row["paragraph_id"], []).append(self._variant_from_row(variant_row))
            chapters = []
            paragraph_count = 0
            for chapter in chapter_rows:
                elements = []
                element_rows = connection.execute("SELECT * FROM book_chapter_elements WHERE chapter_id = ? ORDER BY element_index", (chapter["chapter_id"],)).fetchall()
                for element in element_rows:
                    if element["element_type"] == "paragraph":
                        row = connection.execute("SELECT paragraph_id, original_text, word_count, translation_text, reviewed, proofread, is_service, queued_for_qa, narrator_change, selected_variant_id FROM book_paragraphs WHERE paragraph_id = ?", (element["element_id"],)).fetchone()
                        if row:
                            paragraph_count += 1
                            footnotes = []
                            for footnote_id in FOOTNOTE_TOKEN_RE.findall(row["translation_text"] or ""):
                                note_text = footnote_notes_by_id.get(footnote_id)
                                if note_text is None:
                                    continue
                                footnote_number += 1
                                footnotes.append({"footnoteId": footnote_id, "noteText": note_text, "number": footnote_number})
                            elements.append({"type": "paragraph", "paragraphId": row["paragraph_id"], "originalText": row["original_text"], "wordCount": row["word_count"], "translationText": row["translation_text"], "reviewed": bool(row["reviewed"]), "proofread": bool(row["proofread"]), "isService": bool(row["is_service"]), "queuedForQa": bool(row["queued_for_qa"]), "narratorChange": row["narrator_change"], "footnotes": footnotes, "selectedVariantId": row["selected_variant_id"], "translationVariants": variants_by_paragraph.get(row["paragraph_id"], [])})
                    else:
                        row = connection.execute("SELECT image_id, width, height FROM book_inline_images WHERE image_id = ?", (element["element_id"],)).fetchone()
                        if row:
                            elements.append({"type": "image", "imageId": row["image_id"], "width": row["width"], "height": row["height"]})
                chapters.append({
                    "chapterId": chapter["chapter_id"],
                    "title": chapter["title"], "translationTitle": chapter["translation_title"], "titleReviewed": bool(chapter["title_reviewed"]),
                    "excludeFromExport": bool(chapter["exclude_from_export"]),
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
                paragraphs.extend({"paragraphId": row["paragraph_id"], "chapterId": chapter["chapter_id"], "paragraphIndex": row["paragraph_index"], "originalText": row["original_text"], "wordCount": row["word_count"], "translationText": row["translation_text"], "reviewed": bool(row["reviewed"]), "isService": bool(row["is_service"])} for row in rows)
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

    def update_paragraph(self, paragraph_id: str, translation_text: str | None, reviewed: bool, is_service: bool | None = None, queued_for_qa: bool | None = None, proofread: bool | None = None) -> dict[str, Any] | None:
        """Low-level write of the chosen text. Variant bookkeeping is the caller's job
        (save_paragraph_edit, add_translation_variant); if the text no longer matches the
        selected variant, the selection is dropped rather than left pointing at other text."""
        translation_text = normalize_translation_text(translation_text)
        with self.connection() as connection:
            if not self._write_paragraph(connection, paragraph_id, translation_text, reviewed, is_service, queued_for_qa, proofread=proofread):
                return None
            row = connection.execute("SELECT * FROM book_paragraphs WHERE paragraph_id = ?", (paragraph_id,)).fetchone()
            if row["selected_variant_id"]:
                selected = connection.execute(
                    "SELECT text FROM paragraph_translation_variants WHERE variant_id = ?", (row["selected_variant_id"],)
                ).fetchone()
                if selected is None or _without_footnote_markers(selected["text"]) != _without_footnote_markers(translation_text):
                    connection.execute("UPDATE book_paragraphs SET selected_variant_id = NULL WHERE paragraph_id = ?", (paragraph_id,))
            return self._paragraph_payload(connection, paragraph_id)

    @staticmethod
    def _write_paragraph(
        connection: sqlite3.Connection,
        paragraph_id: str,
        translation_text: str | None,
        reviewed: bool,
        is_service: bool | None = None,
        queued_for_qa: bool | None = None,
        delete_orphaned_footnotes: bool = True,
        proofread: bool | None = None,
    ) -> bool:
        translation_text = normalize_translation_text(translation_text)
        set_clauses = ["translation_text = ?", "reviewed = ?"]
        params: list[Any] = [translation_text, int(reviewed)]
        if proofread is not None:  # None leaves «Вичитано» as it is (edits and replacements never clear it)
            set_clauses.append("proofread = ?")
            params.append(int(proofread))
        if is_service is not None:
            set_clauses.append("is_service = ?")
            params.append(int(is_service))
        if queued_for_qa is not None:
            set_clauses.append("queued_for_qa = ?")
            params.append(int(queued_for_qa))
        params.append(paragraph_id)
        cursor = connection.execute(
            f"UPDATE book_paragraphs SET {', '.join(set_clauses)} WHERE paragraph_id = ?",
            params,
        )
        if cursor.rowcount == 0:
            return False
        if delete_orphaned_footnotes:
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
        return True

    def get_paragraph(self, paragraph_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            return self._paragraph_payload(connection, paragraph_id)

    # --- translation variants -------------------------------------------------------

    @staticmethod
    def _variant_from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "variantId": row["variant_id"],
            "engine": row["engine"],
            "text": row["text"],
            "model": row["model"],
            "warnings": (_json(row["warnings"]) or []) if "warnings" in row.keys() else [],
            "promptHash": (row["prompt_hash"] if "prompt_hash" in row.keys() else None) or None,
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }

    def _list_variants(self, connection: sqlite3.Connection, paragraph_id: str) -> list[dict[str, Any]]:
        rows = connection.execute(
            "SELECT * FROM paragraph_translation_variants WHERE paragraph_id = ? ORDER BY created_at, rowid",
            (paragraph_id,),
        ).fetchall()
        return [self._variant_from_row(row) for row in rows]

    def _paragraph_payload(self, connection: sqlite3.Connection, paragraph_id: str) -> dict[str, Any] | None:
        row = connection.execute("SELECT * FROM book_paragraphs WHERE paragraph_id = ?", (paragraph_id,)).fetchone()
        if row is None:
            return None
        return {
            "paragraphId": row["paragraph_id"],
            "originalText": row["original_text"],
            "translationText": row["translation_text"],
            "reviewed": bool(row["reviewed"]),
            "proofread": bool(row["proofread"]),
            "isService": bool(row["is_service"]),
            "queuedForQa": bool(row["queued_for_qa"]),
            "selectedVariantId": row["selected_variant_id"],
            "translationVariants": self._list_variants(connection, paragraph_id),
        }

    @staticmethod
    def _prune_variants(connection: sqlite3.Connection, paragraph_id: str, engine: str) -> None:
        """Per (paragraph, engine) keep the newest VARIANT_VERSIONS_KEPT versions and the
        selected one; only what is beyond that and not selected is deleted."""
        selected = connection.execute(
            "SELECT selected_variant_id FROM book_paragraphs WHERE paragraph_id = ?", (paragraph_id,)
        ).fetchone()
        rows = connection.execute(
            "SELECT variant_id FROM paragraph_translation_variants WHERE paragraph_id = ? AND engine = ? "
            "ORDER BY created_at DESC, rowid DESC",
            (paragraph_id, engine),
        ).fetchall()
        keep = {row["variant_id"] for row in rows[:VARIANT_VERSIONS_KEPT]}
        if selected and selected["selected_variant_id"]:
            keep.add(selected["selected_variant_id"])
        stale = [(row["variant_id"],) for row in rows if row["variant_id"] not in keep]
        if stale:
            connection.executemany("DELETE FROM paragraph_translation_variants WHERE variant_id = ?", stale)

    @staticmethod
    def _migrate_usage_columns(connection: sqlite3.Connection) -> None:
        """queue_id and source_chars were added to translation_usage later; idempotent."""
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(translation_usage)")}
        if "queue_id" not in columns:
            connection.execute("ALTER TABLE translation_usage ADD COLUMN queue_id TEXT")
        if "source_chars" not in columns:
            connection.execute("ALTER TABLE translation_usage ADD COLUMN source_chars INTEGER")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_translation_usage_queue ON translation_usage(queue_id)")

    @staticmethod
    def _migrate_usage_kinds(connection: sqlite3.Connection) -> None:
        """A table made before kind 'dictionary' existed has a CHECK that rejects it: rebuild the table
        (same columns and rows, ids kept). Idempotent: does nothing once the CHECK allows it."""
        row = connection.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'translation_usage'").fetchone()
        if row is None or "'dictionary'" in (row["sql"] or ""):
            return
        connection.execute("DROP TABLE IF EXISTS translation_usage_new")
        connection.execute(
            "CREATE TABLE translation_usage_new ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "project_id TEXT NOT NULL REFERENCES book_projects(project_id) ON DELETE CASCADE, "
            "chapter_id TEXT, engine TEXT NOT NULL, model TEXT NOT NULL, "
            "kind TEXT NOT NULL CHECK(kind IN ('translate', 'retry', 'qa', 'analysis', 'chat', 'dictionary')), "
            "input_tokens INTEGER NOT NULL DEFAULT 0, output_tokens INTEGER NOT NULL DEFAULT 0, "
            "cache_read_tokens INTEGER NOT NULL DEFAULT 0, cache_write_tokens INTEGER NOT NULL DEFAULT 0, "
            "created_at TEXT NOT NULL, queue_id TEXT, source_chars INTEGER)"
        )
        connection.execute(
            "INSERT INTO translation_usage_new(id, project_id, chapter_id, engine, model, kind, input_tokens, output_tokens, "
            "cache_read_tokens, cache_write_tokens, created_at, queue_id, source_chars) "
            "SELECT id, project_id, chapter_id, engine, model, kind, input_tokens, output_tokens, "
            "cache_read_tokens, cache_write_tokens, created_at, queue_id, source_chars FROM translation_usage"
        )
        connection.execute("DROP TABLE translation_usage")
        connection.execute("ALTER TABLE translation_usage_new RENAME TO translation_usage")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_translation_usage_project ON translation_usage(project_id, chapter_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_translation_usage_queue ON translation_usage(queue_id)")

    # --- dictionary ---------------------------------------------------------------------------

    def paragraph_lookup_context(self, paragraph_id: str) -> dict[str, Any] | None:
        """What a dictionary lookup needs about a paragraph: its project, chapter, original text
        (with inline tags) and the chosen translation."""
        with self.connection() as connection:
            row = connection.execute(
                "SELECT p.paragraph_id, p.chapter_id, p.original_text, p.translation_text, d.project_id "
                "FROM book_paragraphs p JOIN book_chapters c ON c.chapter_id = p.chapter_id "
                "JOIN book_documents d ON d.book_id = c.book_id WHERE p.paragraph_id = ?",
                (paragraph_id,),
            ).fetchone()
        if row is None:
            return None
        return {"paragraphId": row["paragraph_id"], "chapterId": row["chapter_id"], "projectId": row["project_id"],
                "originalText": row["original_text"], "translationText": row["translation_text"]}

    def get_dictionary_cache(self, term_key: str, sentence_hash: str, model: str, mode: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT response FROM dictionary_cache WHERE term_key = ? AND sentence_hash = ? AND model = ? AND mode = ?",
                (term_key, sentence_hash, model, mode),
            ).fetchone()
        return _json(row["response"]) if row else None

    def put_dictionary_cache(self, term_key: str, sentence_hash: str, model: str, mode: str, response: dict[str, Any]) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO dictionary_cache(term_key, sentence_hash, model, mode, response, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (term_key, sentence_hash, model, mode, json.dumps(response, ensure_ascii=False), _now()),
            )

    def list_dictionary_cache(self, term_key: str, sentence_hash: str, model: str) -> list[tuple[str, dict[str, Any]]]:
        """(mode, response) of every cached answer for this term in this sentence, oldest first."""
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT mode, response FROM dictionary_cache WHERE term_key = ? AND sentence_hash = ? AND model = ? ORDER BY created_at, mode",
                (term_key, sentence_hash, model),
            ).fetchall()
        return [(row["mode"], _json(row["response"])) for row in rows]

    _SEED_TOMBSTONES_KEY = "deleted_seed_prices"

    def _migrate_model_prices(self, connection: sqlite3.Connection) -> None:
        """Idempotent. Adds the `source` column to a table made before it existed (rows that still
        hold the initial values become "seed", the rest "manual"), drops rows without any price
        (they would shadow the undated model), and seeds the initial prices that are missing and
        were not deleted on purpose. A price the user edited is never overwritten."""
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(model_prices)")}
        if "source" not in columns:
            connection.execute("ALTER TABLE model_prices ADD COLUMN source TEXT NOT NULL DEFAULT 'manual'")
            for model, (input_price, output_price, cache_read, cache_write) in DEFAULT_MODEL_PRICES.items():
                connection.execute(
                    "UPDATE model_prices SET source = 'seed' WHERE model = ? AND input_per_mtok IS ? AND output_per_mtok IS ? "
                    "AND cache_read_per_mtok IS ? AND cache_write_per_mtok IS ?",
                    (model, input_price, output_price, cache_read, cache_write),
                )
        tombstones = self._tombstones(connection)
        empty = connection.execute(
            "SELECT model FROM model_prices WHERE input_per_mtok IS NULL AND output_per_mtok IS NULL "
            "AND cache_read_per_mtok IS NULL AND cache_write_per_mtok IS NULL"
        ).fetchall()
        for record in empty:
            connection.execute("DELETE FROM model_prices WHERE model = ?", (record["model"],))
            if record["model"] in DEFAULT_MODEL_PRICES:
                tombstones.add(record["model"])
        self._store_tombstones(connection, tombstones)
        timestamp = _now()
        for model, (input_price, output_price, cache_read, cache_write) in DEFAULT_MODEL_PRICES.items():
            if model in tombstones:
                continue
            connection.execute(
                "INSERT OR IGNORE INTO model_prices(model, input_per_mtok, output_per_mtok, cache_read_per_mtok, cache_write_per_mtok, updated_at, source) "
                "VALUES (?, ?, ?, ?, ?, ?, 'seed')",
                (model, input_price, output_price, cache_read, cache_write, timestamp),
            )

    def _tombstones(self, connection: sqlite3.Connection) -> set[str]:
        record = connection.execute("SELECT value FROM app_settings WHERE key = ?", (self._SEED_TOMBSTONES_KEY,)).fetchone()
        try:
            return {item for item in json.loads(record["value"]) if isinstance(item, str)} if record else set()
        except (ValueError, TypeError):
            return set()

    def _store_tombstones(self, connection: sqlite3.Connection, tombstones: set[str]) -> None:
        connection.execute(
            "INSERT INTO app_settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (self._SEED_TOMBSTONES_KEY, json.dumps(sorted(tombstones))),
        )

    # --- settings ---------------------------------------------------------------------------

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        with self.connection() as connection:
            record = connection.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
        return record["value"] if record else default

    def set_setting(self, key: str, value: str) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO app_settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

    def get_timezone_name(self) -> str:
        """The time zone days are counted in: the stored one, or Europe/Kyiv when it is missing
        or no longer valid (never raises)."""
        stored = self.get_setting("timezone")
        return stored if resolve_timezone(stored) else DEFAULT_TIMEZONE

    def record_translation_usage(
        self, project_id: str | None, chapter_id: str | None, engine: str, model: str, kind: str, usage: Mapping[str, int],
        queue_id: str | None = None, source_chars: int | None = None,
    ) -> dict[str, Any] | None:
        """One row for one billed API call. Returns the stored row (None without a project)."""
        if not project_id:
            return None
        values = (
            project_id, chapter_id, engine, model or "", kind,
            int(usage.get("input_tokens", 0) or 0), int(usage.get("output_tokens", 0) or 0),
            int(usage.get("cache_read_input_tokens", 0) or 0), int(usage.get("cache_creation_input_tokens", 0) or 0),
            _now(), queue_id, source_chars,
        )
        with self.connection() as connection:
            cursor = connection.execute(
                "INSERT INTO translation_usage(project_id, chapter_id, engine, model, kind, input_tokens, output_tokens, "
                "cache_read_tokens, cache_write_tokens, created_at, queue_id, source_chars) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                values,
            )
            record = connection.execute("SELECT * FROM translation_usage WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return usage_row_from_record(record)

    def record_activity_minute(self, project_id: str, chapter_id: str | None, moment: datetime | None = None) -> bool:
        """One active minute (UTC, cut to the minute) of a project. INSERT OR IGNORE: pings of several tabs in
        the same minute are one row. A chapter that is not in this project is stored as NULL. False when the
        project does not exist."""
        moment = (moment or datetime.now(timezone.utc)).astimezone(timezone.utc)
        minute = moment.replace(second=0, microsecond=0).isoformat()
        with self.connection() as connection:
            if connection.execute("SELECT 1 FROM book_projects WHERE project_id = ?", (project_id,)).fetchone() is None:
                return False
            if chapter_id is not None and connection.execute(
                "SELECT 1 FROM book_chapters c JOIN book_documents d ON d.book_id = c.book_id "
                "WHERE c.chapter_id = ? AND d.project_id = ?", (chapter_id, project_id),
            ).fetchone() is None:
                chapter_id = None
            connection.execute(
                "INSERT OR IGNORE INTO activity_minutes(project_id, chapter_id, minute_utc) VALUES (?, ?, ?)",
                (project_id, chapter_id, minute),
            )
        return True

    def list_activity_minutes(self, project_id: str | None = None, since: str | None = None) -> list[dict[str, Any]]:
        """Active minutes of one project or of all, from an ISO UTC instant on."""
        query = "SELECT project_id, chapter_id, minute_utc FROM activity_minutes WHERE 1 = 1"
        params: list[Any] = []
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        if since:
            query += " AND minute_utc >= ?"
            params.append(since)
        with self.connection() as connection:
            records = connection.execute(query + " ORDER BY minute_utc", params).fetchall()
        return [{"projectId": r["project_id"], "chapterId": r["chapter_id"], "minuteUtc": r["minute_utc"]} for r in records]

    def list_translation_usage(self, project_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            records = connection.execute(
                "SELECT * FROM translation_usage WHERE project_id = ? ORDER BY id", (project_id,)
            ).fetchall()
        return [usage_row_from_record(record) for record in records]

    def usage_chapters(self, project_id: str) -> dict[str, dict[str, Any]]:
        """chapterId -> {chapterIndex, title} of the project's current book (titles only)."""
        with self.connection() as connection:
            records = connection.execute(
                "SELECT c.chapter_id, c.chapter_index, c.title FROM book_chapters c "
                "JOIN book_documents d ON d.book_id = c.book_id WHERE d.project_id = ?",
                (project_id,),
            ).fetchall()
        return {record["chapter_id"]: {"chapterIndex": record["chapter_index"], "title": record["title"]} for record in records}

    def list_translation_usage_all(self, project_id: str | None = None, since: str | None = None) -> list[dict[str, Any]]:
        """Usage rows of one project or of all, from an ISO UTC instant on."""
        query = "SELECT * FROM translation_usage WHERE 1 = 1"
        params: list[Any] = []
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        if since:
            query += " AND created_at >= ?"
            params.append(since)
        with self.connection() as connection:
            records = connection.execute(query + " ORDER BY id", params).fetchall()
        return [usage_row_from_record(record) for record in records]

    def list_queue_usage(self, queue_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            records = connection.execute("SELECT * FROM translation_usage WHERE queue_id = ? ORDER BY id", (queue_id,)).fetchall()
        return [usage_row_from_record(record) for record in records]

    def project_titles(self) -> dict[str, str]:
        with self.connection() as connection:
            return {record["project_id"]: record["title"] for record in connection.execute("SELECT project_id, title FROM book_projects")}

    @staticmethod
    def _price_entry(record: sqlite3.Row) -> dict[str, Any]:
        return {
            "model": record["model"],
            "inputPerMTok": record["input_per_mtok"],
            "outputPerMTok": record["output_per_mtok"],
            "cacheReadPerMTok": record["cache_read_per_mtok"],
            "cacheWritePerMTok": record["cache_write_per_mtok"],
            "updatedAt": record["updated_at"],
            "source": record["source"],
        }

    def list_model_prices(self) -> dict[str, dict[str, Any]]:
        with self.connection() as connection:
            records = connection.execute("SELECT * FROM model_prices ORDER BY model").fetchall()
        return {record["model"]: self._price_entry(record) for record in records}

    def save_model_prices(self, prices: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """The user's edits. A row whose prices changed becomes source "manual"; an unchanged one
        keeps its source and date. A row with no price at all is deleted (a deleted initial model
        stays deleted until restore_default_prices())."""
        timestamp = _now()
        with self.connection() as connection:
            tombstones = self._tombstones(connection)
            for item in prices:
                model = item["model"]
                values = tuple(item.get(key) for key in PRICE_KEYS)
                if all(value is None for value in values):
                    connection.execute("DELETE FROM model_prices WHERE model = ?", (model,))
                    if model in DEFAULT_MODEL_PRICES:
                        tombstones.add(model)
                    continue
                existing = connection.execute("SELECT * FROM model_prices WHERE model = ?", (model,)).fetchone()
                if existing is not None and tuple(existing[column] for column in (
                    "input_per_mtok", "output_per_mtok", "cache_read_per_mtok", "cache_write_per_mtok")) == values:
                    continue
                connection.execute(
                    "INSERT INTO model_prices(model, input_per_mtok, output_per_mtok, cache_read_per_mtok, cache_write_per_mtok, updated_at, source) "
                    "VALUES (?, ?, ?, ?, ?, ?, 'manual') ON CONFLICT(model) DO UPDATE SET input_per_mtok = excluded.input_per_mtok, "
                    "output_per_mtok = excluded.output_per_mtok, cache_read_per_mtok = excluded.cache_read_per_mtok, "
                    "cache_write_per_mtok = excluded.cache_write_per_mtok, updated_at = excluded.updated_at, source = 'manual'",
                    (model, *values, timestamp),
                )
            self._store_tombstones(connection, tombstones)
        return self.list_model_prices()

    def restore_default_prices(self) -> list[str]:
        """Put back the initial prices of initial models that are missing (deleted). A model that
        exists, whatever its source, is not touched."""
        timestamp = _now()
        restored = []
        with self.connection() as connection:
            tombstones = self._tombstones(connection)
            for model, values in DEFAULT_MODEL_PRICES.items():
                if connection.execute("SELECT 1 FROM model_prices WHERE model = ?", (model,)).fetchone():
                    tombstones.discard(model)
                    continue
                connection.execute(
                    "INSERT INTO model_prices(model, input_per_mtok, output_per_mtok, cache_read_per_mtok, cache_write_per_mtok, updated_at, source) "
                    "VALUES (?, ?, ?, ?, ?, ?, 'seed')",
                    (model, *values, timestamp),
                )
                tombstones.discard(model)
                restored.append(model)
            self._store_tombstones(connection, tombstones)
        return restored

    def apply_list_prices(self, updates: dict[str, dict[str, Any]], overwrite_manual: bool) -> tuple[list[str], list[str]]:
        """Write prices taken from the public list (source "list"). Rows the user edited by hand
        (source "manual") are skipped unless overwrite_manual. Returns (applied, skipped_manual)."""
        timestamp = _now()
        applied: list[str] = []
        skipped: list[str] = []
        with self.connection() as connection:
            tombstones = self._tombstones(connection)
            for model, entry in updates.items():
                existing = connection.execute("SELECT source FROM model_prices WHERE model = ?", (model,)).fetchone()
                if existing is not None and existing["source"] == "manual" and not overwrite_manual:
                    skipped.append(model)
                    continue
                connection.execute(
                    "INSERT INTO model_prices(model, input_per_mtok, output_per_mtok, cache_read_per_mtok, cache_write_per_mtok, updated_at, source) "
                    "VALUES (?, ?, ?, ?, ?, ?, 'list') ON CONFLICT(model) DO UPDATE SET input_per_mtok = excluded.input_per_mtok, "
                    "output_per_mtok = excluded.output_per_mtok, cache_read_per_mtok = excluded.cache_read_per_mtok, "
                    "cache_write_per_mtok = excluded.cache_write_per_mtok, updated_at = excluded.updated_at, source = 'list'",
                    (model, *(entry.get(key) for key in PRICE_KEYS), timestamp),
                )
                tombstones.discard(model)
                applied.append(model)
            self._store_tombstones(connection, tombstones)
        return applied, skipped

    def _migrate_translation_variants(self, connection: sqlite3.Connection) -> None:
        """Existing translations become the variant "current" ("Поточний") and stay chosen.
        Only paragraphs that have no variants at all are touched, so this runs safely on every start."""
        rows = connection.execute(
            "SELECT paragraph_id, translation_text FROM book_paragraphs p "
            "WHERE p.selected_variant_id IS NULL AND TRIM(COALESCE(p.translation_text, '')) != '' "
            "AND NOT EXISTS (SELECT 1 FROM paragraph_translation_variants v WHERE v.paragraph_id = p.paragraph_id)"
        ).fetchall()
        timestamp = _now()
        for row in rows:
            variant_id = _new_id("variant")
            connection.execute(
                "INSERT INTO paragraph_translation_variants(variant_id, paragraph_id, engine, text, model, created_at, updated_at) "
                "VALUES (?, ?, 'current', ?, NULL, ?, ?)",
                (variant_id, row["paragraph_id"], row["translation_text"], timestamp, timestamp),
            )
            connection.execute(
                "UPDATE book_paragraphs SET selected_variant_id = ? WHERE paragraph_id = ?",
                (variant_id, row["paragraph_id"]),
            )

    def add_translation_variant(
        self, paragraph_id: str, engine: str, text: str, model: str | None = None, warnings: list[dict[str, Any]] | None = None,
        prompt_hash: str | None = None,
    ) -> dict[str, Any] | None:
        """Store an engine's translation as a new version of the (paragraph, engine) variant;
        nothing is overwritten, and text identical to the newest version adds nothing. It becomes
        the chosen text only when the paragraph has no chosen variant yet; otherwise
        translation_text (and reviewed) stay untouched."""
        with self.connection() as connection:
            exists, _created, _auto = self._add_variant_in(connection, paragraph_id, engine, text, model, warnings, prompt_hash)
            if not exists:
                return None
            return self._paragraph_payload(connection, paragraph_id)

    def _add_variant_in(
        self, connection: sqlite3.Connection, paragraph_id: str, engine: str, text: str, model: str | None,
        warnings: list[dict[str, Any]] | None, prompt_hash: str | None = None,
    ) -> tuple[bool, str | None, bool]:
        """(paragraph exists, id of the version created or None when the text equals the newest one,
        whether it became the chosen text). Shared by the single translate and the queue."""
        if engine not in TRANSLATION_ENGINES or engine in {"current", "manual"}:
            raise ValueError(f"Unknown translation engine: {engine}")
        text = normalize_translation_text(text) or ""
        row = connection.execute("SELECT * FROM book_paragraphs WHERE paragraph_id = ?", (paragraph_id,)).fetchone()
        if row is None:
            return False, None, False
        newest = connection.execute(
            "SELECT text FROM paragraph_translation_variants WHERE paragraph_id = ? AND engine = ? "
            "ORDER BY created_at DESC, rowid DESC LIMIT 1",
            (paragraph_id, engine),
        ).fetchone()
        if newest is not None and newest["text"] == text:
            # Same text as this engine's newest version: no duplicate version.
            return True, None, False
        timestamp = _now()
        variant_id = _new_id("variant")
        connection.execute(
            "INSERT INTO paragraph_translation_variants(variant_id, paragraph_id, engine, text, model, created_at, updated_at, warnings, prompt_hash) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (variant_id, paragraph_id, engine, text, model, timestamp, timestamp,
             json.dumps(warnings, ensure_ascii=False) if warnings else None, prompt_hash or None),
        )
        auto_selected = False
        if not row["selected_variant_id"]:
            chosen, _moved = _with_carried_footnote_markers(text, row["translation_text"])
            self._write_paragraph(connection, paragraph_id, chosen, False, delete_orphaned_footnotes=False)
            connection.execute("UPDATE book_paragraphs SET selected_variant_id = ? WHERE paragraph_id = ?", (variant_id, paragraph_id))
            auto_selected = True
        self._prune_variants(connection, paragraph_id, engine)
        return True, variant_id, auto_selected

    def select_translation_variant(self, paragraph_id: str, variant_id: str) -> dict[str, Any] | None:
        """"У файл": copy a variant into translation_text. Footnote markers the previous text
        had are appended (never dropped, so no footnote is deleted); reviewed is cleared when
        the chosen text actually changes. The response's "previous" is the undo state."""
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM book_paragraphs WHERE paragraph_id = ?", (paragraph_id,)).fetchone()
            if row is None:
                return None
            variant = connection.execute(
                "SELECT * FROM paragraph_translation_variants WHERE variant_id = ? AND paragraph_id = ?", (variant_id, paragraph_id)
            ).fetchone()
            if variant is None:
                raise ValueError("Варіант перекладу не знайдено.")
            previous, moved = self._choose_variant(connection, row, variant)
            payload = self._paragraph_payload(connection, paragraph_id)
        return {**payload, "movedFootnoteIds": moved, "previous": previous}

    def _choose_variant(self, connection: sqlite3.Connection, row: sqlite3.Row, variant: sqlite3.Row) -> tuple[dict[str, Any], list[str]]:
        """The one place a variant becomes the chosen text (single «У файл» and the bulk action
        use it, so footnote and reviewed rules cannot drift). Returns (undo state, moved footnote ids)."""
        paragraph_id = row["paragraph_id"]
        previous = self._selection_state(connection, row)
        chosen, moved = _with_carried_footnote_markers(variant["text"], row["translation_text"])
        changed = chosen != (row["translation_text"] or "")
        self._write_paragraph(
            connection, paragraph_id, chosen, bool(row["reviewed"]) and not changed, delete_orphaned_footnotes=False,
            proofread=bool(row["proofread"]) and not changed,
        )
        connection.execute("UPDATE book_paragraphs SET selected_variant_id = ? WHERE paragraph_id = ?", (variant["variant_id"], paragraph_id))
        if previous["variant"]:
            self._prune_variants(connection, paragraph_id, previous["variant"]["engine"])
        return previous, moved

    def _selection_state(self, connection: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
        variant = None
        if row["selected_variant_id"]:
            variant_row = connection.execute(
                "SELECT * FROM paragraph_translation_variants WHERE variant_id = ?", (row["selected_variant_id"],)
            ).fetchone()
            variant = self._variant_from_row(variant_row) if variant_row else None
        return {
            "selectedVariantId": row["selected_variant_id"],
            "translationText": row["translation_text"],
            "reviewed": bool(row["reviewed"]),
            "proofread": bool(row["proofread"]),
            "variant": variant,
        }

    def restore_translation_selection(self, paragraph_id: str, state: dict[str, Any]) -> dict[str, Any] | None:
        """Undo of "У файл": put back the chosen text, reviewed flag and selected variant
        exactly as they were (re-creating that variant if it has been pruned since),
        without recording a manual edit. Footnotes are never deleted here."""
        if not isinstance(state, dict):
            raise ValueError("Некоректний стан для скасування.")
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM book_paragraphs WHERE paragraph_id = ?", (paragraph_id,)).fetchone()
            if row is None:
                return None
            self._restore_selection(connection, row, state)
            return self._paragraph_payload(connection, paragraph_id)

    def _restore_selection(self, connection: sqlite3.Connection, row: sqlite3.Row, state: dict[str, Any]) -> None:
        paragraph_id = row["paragraph_id"]
        variant = state.get("variant")
        selected_id = state.get("selectedVariantId") or None
        if selected_id and isinstance(variant, dict) and variant.get("variantId") == selected_id:
            exists = connection.execute(
                "SELECT 1 FROM paragraph_translation_variants WHERE variant_id = ?", (selected_id,)
            ).fetchone()
            if exists is None:
                engine = variant.get("engine")
                if engine not in TRANSLATION_ENGINES:
                    raise ValueError("Некоректний стан для скасування.")
                connection.execute(
                    "INSERT INTO paragraph_translation_variants(variant_id, paragraph_id, engine, text, model, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (selected_id, paragraph_id, engine, str(variant.get("text") or ""), variant.get("model"),
                     variant.get("createdAt") or _now(), variant.get("updatedAt") or _now()),
                )
        elif selected_id and connection.execute(
            "SELECT 1 FROM paragraph_translation_variants WHERE variant_id = ? AND paragraph_id = ?", (selected_id, paragraph_id)
        ).fetchone() is None:
            selected_id = None
        text, _moved = _with_carried_footnote_markers(str(state.get("translationText") or ""), row["translation_text"])
        self._write_paragraph(
            connection, paragraph_id, text or None, bool(state.get("reviewed")), delete_orphaned_footnotes=False,
            proofread=bool(state.get("proofread")),
        )
        connection.execute("UPDATE book_paragraphs SET selected_variant_id = ? WHERE paragraph_id = ?", (selected_id, paragraph_id))

    # --- the whole chapter at once ----------------------------------------------------------------

    @staticmethod
    def _shorten(text: str | None, limit: int = BULK_EXAMPLE_CHARS) -> str:
        plain = " ".join(_without_footnote_markers(text).split())
        return plain if len(plain) <= limit else plain[: limit - 1].rstrip() + "…"

    def select_chapter_variants(
        self, chapter_id: str, engine: str, include_reviewed: bool = False, dry_run: bool = False
    ) -> dict[str, Any] | None:
        """«Обрати для файлу весь розділ з…»: for every paragraph of the chapter that has a variant of
        `engine`, the newest version becomes the chosen text, exactly like «У файл». Paragraphs
        without such a variant are not touched; proofread ones are skipped unless include_reviewed;
        one that already has that version chosen is left alone. All or nothing (one transaction).
        With dry_run nothing is written: only the summary and up to three examples come back."""
        if engine not in BULK_SELECTION_ENGINES:
            raise ValueError("Невідомий рушій для масового вибору.")
        with self.connection() as connection:
            if connection.execute("SELECT 1 FROM book_chapters WHERE chapter_id = ?", (chapter_id,)).fetchone() is None:
                return None
            rows = connection.execute(
                "SELECT * FROM book_paragraphs WHERE chapter_id = ? ORDER BY paragraph_index", (chapter_id,)
            ).fetchall()
            summary = {"changed": 0, "withoutVariant": 0, "skippedReviewed": 0, "alreadySelected": 0, "movedFootnotes": 0,
                       "reviewedUnmarked": 0, "proofreadUnmarked": 0}
            plan: list[tuple[int, sqlite3.Row, sqlite3.Row]] = []
            for number, row in enumerate(rows, 1):
                variant = connection.execute(
                    "SELECT * FROM paragraph_translation_variants WHERE paragraph_id = ? AND engine = ? "
                    "ORDER BY created_at DESC, rowid DESC LIMIT 1",
                    (row["paragraph_id"], engine),
                ).fetchone()
                if variant is None:
                    summary["withoutVariant"] += 1
                elif row["selected_variant_id"] == variant["variant_id"]:
                    summary["alreadySelected"] += 1
                elif (row["reviewed"] or row["proofread"]) and not include_reviewed:
                    summary["skippedReviewed"] += 1
                else:
                    plan.append((number, row, variant))
            summary["changed"] = len(plan)
            examples = [
                {"number": number, "before": self._shorten(row["translation_text"]), "after": self._shorten(variant["text"]),
                 "reviewed": bool(row["reviewed"]), "proofread": bool(row["proofread"])}
                for number, row, variant in plan[:BULK_EXAMPLE_COUNT]
            ]
            paragraphs: list[dict[str, Any]] = []
            undo_items: list[dict[str, Any]] = []
            for _number, row, variant in plan:
                new_text, would_move = _with_carried_footnote_markers(variant["text"], row["translation_text"])
                summary["movedFootnotes"] += 1 if would_move else 0
                # a proofread paragraph keeps «Перевірено» only when the chosen text is the same
                summary["reviewedUnmarked"] += 1 if row["reviewed"] and new_text != (row["translation_text"] or "") else 0
                summary["proofreadUnmarked"] += 1 if row["proofread"] and new_text != (row["translation_text"] or "") else 0
                if dry_run:
                    continue
                previous, _moved = self._choose_variant(connection, row, variant)
                undo_items.append({"paragraphId": row["paragraph_id"], "variantId": variant["variant_id"], "previous": previous})
                paragraphs.append(self._paragraph_payload(connection, row["paragraph_id"]))
        return {
            "chapterId": chapter_id, "engine": engine, "includeReviewed": bool(include_reviewed), "dryRun": bool(dry_run),
            "summary": summary, "examples": examples, "paragraphs": paragraphs, "undo": {"items": undo_items},
        }

    def _chapter_items(self, connection: sqlite3.Connection, chapter_id: str, items: Any, keys: tuple[str, ...]) -> list[dict[str, Any]]:
        """Validate the items of a bulk request: every paragraph must belong to this chapter."""
        if not isinstance(items, list) or len(items) > BULK_SELECTION_MAX_ITEMS:
            raise ValueError("Некоректний список абзаців.")
        in_chapter = {
            record["paragraph_id"]
            for record in connection.execute("SELECT paragraph_id FROM book_paragraphs WHERE chapter_id = ?", (chapter_id,))
        }
        seen: set[str] = set()
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("paragraphId"), str) or item["paragraphId"] in seen:
                raise ValueError("Некоректний список абзаців.")
            if item["paragraphId"] not in in_chapter:
                raise ValueError("Абзац не належить цьому розділу.")
            if not all(key in item for key in keys):
                raise ValueError("Некоректний список абзаців.")
            seen.add(item["paragraphId"])
        return items

    def restore_chapter_selection(self, chapter_id: str, items: Any) -> dict[str, Any] | None:
        """Undo of the whole-chapter choice: every listed paragraph gets back its chosen text, reviewed
        flag, selected variant and footnote markers (a pruned selected variant is re-created), as in the
        single undo. One transaction: if one item is invalid nothing is restored."""
        with self.connection() as connection:
            if connection.execute("SELECT 1 FROM book_chapters WHERE chapter_id = ?", (chapter_id,)).fetchone() is None:
                return None
            items = self._chapter_items(connection, chapter_id, items, ("previous",))
            paragraphs = []
            for item in items:
                if not isinstance(item["previous"], dict):
                    raise ValueError("Некоректний стан для скасування.")
                row = connection.execute("SELECT * FROM book_paragraphs WHERE paragraph_id = ?", (item["paragraphId"],)).fetchone()
                self._restore_selection(connection, row, item["previous"])
                paragraphs.append(self._paragraph_payload(connection, item["paragraphId"]))
        return {"chapterId": chapter_id, "restored": len(paragraphs), "paragraphs": paragraphs}

    def apply_chapter_selection(self, chapter_id: str, items: Any) -> dict[str, Any] | None:
        """Redo of the whole-chapter choice: the exact variants given (not "the newest" again), each as
        «У файл». One transaction. Returns the new undo state like select_chapter_variants."""
        with self.connection() as connection:
            if connection.execute("SELECT 1 FROM book_chapters WHERE chapter_id = ?", (chapter_id,)).fetchone() is None:
                return None
            items = self._chapter_items(connection, chapter_id, items, ("variantId",))
            paragraphs, undo_items = [], []
            for item in items:
                row = connection.execute("SELECT * FROM book_paragraphs WHERE paragraph_id = ?", (item["paragraphId"],)).fetchone()
                variant = connection.execute(
                    "SELECT * FROM paragraph_translation_variants WHERE variant_id = ? AND paragraph_id = ?",
                    (item["variantId"], item["paragraphId"]),
                ).fetchone()
                if variant is None:
                    raise ValueError("Варіант перекладу не знайдено.")
                previous, _moved = self._choose_variant(connection, row, variant)
                undo_items.append({"paragraphId": item["paragraphId"], "variantId": item["variantId"], "previous": previous})
                paragraphs.append(self._paragraph_payload(connection, item["paragraphId"]))
        return {"chapterId": chapter_id, "applied": len(paragraphs), "paragraphs": paragraphs, "undo": {"items": undo_items}}

    # --- «Знайти й замінити» in the translation text ---------------------------------------------------

    REPLACE_SAMPLE_COUNT = 5
    REPLACE_LIST_LIMIT = 1000

    @staticmethod
    def _replace_request(data: Any) -> dict[str, Any]:
        """Validate a find/replace request body."""
        if not isinstance(data, dict):
            raise ValueError("Некоректний запит.")
        query, replacement = data.get("query"), data.get("replacement", "")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Вкажіть, що шукати.")
        if len(query) > MAX_QUERY_CHARS:
            raise ValueError("Запит задовгий.")
        if not _CYRILLIC_RE.search(query):
            raise ValueError("Заміна доступна лише для кириличного запиту: вона працює по тексту перекладу, не оригіналу.")
        if not isinstance(replacement, str) or len(replacement) > MAX_REPLACEMENT_CHARS or any(ord(ch) < 32 or ch == "\uE000" for ch in replacement):
            raise ValueError("Некоректний текст заміни.")
        options = data.get("options") if isinstance(data.get("options"), dict) else {}
        mode = options.get("mode", "start")
        match_case = options.get("matchCase", False)
        if mode not in REPLACE_MODES or not isinstance(match_case, bool):
            raise ValueError("Некоректні опції пошуку.")
        scope = data.get("scope", "chapter")
        if scope not in ("chapter", "project"):
            raise ValueError("Область має бути chapter або project.")
        if scope == "chapter" and not isinstance(data.get("chapterId"), str):
            raise ValueError("Вкажіть розділ.")
        target = data.get("target")
        if target is not None and (
            not isinstance(target, dict) or not isinstance(target.get("paragraphId"), str)
            or isinstance(target.get("occurrence"), bool) or not isinstance(target.get("occurrence"), int) or target["occurrence"] < 0
        ):
            raise ValueError("Некоректний збіг для заміни.")
        include_variants = data.get("includeVariants", False)
        if not isinstance(include_variants, bool):
            raise ValueError("Некоректна опція варіантів.")
        return {
            "matcher": Matcher(query, replacement, match_case, mode), "scope": scope, "chapterId": data.get("chapterId"),
            "target": target, "includeVariants": include_variants, "dryRun": bool(data.get("dryRun", False)),
            "returnChapterId": data.get("returnChapterId") if isinstance(data.get("returnChapterId"), str) else None,
        }

    def _replace_rows(self, connection: sqlite3.Connection, project_id: str, scope: str, chapter_id: str | None) -> list[sqlite3.Row] | None:
        """The paragraphs with a translation in the scope, in book order; None for an unknown project/chapter."""
        if connection.execute("SELECT 1 FROM book_projects WHERE project_id = ?", (project_id,)).fetchone() is None:
            return None
        conditions, params = ["doc.project_id = ?", "bp.is_service = 0", "bp.translation_text IS NOT NULL", "bp.translation_text != ''"], [project_id]
        if scope == "chapter":
            owned = connection.execute(
                "SELECT 1 FROM book_chapters ch JOIN book_documents doc ON doc.book_id = ch.book_id "
                "WHERE ch.chapter_id = ? AND doc.project_id = ?", (chapter_id, project_id),
            ).fetchone()
            if owned is None:
                return None
            conditions.append("bp.chapter_id = ?")
            params.append(chapter_id)
        return connection.execute(
            "SELECT bp.*, ch.chapter_index, ch.title AS chapter_title, ch.translation_title AS chapter_translation_title, "
            "ch.paragraph_count AS chapter_paragraph_count FROM book_paragraphs bp "
            "JOIN book_chapters ch ON ch.chapter_id = bp.chapter_id JOIN book_documents doc ON doc.book_id = ch.book_id "
            f"WHERE {' AND '.join(conditions)} ORDER BY ch.chapter_index, bp.paragraph_index", params,
        ).fetchall()

    def find_translation_matches(self, project_id: str, data: Any) -> dict[str, Any] | None:
        """Every match of the query in the chosen translation text of the scope, in book order, with a short
        context, plus how many matches cross formatting and are therefore left alone."""
        request = self._replace_request(data)
        matcher: Matcher = request["matcher"]
        with self.connection() as connection:
            rows = self._replace_rows(connection, project_id, request["scope"], request["chapterId"])
            if rows is None:
                return None
            matches, paragraphs, chapters, reviewed, proofread, across = [], 0, set(), 0, 0, 0
            total = 0
            for row in rows:
                scan = matcher.scan(row["translation_text"])
                across += scan.across
                if not scan.matches:
                    continue
                paragraphs += 1
                chapters.add(row["chapter_id"])
                reviewed += 1 if row["reviewed"] else 0
                proofread += 1 if row["proofread"] else 0
                for occurrence, match in enumerate(scan.matches):
                    total += 1
                    if len(matches) < self.REPLACE_LIST_LIMIT:
                        matches.append({
                            "paragraphId": row["paragraph_id"], "chapterId": row["chapter_id"], "chapterIndex": row["chapter_index"],
                            "paragraphIndex": row["paragraph_index"], "chapterTitle": row["chapter_translation_title"] or row["chapter_title"], "occurrence": occurrence,
                            "snippet": replace_context(scan.visible, match.visible_start, match.visible_end, match.old),
                            "matchedText": match.old, "visibleStart": match.visible_start, "visibleEnd": match.visible_end,
                            "reviewed": bool(row["reviewed"]), "proofread": bool(row["proofread"]),
                            "positionPercent": round((row["paragraph_index"] + 1) / (row["chapter_paragraph_count"] or 1) * 100, 1),
                        })
        return {"total": total, "paragraphs": paragraphs, "chapters": len(chapters), "reviewedParagraphs": reviewed,
                "proofreadParagraphs": proofread, "acrossMarkup": across, "truncated": total > len(matches), "matches": matches}

    def _replacement_snapshot(self, connection: sqlite3.Connection, row: sqlite3.Row, variant_ids: list[str]) -> dict[str, Any]:
        """What the undo of a replacement needs: the chosen text, reviewed flag and selected variant, the
        manual variant (it is rewritten by the replacement) and the text of the engine variants touched."""
        manual = connection.execute(
            "SELECT variant_id, text FROM paragraph_translation_variants WHERE paragraph_id = ? AND engine = 'manual'", (row["paragraph_id"],)
        ).fetchone()
        variants = []
        for variant_id in variant_ids:
            record = connection.execute("SELECT text FROM paragraph_translation_variants WHERE variant_id = ?", (variant_id,)).fetchone()
            variants.append({"variantId": variant_id, "text": record["text"]})
        return {
            "selection": self._selection_state(connection, row),
            "manual": {"variantId": manual["variant_id"], "text": manual["text"]} if manual else None,
            "variants": variants,
        }

    def _apply_replacements(self, connection: sqlite3.Connection, plan: list[tuple[sqlite3.Row, str | None, list[tuple[str, str]]]]) -> list[dict[str, Any]]:
        """Write the planned texts: the chosen text as a manual edit («Перевірено» stays as it was), the engine
        variants' texts in place. Returns the undo items. Runs inside the caller's transaction."""
        undo: list[dict[str, Any]] = []
        timestamp = _now()
        for row, new_text, variant_updates in plan:
            new_text = normalize_translation_text(new_text)
            variant_updates = [(variant_id, normalize_translation_text(text) or "") for variant_id, text in variant_updates]
            previous = self._replacement_snapshot(connection, row, [variant_id for variant_id, _text in variant_updates])
            for variant_id, text in variant_updates:
                connection.execute(
                    "UPDATE paragraph_translation_variants SET text = ?, updated_at = ? WHERE variant_id = ? AND paragraph_id = ?",
                    (text, timestamp, variant_id, row["paragraph_id"]),
                )
            if new_text is not None and new_text != (row["translation_text"] or ""):
                self._manual_edit_in(connection, row, new_text)
                self._write_paragraph(connection, row["paragraph_id"], new_text, bool(row["reviewed"]))
            undo.append({
                "paragraphId": row["paragraph_id"], "chapterId": row["chapter_id"], "previous": previous,
                "text": new_text if new_text is not None else row["translation_text"],
                "variants": [{"variantId": variant_id, "text": text} for variant_id, text in variant_updates],
            })
        return undo

    def _replacement_result(self, connection: sqlite3.Connection, undo: list[dict[str, Any]], return_chapter_id: str | None) -> dict[str, Any]:
        chapter_ids = list(dict.fromkeys(item["chapterId"] for item in undo))
        paragraphs = [
            self._paragraph_payload(connection, item["paragraphId"]) for item in undo
            if return_chapter_id and item["chapterId"] == return_chapter_id
        ]
        return {"chapterIds": chapter_ids, "paragraphs": paragraphs, "undo": {"items": undo}}

    def replace_in_translation(self, project_id: str, data: Any) -> dict[str, Any] | None:
        """«Замінити» (one match: `target`) and «Замінити все» (every match in the chapter or the project).
        Only text between tags and footnote markers changes. The chosen text is written as a manual edit and
        «Перевірено» is kept. With includeVariants the engine variants get the same replacement. All or
        nothing. With dryRun nothing is written: the summary and the first matches come back."""
        request = self._replace_request(data)
        matcher: Matcher = request["matcher"]
        target = request["target"]
        with self.connection() as connection:
            rows = self._replace_rows(connection, project_id, request["scope"], request["chapterId"])
            if rows is None:
                return None
            summary = {"matches": 0, "paragraphs": 0, "chapters": 0, "reviewedParagraphs": 0, "proofreadParagraphs": 0, "acrossMarkup": 0, "variantsChanged": 0}
            examples: list[dict[str, Any]] = []
            replaced_info: list[dict[str, Any]] = []
            plan: list[tuple[sqlite3.Row, str | None, list[tuple[str, str]]]] = []
            chapters: set[str] = set()
            for row in rows:
                if target and row["paragraph_id"] != target["paragraphId"]:
                    continue
                scan = matcher.scan(row["translation_text"])
                summary["acrossMarkup"] += scan.across
                only = target["occurrence"] if target else None
                if only is not None and only >= len(scan.matches):
                    raise ValueError("Збіг уже змінився. Оновіть список і спробуйте ще раз.")
                new_text, replaced = matcher.replace(row["translation_text"], scan.matches, only)
                variant_updates: list[tuple[str, str]] = []
                if request["includeVariants"]:
                    for variant in connection.execute(
                        "SELECT variant_id, text FROM paragraph_translation_variants WHERE paragraph_id = ? AND engine != 'manual' "
                        "ORDER BY created_at, rowid", (row["paragraph_id"],),
                    ):
                        changed, variant_matches = matcher.replace(variant["text"])
                        if variant_matches:
                            variant_updates.append((variant["variant_id"], changed))
                if not replaced and not variant_updates:
                    continue
                summary["matches"] += len(replaced)
                summary["paragraphs"] += 1
                summary["reviewedParagraphs"] += 1 if row["reviewed"] else 0
                summary["proofreadParagraphs"] += 1 if row["proofread"] else 0
                summary["variantsChanged"] += len(variant_updates)
                chapters.add(row["chapter_id"])
                if target and replaced:
                    # where the next «Замінити» should continue: right after the new text
                    replaced_info.append({"paragraphId": row["paragraph_id"], "chapterIndex": row["chapter_index"],
                                          "paragraphIndex": row["paragraph_index"], "visibleStart": replaced[0].visible_start,
                                          "newLength": len(replaced[0].new)})
                for match in replaced:
                    if len(examples) < self.REPLACE_SAMPLE_COUNT:
                        examples.append({
                            "chapterIndex": row["chapter_index"], "paragraphId": row["paragraph_id"],
                            "before": replace_context(scan.visible, match.visible_start, match.visible_end, match.old),
                            "after": replace_context(scan.visible, match.visible_start, match.visible_end, match.new),
                        })
                plan.append((row, new_text if replaced else None, variant_updates))
            summary["chapters"] = len(chapters)
            if target and not plan:
                raise ValueError("Збіг не знайдено.")
            result: dict[str, Any] = {"summary": summary, "examples": examples, "dryRun": request["dryRun"], "replaced": replaced_info}
            if request["dryRun"]:
                return {**result, "chapterIds": [], "paragraphs": [], "undo": {"items": []}}
            undo = self._apply_replacements(connection, plan)
            return {**result, **self._replacement_result(connection, undo, request["returnChapterId"])}

    def _replacement_items(self, connection: sqlite3.Connection, project_id: str, items: Any, keys: tuple[str, ...]) -> list[sqlite3.Row]:
        if not isinstance(items, list) or not items or len(items) > BULK_SELECTION_MAX_ITEMS:
            raise ValueError("Некоректний список абзаців.")
        seen: set[str] = set()
        rows = []
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("paragraphId"), str) or item["paragraphId"] in seen or not all(key in item for key in keys):
                raise ValueError("Некоректний список абзаців.")
            seen.add(item["paragraphId"])
            row = connection.execute(
                "SELECT bp.* FROM book_paragraphs bp JOIN book_chapters ch ON ch.chapter_id = bp.chapter_id "
                "JOIN book_documents doc ON doc.book_id = ch.book_id WHERE bp.paragraph_id = ? AND doc.project_id = ?",
                (item["paragraphId"], project_id),
            ).fetchone()
            if row is None:
                raise ValueError("Абзац не належить цьому проєкту.")
            rows.append(row)
        return rows

    def restore_replacement(self, project_id: str, items: Any, return_chapter_id: str | None = None) -> dict[str, Any] | None:
        """Undo of a replacement: every paragraph gets back its chosen text, reviewed flag, selected variant,
        manual variant and the engine variants' texts. One transaction."""
        with self.connection() as connection:
            if connection.execute("SELECT 1 FROM book_projects WHERE project_id = ?", (project_id,)).fetchone() is None:
                return None
            rows = self._replacement_items(connection, project_id, items, ("previous",))
            restored = []
            for row, item in zip(rows, items):
                previous = item["previous"]
                if not isinstance(previous, dict) or not isinstance(previous.get("selection"), dict):
                    raise ValueError("Некоректний стан для скасування.")
                for variant in previous.get("variants") or []:
                    if not isinstance(variant, dict) or not isinstance(variant.get("variantId"), str):
                        raise ValueError("Некоректний стан для скасування.")
                    connection.execute(
                        "UPDATE paragraph_translation_variants SET text = ?, updated_at = ? WHERE variant_id = ? AND paragraph_id = ?",
                        (str(variant.get("text") or ""), _now(), variant["variantId"], row["paragraph_id"]),
                    )
                manual = previous.get("manual")
                if isinstance(manual, dict) and isinstance(manual.get("variantId"), str):
                    exists = connection.execute("SELECT 1 FROM paragraph_translation_variants WHERE variant_id = ?", (manual["variantId"],)).fetchone()
                    timestamp = _now()
                    if exists:
                        connection.execute("UPDATE paragraph_translation_variants SET text = ?, updated_at = ? WHERE variant_id = ?",
                                           (str(manual.get("text") or ""), timestamp, manual["variantId"]))
                    else:
                        connection.execute(
                            "INSERT INTO paragraph_translation_variants(variant_id, paragraph_id, engine, text, model, created_at, updated_at) "
                            "VALUES (?, ?, 'manual', ?, NULL, ?, ?)", (manual["variantId"], row["paragraph_id"], str(manual.get("text") or ""), timestamp, timestamp),
                        )
                self._restore_selection(connection, row, previous["selection"])
                if manual is None:
                    # the paragraph had no manual variant: the one the replacement made goes away
                    connection.execute("DELETE FROM paragraph_translation_variants WHERE paragraph_id = ? AND engine = 'manual'", (row["paragraph_id"],))
                restored.append({"paragraphId": row["paragraph_id"], "chapterId": row["chapter_id"]})
            chapter_ids = list(dict.fromkeys(item["chapterId"] for item in restored))
            paragraphs = [self._paragraph_payload(connection, item["paragraphId"]) for item in restored if return_chapter_id and item["chapterId"] == return_chapter_id]
        return {"restored": len(restored), "chapterIds": chapter_ids, "paragraphs": paragraphs}

    def apply_replacement(self, project_id: str, items: Any, return_chapter_id: str | None = None) -> dict[str, Any] | None:
        """Redo of a replacement: exactly the texts given (not a new search), in one transaction. Returns the
        new undo state like replace_in_translation."""
        with self.connection() as connection:
            if connection.execute("SELECT 1 FROM book_projects WHERE project_id = ?", (project_id,)).fetchone() is None:
                return None
            rows = self._replacement_items(connection, project_id, items, ("text", "variants"))
            plan = []
            for row, item in zip(rows, items):
                if not isinstance(item["text"], str) or not isinstance(item["variants"], list):
                    raise ValueError("Некоректний список абзаців.")
                updates = []
                for variant in item["variants"]:
                    if not isinstance(variant, dict) or not isinstance(variant.get("variantId"), str) or not isinstance(variant.get("text"), str):
                        raise ValueError("Некоректний список абзаців.")
                    owned = connection.execute("SELECT 1 FROM paragraph_translation_variants WHERE variant_id = ? AND paragraph_id = ?", (variant["variantId"], row["paragraph_id"])).fetchone()
                    if owned is None:
                        raise ValueError("Варіант перекладу не знайдено.")
                    updates.append((variant["variantId"], variant["text"]))
                plan.append((row, item["text"], updates))
            undo = self._apply_replacements(connection, plan)
            return {"applied": len(undo), **self._replacement_result(connection, undo, return_chapter_id)}

    # --- translation queues ------------------------------------------------------------------------

    QUEUE_ACTIVE_STATUSES = ("running", "paused")

    @staticmethod
    def _queue_item(record: sqlite3.Row, with_plan: bool = False) -> dict[str, Any]:
        item = {
            "itemId": record["item_id"], "position": record["position"], "chapterId": record["chapter_id"],
            "chapterIndex": record["chapter_index"], "title": record["title"], "status": record["status"],
            "paragraphsTotal": record["paragraphs_total"], "paragraphsDone": record["paragraphs_done"],
            "batchesTotal": record["batches_total"], "batchesDone": record["batches_done"], "charsTotal": record["chars_total"],
            "error": record["error"], "startedAt": record["started_at"], "finishedAt": record["finished_at"],
        }
        if with_plan:
            item["plan"] = _json(record["plan"]) or []
        return item

    @staticmethod
    def _queue(record: sqlite3.Row) -> dict[str, Any]:
        return {
            "queueId": record["queue_id"], "projectId": record["project_id"], "engine": record["engine"],
            "connectionId": record["connection_id"], "model": record["model"], "reasoning": record["reasoning"],
            "options": _json(record["options"]) or {}, "status": record["status"], "budgetUsd": record["budget_usd"],
            "estimateUsd": record["estimate_usd"], "error": record["error"], "createdAt": record["created_at"],
            "startedAt": record["started_at"], "finishedAt": record["finished_at"], "undoneAt": record["undone_at"],
        }

    def create_translation_queue(
        self, project_id: str, engine: str, connection_id: str, model: str | None, reasoning: str | None,
        options: dict[str, Any], budget_usd: float | None, estimate_usd: float | None, items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """A new running queue. Only one queue per project may be running or paused."""
        queue_id = _new_id("queue")
        timestamp = _now()
        with self.connection() as connection:
            active = connection.execute(
                "SELECT 1 FROM translation_queues WHERE project_id = ? AND status IN ('running', 'paused')", (project_id,)
            ).fetchone()
            if active:
                raise ValueError("У проєкті вже є активна черга перекладу.")
            connection.execute(
                "INSERT INTO translation_queues(queue_id, project_id, engine, connection_id, model, reasoning, options, status, budget_usd, "
                "estimate_usd, created_at, started_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'running', ?, ?, ?, ?)",
                (queue_id, project_id, engine, connection_id, model, reasoning, json.dumps(options, ensure_ascii=False),
                 budget_usd, estimate_usd, timestamp, timestamp),
            )
            for position, item in enumerate(items, 1):
                connection.execute(
                    "INSERT INTO translation_queue_items(queue_id, position, chapter_id, chapter_index, title, plan, paragraphs_total, "
                    "batches_total, chars_total) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (queue_id, position, item["chapterId"], item["chapterIndex"], item["title"], json.dumps(item["plan"]),
                     len(item["plan"]), item["batchesTotal"], item["chars"]),
                )
        return self.get_translation_queue(queue_id) or {}

    def get_translation_queue(self, queue_id: str, with_plans: bool = False) -> dict[str, Any] | None:
        with self.connection() as connection:
            record = connection.execute("SELECT * FROM translation_queues WHERE queue_id = ?", (queue_id,)).fetchone()
            if record is None:
                return None
            items = connection.execute(
                "SELECT * FROM translation_queue_items WHERE queue_id = ? ORDER BY position", (queue_id,)
            ).fetchall()
        return {**self._queue(record), "items": [self._queue_item(item, with_plans) for item in items]}

    def paragraph_original_texts(self, paragraph_ids: list[str]) -> dict[str, str]:
        """id -> original text for the paragraphs that still exist (a queue plan may outlive a re-import)."""
        texts: dict[str, str] = {}
        with self.connection() as connection:
            for index in range(0, len(paragraph_ids), 500):
                chunk = paragraph_ids[index:index + 500]
                for record in connection.execute(
                    f"SELECT paragraph_id, original_text FROM book_paragraphs WHERE paragraph_id IN ({','.join('?' for _ in chunk)})", chunk
                ):
                    texts[record["paragraph_id"]] = record["original_text"] or ""
        return texts

    def chapter_variant_chars(self, chapter_id: str, engine: str) -> int:
        """Source characters of the chapter's paragraphs that have a variant of the engine (a stand-in
        for what an old usage row, without source_chars, translated)."""
        with self.connection() as connection:
            record = connection.execute(
                "SELECT COALESCE(SUM(LENGTH(p.original_text)), 0) AS chars FROM book_paragraphs p WHERE p.chapter_id = ? AND EXISTS "
                "(SELECT 1 FROM paragraph_translation_variants v WHERE v.paragraph_id = p.paragraph_id AND v.engine = ?)",
                (chapter_id, engine),
            ).fetchone()
        return int(record["chars"])

    def queue_variant_count(self, queue_id: str) -> int:
        with self.connection() as connection:
            return connection.execute("SELECT COUNT(*) FROM translation_queue_variants WHERE queue_id = ?", (queue_id,)).fetchone()[0]

    def latest_translation_queue(self, project_id: str) -> dict[str, Any] | None:
        """The active queue of a project, else the most recent one."""
        with self.connection() as connection:
            record = connection.execute(
                "SELECT queue_id FROM translation_queues WHERE project_id = ? ORDER BY "
                "CASE WHEN status IN ('running', 'paused') THEN 0 ELSE 1 END, created_at DESC, rowid DESC LIMIT 1",
                (project_id,),
            ).fetchone()
        return self.get_translation_queue(record["queue_id"]) if record else None

    def running_queue_ids(self) -> list[str]:
        with self.connection() as connection:
            return [record["queue_id"] for record in connection.execute(
                "SELECT queue_id FROM translation_queues WHERE status = 'running' ORDER BY created_at, rowid")]

    def set_queue_status(self, queue_id: str, status: str, error: str | None = None, finished: bool = False) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE translation_queues SET status = ?, error = COALESCE(?, error), finished_at = CASE WHEN ? THEN ? ELSE finished_at END "
                "WHERE queue_id = ?",
                (status, error, 1 if finished else 0, _now(), queue_id),
            )

    def transition_queue(self, queue_id: str, allowed_from: tuple[str, ...], status: str, finished: bool = False) -> bool:
        """Atomic status change (pause / resume / stop): only when the queue is in one of `allowed_from`."""
        with self.connection() as connection:
            cursor = connection.execute(
                f"UPDATE translation_queues SET status = ?, finished_at = CASE WHEN ? THEN ? ELSE finished_at END "
                f"WHERE queue_id = ? AND status IN ({','.join('?' for _ in allowed_from)})",
                (status, 1 if finished else 0, _now(), queue_id, *allowed_from),
            )
            return cursor.rowcount > 0

    def update_queue_item(self, item_id: int, **fields: Any) -> None:
        allowed = {"status": "status", "error": "error", "started_at": "started_at", "finished_at": "finished_at"}
        assignments, params = [], []
        for key, value in fields.items():
            assignments.append(f"{allowed[key]} = ?")
            params.append(value)
        if assignments:
            with self.connection() as connection:
                connection.execute(f"UPDATE translation_queue_items SET {', '.join(assignments)} WHERE item_id = ?", (*params, item_id))

    def skip_pending_queue_items(self, queue_id: str, running_to: str | None = None) -> None:
        """Pending items become skipped; with running_to the running item gets that status too."""
        with self.connection() as connection:
            connection.execute(
                "UPDATE translation_queue_items SET status = 'skipped', finished_at = ? WHERE queue_id = ? AND status = 'pending'",
                (_now(), queue_id),
            )
            if running_to:
                connection.execute(
                    "UPDATE translation_queue_items SET status = ?, finished_at = ? WHERE queue_id = ? AND status = 'running'",
                    (running_to, _now(), queue_id),
                )

    def save_queue_batch(self, queue_id: str, item_id: int, engine: str, entries: list[dict[str, Any]]) -> dict[str, int]:
        """One translated batch of a queue, atomically: the new variants, their link to the queue and the
        item's counters. A crash can therefore never leave variants without the counters (the batch is
        repeated after a restart) or counters without variants."""
        created = auto = 0
        with self.connection() as connection:
            for entry in entries:
                _exists, variant_id, auto_selected = self._add_variant_in(
                    connection, entry["paragraphId"], engine, entry["text"], entry.get("model"), entry.get("warnings"),
                    entry.get("promptHash"),
                )
                if variant_id:
                    created += 1
                    auto += 1 if auto_selected else 0
                    connection.execute(
                        "INSERT OR IGNORE INTO translation_queue_variants(queue_id, variant_id, paragraph_id, auto_selected) VALUES (?, ?, ?, ?)",
                        (queue_id, variant_id, entry["paragraphId"], 1 if auto_selected else 0),
                    )
            connection.execute(
                "UPDATE translation_queue_items SET batches_done = batches_done + 1, paragraphs_done = paragraphs_done + ?, "
                "status = CASE WHEN batches_done + 1 >= batches_total THEN 'done' ELSE status END, "
                "finished_at = CASE WHEN batches_done + 1 >= batches_total THEN ? ELSE finished_at END WHERE item_id = ?",
                (len(entries), _now(), item_id),
            )
        return {"created": created, "autoSelected": auto}

    def undo_queue_results(self, queue_id: str, dry_run: bool = False) -> dict[str, int] | None:
        """«Скасувати перекладене чергою»: delete the variants this queue created, except those the user
        chose by hand, and take back the automatic choice where the variant became the chosen text on its
        own and the paragraph has not been touched since (same text, not proofread). Anything the user
        did to a paragraph — edited it, chose another variant, proofread it — is left as it is."""
        with self.connection() as connection:
            if connection.execute("SELECT 1 FROM translation_queues WHERE queue_id = ?", (queue_id,)).fetchone() is None:
                return None
            summary = {"removedVariants": 0, "revertedSelections": 0, "keptChosen": 0, "alreadyGone": 0}
            links = connection.execute(
                "SELECT * FROM translation_queue_variants WHERE queue_id = ? ORDER BY rowid", (queue_id,)
            ).fetchall()
            for link in links:
                variant = connection.execute(
                    "SELECT * FROM paragraph_translation_variants WHERE variant_id = ?", (link["variant_id"],)
                ).fetchone()
                if variant is None:
                    summary["alreadyGone"] += 1
                    continue
                paragraph = connection.execute("SELECT * FROM book_paragraphs WHERE paragraph_id = ?", (link["paragraph_id"],)).fetchone()
                chosen_now = paragraph is not None and paragraph["selected_variant_id"] == variant["variant_id"]
                if chosen_now:
                    untouched = (
                        bool(link["auto_selected"]) and (paragraph["translation_text"] or "") == variant["text"]
                        and not paragraph["reviewed"] and not paragraph["proofread"]
                    )
                    if not untouched:
                        summary["keptChosen"] += 1  # chosen by hand, edited or proofread since: not ours to undo
                        continue
                    summary["revertedSelections"] += 1
                    if not dry_run:
                        connection.execute(
                            "UPDATE book_paragraphs SET translation_text = NULL, selected_variant_id = NULL, reviewed = 0 WHERE paragraph_id = ?",
                            (link["paragraph_id"],),
                        )
                summary["removedVariants"] += 1
                if not dry_run:
                    connection.execute("DELETE FROM paragraph_translation_variants WHERE variant_id = ?", (variant["variant_id"],))
            if not dry_run:
                connection.execute("DELETE FROM translation_queue_variants WHERE queue_id = ? AND variant_id NOT IN "
                                   "(SELECT variant_id FROM paragraph_translation_variants)", (queue_id,))
                connection.execute("UPDATE translation_queues SET undone_at = ? WHERE queue_id = ?", (_now(), queue_id))
        return summary

    def save_paragraph_edit(
        self,
        paragraph_id: str,
        translation_text: str | None,
        reviewed: bool,
        is_service: bool | None = None,
        queued_for_qa: bool | None = None,
        proofread: bool | None = None,
    ) -> dict[str, Any] | None:
        """The editor's save (PUT /api/paragraphs/{id}). A real change of the chosen text is
        a manual edit: it is kept in the single "manual" variant, which becomes the chosen
        one. Saving the same text again (reviewed/service toggles, chapter save) records nothing."""
        translation_text = normalize_translation_text(translation_text)
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM book_paragraphs WHERE paragraph_id = ?", (paragraph_id,)).fetchone()
            if row is None:
                return None
            # None clears the text, exactly like update_paragraph (the editor sends null for an emptied field).
            if (translation_text or "") != (row["translation_text"] or ""):
                self._manual_edit_in(connection, row, translation_text)
            self._write_paragraph(connection, paragraph_id, translation_text, reviewed, is_service, queued_for_qa, proofread=proofread)
            return self._paragraph_payload(connection, paragraph_id)

    def _manual_edit_in(self, connection: sqlite3.Connection, row: sqlite3.Row, translation_text: str | None) -> str:
        """A real change of the chosen text is a manual edit: it is kept in the single "manual" variant,
        which becomes the chosen one (the variant that was chosen before is pruned if it is now beyond
        the kept versions). Returns the id of the manual variant. The caller writes the paragraph."""
        paragraph_id = row["paragraph_id"]
        translation_text = normalize_translation_text(translation_text)
        timestamp = _now()
        manual = connection.execute(
            "SELECT variant_id FROM paragraph_translation_variants WHERE paragraph_id = ? AND engine = 'manual'",
            (paragraph_id,),
        ).fetchone()
        if manual:
            variant_id = manual["variant_id"]
            connection.execute(
                "UPDATE paragraph_translation_variants SET text = ?, updated_at = ? WHERE variant_id = ?",
                (translation_text or "", timestamp, variant_id),
            )
        else:
            variant_id = _new_id("variant")
            connection.execute(
                "INSERT INTO paragraph_translation_variants(variant_id, paragraph_id, engine, text, model, created_at, updated_at) "
                "VALUES (?, ?, 'manual', ?, NULL, ?, ?)",
                (variant_id, paragraph_id, translation_text or "", timestamp, timestamp),
            )
        previous_selected = row["selected_variant_id"]
        connection.execute("UPDATE book_paragraphs SET selected_variant_id = ? WHERE paragraph_id = ?", (variant_id, paragraph_id))
        if previous_selected and previous_selected != variant_id:
            previous = connection.execute(
                "SELECT engine FROM paragraph_translation_variants WHERE variant_id = ?", (previous_selected,)
            ).fetchone()
            if previous:
                self._prune_variants(connection, paragraph_id, previous["engine"])
        return variant_id

    def list_chapter_qa_findings(self, chapter_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM chapter_qa_findings WHERE chapter_id = ? ORDER BY created_at",
                (chapter_id,),
            ).fetchall()
        return [self._qa_finding_from_row(row) for row in rows]

    def add_chapter_qa_findings(self, chapter_id: str, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        timestamp = _now()
        with self.connection() as connection:
            for finding in findings:
                connection.execute(
                    "INSERT OR IGNORE INTO chapter_qa_findings"
                    "(finding_id, chapter_id, paragraph_id, category, quote, explanation, suggestion, source_model, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        _new_id("qa-finding"),
                        chapter_id,
                        finding["paragraphId"],
                        finding["category"],
                        finding["quote"],
                        finding.get("explanation"),
                        finding.get("suggestion"),
                        finding["sourceModel"],
                        timestamp,
                    ),
                )
        return self.list_chapter_qa_findings(chapter_id)

    def record_qa_run(self, chapter_id: str, provider: str) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO qa_runs(chapter_id, provider) VALUES (?, ?)",
                (chapter_id, provider),
            )

    def count_qa_runs_by_provider(self, chapter_id: str) -> dict[str, int]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT provider, COUNT(*) AS run_count FROM qa_runs "
                "WHERE chapter_id = ? GROUP BY provider",
                (chapter_id,),
            ).fetchall()
            configured_rows = connection.execute(
                "SELECT DISTINCT connection.provider_id "
                "FROM book_chapters chapter "
                "JOIN book_documents book ON book.book_id = chapter.book_id "
                "JOIN book_projects project ON project.project_id = book.project_id "
                "JOIN json_each(project.ai_configuration, '$.qaConnectionIds') configured "
                "JOIN integration_connections connection ON connection.connection_id = configured.value "
                "WHERE chapter.chapter_id = ? AND connection.provider_id IN ('claude', 'gemini', 'openai', 'grok')",
                (chapter_id,),
            ).fetchall()
        counts = {row["provider"]: row["run_count"] for row in rows}
        for row in configured_rows:
            counts.setdefault(row["provider_id"], 0)
        return counts

    def delete_chapter_qa_finding(self, finding_id: str) -> bool:
        with self.connection() as connection:
            cursor = connection.execute("DELETE FROM chapter_qa_findings WHERE finding_id = ?", (finding_id,))
        return cursor.rowcount > 0

    @staticmethod
    def _qa_finding_from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "findingId": row["finding_id"],
            "chapterId": row["chapter_id"],
            "paragraphId": row["paragraph_id"],
            "category": row["category"],
            "quote": row["quote"],
            "explanation": row["explanation"],
            "suggestion": row["suggestion"],
            "sourceModel": row["source_model"],
            "createdAt": row["created_at"],
        }

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

    def get_chapter_paragraphs(self, chapter_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT paragraph_id, paragraph_index, original_text, translation_text, reviewed, proofread, is_service, queued_for_qa, narrator_change "
                "FROM book_paragraphs WHERE chapter_id = ? ORDER BY paragraph_index",
                (chapter_id,),
            ).fetchall()
        return [
            {
                "paragraphId": row["paragraph_id"],
                "paragraphIndex": row["paragraph_index"],
                "originalText": row["original_text"],
                "translationText": row["translation_text"],
                "reviewed": _bool(row["reviewed"]),
                "proofread": _bool(row["proofread"]),
                "isService": _bool(row["is_service"]),
                "queuedForQa": _bool(row["queued_for_qa"]),
                "narratorChange": row["narrator_change"],
            }
            for row in rows
        ]

    def set_paragraph_narrator_change(self, paragraph_id: str, narrator_change: str | None) -> dict[str, Any] | None:
        """Mark (or clear) a paragraph as a narrator POV-switch point. When set,
        the given narrator gender/person is inherited by every following
        paragraph in the chapter until the next switch point, or the chapter's
        end if there isn't one."""
        narrator_change = _validated_narrator_gender(narrator_change)
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE book_paragraphs SET narrator_change = ? WHERE paragraph_id = ?",
                (narrator_change, paragraph_id),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute(
                "SELECT paragraph_id, narrator_change FROM book_paragraphs WHERE paragraph_id = ?",
                (paragraph_id,),
            ).fetchone()
        return {"paragraphId": row["paragraph_id"], "narratorChange": row["narrator_change"]}

    def set_paragraphs_qa_queue(self, paragraph_ids: list[str], queued: bool) -> None:
        """Bulk-set the 'queued for QA' flag. Used to auto-clear it on the
        paragraphs covered by a successful targeted QA re-run (mode 2 in the
        QA AI tab); whole-chapter QA runs never call this."""
        if not paragraph_ids:
            return
        with self.connection() as connection:
            connection.executemany(
                "UPDATE book_paragraphs SET queued_for_qa = ? WHERE paragraph_id = ?",
                [(int(queued), paragraph_id) for paragraph_id in paragraph_ids],
            )

    def get_project_character_genders(self, project_id: str) -> dict[str, str]:
        """Стем перекладеного імені персонажа -> 'femn'|'masc'|'plur', зібрані
        з власного і успадкованого глосарія проєкту. Стем для жіночого роду
        отримується відкиданням кінцевого 'а'/'я' (звичайне українське
        закінчення називного відмінка), щоб зловити відмінкові форми;
        чоловічий/на-«ви» рід лишається як є, бо приголосна основа зазвичай
        не змінюється в непрямих відмінках так само наперед передбачувано.
        """
        project = self.get_project(project_id)
        if project is None:
            return {}
        entry_ids = list(project["projectGlossaryEntryIds"]) + [
            item["glossaryEntryId"] for item in project["inheritedGlossary"]
        ]
        if not entry_ids:
            return {}
        placeholders = ",".join("?" for _ in entry_ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT target, character_gender FROM glossary_entries "
                f"WHERE glossary_entry_id IN ({placeholders}) AND character_gender IS NOT NULL AND active = 1",
                entry_ids,
            ).fetchall()
        genders: dict[str, str] = {}
        for row in rows:
            target = row["target"]
            gender = row["character_gender"]
            if not target:
                continue
            stem = target
            if gender == "femn" and target[-1] in "ая":
                stem = target[:-1]
            genders[stem] = gender
        return genders

    def get_project_character_registers(self, project_id: str) -> dict[str, str]:
        """Перекладене ім'я персонажа -> нотатка про мовний регістр (напр.
        "постійна лайка", "формальна мова, лайка виключена"), зібрана з
        власного і успадкованого глосарія проєкту. Використовується AI QA
        для стильової перевірки (пункт 1a: чи виправдане згладжування
        грубості для цього персонажа)."""
        project = self.get_project(project_id)
        if project is None:
            return {}
        entry_ids = list(project["projectGlossaryEntryIds"]) + [
            item["glossaryEntryId"] for item in project["inheritedGlossary"]
        ]
        if not entry_ids:
            return {}
        placeholders = ",".join("?" for _ in entry_ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT target, speech_register FROM glossary_entries "
                f"WHERE glossary_entry_id IN ({placeholders}) AND speech_register IS NOT NULL AND active = 1",
                entry_ids,
            ).fetchall()
        return {row["target"]: row["speech_register"] for row in rows if row["target"]}

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

    def set_chapter_export_flag(self, chapter_id: str, exclude: bool) -> bool:
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE book_chapters SET exclude_from_export = ? WHERE chapter_id = ?",
                (int(exclude), chapter_id),
            )
        return cursor.rowcount > 0

    def add_chat_message(self, project_id: str, role: str, content: str, provider_id: str | None = None) -> dict[str, Any]:
        message_id = _new_id("chat-message")
        timestamp = _now()
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO project_chat_messages(message_id, project_id, role, content, provider_id, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (message_id, project_id, role, content, provider_id, timestamp),
            )
        return {
            "messageId": message_id,
            "projectId": project_id,
            "role": role,
            "content": content,
            "providerId": provider_id,
            "createdAt": timestamp,
        }

    def get_chat_messages(self, project_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM project_chat_messages WHERE project_id = ? ORDER BY created_at",
                (project_id,),
            ).fetchall()
        return [
            {
                "messageId": row["message_id"],
                "projectId": row["project_id"],
                "role": row["role"],
                "content": row["content"],
                "providerId": row["provider_id"],
                "createdAt": row["created_at"],
            }
            for row in rows
        ]

    def clear_chat_messages(self, project_id: str) -> None:
        with self.connection() as connection:
            connection.execute("DELETE FROM project_chat_messages WHERE project_id = ?", (project_id,))

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
    def _project_summary_from_row(row: sqlite3.Row, progress: dict[str, Any]) -> dict[str, Any]:
        return {
            "projectId": row["project_id"],
            "title": row["title"],
            "authorId": row["author_id"],
            "seriesId": row["series_id"],
            "status": row["status"],
            # "progress" (the overall percent, paragraphs) is what older clients read; "paragraphs"/"words" carry the
            # four figures of each unit (translated, reviewed, proofread, overall).
            "progress": {"progress": round(progress["paragraphs"]["percent"]["overall"]), **progress},
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
            "narratorGender": _validated_narrator_gender(data.get("narratorGender", source.get("narratorGender"))),
            "analysisResult": analysis_result,
            "translationRules": str(data.get("translationRules", source.get("translationRules", ""))),
            "aiConfiguration": ai_configuration,
            "chapterCount": data.get("chapterCount", source.get("chapterCount", 0)),
            "createdAt": created_at,
            "updatedAt": updated_at,
            "projectRuleIds": _deduped_ids(data.get("projectRuleIds", source.get("projectRuleIds", []))),
            "projectGlossaryEntryIds": _deduped_ids(data.get("projectGlossaryEntryIds", source.get("projectGlossaryEntryIds", []))),
            "inheritedRules": _deduped_by_key(data.get("inheritedRules", source.get("inheritedRules", [])), "ruleId"),
            "inheritedGlossary": _deduped_by_key(data.get("inheritedGlossary", source.get("inheritedGlossary", [])), "glossaryEntryId"),
        }

    @staticmethod
    def _write_project(connection: sqlite3.Connection, project: dict[str, Any], replace: bool, raw_data: dict[str, Any] | None = None) -> None:
        if not project["title"]:
            raise ValueError("Project title is required.")
        analysis_result_json = json.dumps(project["analysisResult"], ensure_ascii=False) if project["analysisResult"] is not None else None
        ai_configuration_json = json.dumps(project["aiConfiguration"], ensure_ascii=False)
        if replace:
            # An UPDATE, not "INSERT OR REPLACE": the latter deletes the existing
            # book_projects row before reinserting it, and every child table with
            # ON DELETE CASCADE on project_id (project_rules, project_glossary,
            # project_translation_glossaries, project_brief_entries,
            # project_chat_messages, ...) has that DELETE's cascade fire immediately
            # — permanently wiping those rows even though the parent row reappears
            # a moment later in the same statement, silently, on every single
            # project update regardless of what the caller actually changed.
            connection.execute(
                "UPDATE book_projects SET title = ?, author_id = ?, series_id = ?, status = ?, file_name = ?, file_format = ?, file_size = ?, book_number = ?, analysis_result = ?, translation_rules = ?, ai_configuration = ?, narrator_gender = ?, chapter_count = ?, updated_at = ? WHERE project_id = ?",
                (project["title"], project["authorId"], project["seriesId"], project["status"], project["fileName"], project["fileFormat"], project["fileSize"], project["bookNumber"], analysis_result_json, project["translationRules"], ai_configuration_json, project["narratorGender"], project["chapterCount"], project["updatedAt"], project["projectId"]),
            )
        else:
            connection.execute(
                "INSERT INTO book_projects(project_id, title, author_id, series_id, status, file_name, file_format, file_size, book_number, analysis_result, translation_rules, ai_configuration, narrator_gender, chapter_count, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (project["projectId"], project["title"], project["authorId"], project["seriesId"], project["status"], project["fileName"], project["fileFormat"], project["fileSize"], project["bookNumber"], analysis_result_json, project["translationRules"], ai_configuration_json, project["narratorGender"], project["chapterCount"], project["createdAt"], project["updatedAt"]),
            )

        # `raw_data` is the caller's actual request body (None on internal callers that
        # always mean to rewrite everything). When a caller sends a partial update — for
        # example the "project info" form that only edits title/series/bookNumber — it
        # must not be able to silently wipe project_rules/project_glossary just because
        # its local model defaults those fields to an empty list. We only touch each
        # table when the request explicitly mentions the relevant key(s); otherwise we
        # leave the existing rows untouched, no matter what _project_input merged in.
        touches_rules = raw_data is None or "projectRuleIds" in raw_data or "inheritedRules" in raw_data
        touches_glossary = raw_data is None or "projectGlossaryEntryIds" in raw_data or "inheritedGlossary" in raw_data

        if touches_rules:
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

        if touches_glossary:
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
            "narratorGender": row["narrator_gender"],
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
