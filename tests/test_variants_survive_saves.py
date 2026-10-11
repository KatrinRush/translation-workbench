"""Translation variants must outlive every "save" the UI performs.

Reproduces the report "variant tabs (Claude / GPT / Gemini) vanished from a chapter after a
deploy": create variants, save the project (PUT /api/projects/{id}) and the chapter
(PUT /api/paragraphs/{id} for each paragraph), restart (Storage.initialize runs the
migrations again), reload the book structure, and compare the variants with what was there.
"""
import subprocess
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend import server
from backend.storage import Storage


class FakeHandler:
    def __init__(self, payload=None):
        self.payload = payload

    def read_json(self):
        return self.payload


def variant_fingerprint(storage, project_id):
    """{paragraphId: (selectedVariantId, [(variantId, engine, text), ...])} -- test data only."""
    result = {}
    for chapter in storage.get_book_structure(project_id)["chapters"]:
        for element in chapter["elements"]:
            if element["type"] == "paragraph":
                result[element["paragraphId"]] = (
                    element["selectedVariantId"],
                    [(v["variantId"], v["engine"], v["text"]) for v in element["translationVariants"]],
                )
    return result


class VariantsFixture(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "workbench.sqlite3"
        self.storage = Storage(self.database_path)
        self.project_id = self.storage.create_project({"title": "Fool me twice", "status": "translation"})["projectId"]
        self.storage.save_book_structure(
            self.project_id, "book.epub", "application/epub+zip", b"book",
            {"chapters": [
                {"title": f"CHAPTER {number}", "elements": [
                    {"type": "paragraph", "text": f"Original {number}.{index}"} for index in range(3)
                ]} for number in (37, 38)
            ]},
        )
        paragraph_ids = [
            element["paragraphId"]
            for chapter in self.storage.get_book_structure(self.project_id)["chapters"]
            for element in chapter["elements"]
        ]
        for paragraph_id in paragraph_ids:
            self.storage.update_paragraph(paragraph_id, f"Поточний {paragraph_id}", False)
        # An existing translation becomes the "current" variant when the service starts.
        self.storage = Storage(self.database_path)
        for paragraph_id in paragraph_ids:
            self.storage.add_translation_variant(paragraph_id, "claude", f"Claude {paragraph_id}")
            self.storage.add_translation_variant(paragraph_id, "openai", f"GPT {paragraph_id}")
            self.storage.add_translation_variant(paragraph_id, "gemini", f"Gemini {paragraph_id}")
        self.before = variant_fingerprint(self.storage, self.project_id)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def api(self, method, path, payload=None):
        with patch.object(server, "storage", self.storage):
            return server.WorkbenchHandler.handle_api(FakeHandler(payload), method, path)

    def assert_variants_intact(self):
        after = variant_fingerprint(self.storage, self.project_id)
        self.assertEqual(self.before, after)
        for selected, variants in after.values():
            self.assertEqual({"current", "claude", "openai", "gemini"}, {engine for _id, engine, _text in variants})
            self.assertIsNotNone(selected)


class VariantsSurviveSavesTests(VariantsFixture):
    def test_fixture_has_four_variants_per_paragraph(self):
        self.assertEqual(6, len(self.before))
        self.assert_variants_intact()

    def test_saving_the_project_keeps_variants(self):
        project = self.api("GET", f"/api/projects/{self.project_id}")[1]
        status, _body = self.api("PUT", f"/api/projects/{self.project_id}", project)
        self.assertEqual(200, status)
        status, _body = self.api("PUT", f"/api/projects/{self.project_id}", {"title": "Renamed", "bookNumber": 2})
        self.assertEqual(200, status)
        self.assert_variants_intact()

    def test_saving_a_chapter_unchanged_keeps_variants(self):
        # The 💾 button PUTs every dirty paragraph; here with the text the paragraph already has.
        for paragraph_id, _ in self.before.items():
            current = self.storage.get_paragraph(paragraph_id)
            status, _body = self.api("PUT", f"/api/paragraphs/{paragraph_id}", {
                "translationText": current["translationText"], "reviewed": True, "isService": False,
            })
            self.assertEqual(200, status)
        reviewed = self.storage.get_book_structure(self.project_id)["chapters"][1]["elements"][0]
        self.assertTrue(reviewed["reviewed"])
        self.assert_variants_intact()

    def test_editing_a_chapter_only_adds_a_manual_variant(self):
        paragraph_id = next(iter(self.before))
        self.api("PUT", f"/api/paragraphs/{paragraph_id}", {"translationText": "Моя правка", "reviewed": False})
        _selected, variants = variant_fingerprint(self.storage, self.project_id)[paragraph_id]
        self.assertEqual({"current", "claude", "openai", "gemini", "manual"}, {engine for _id, engine, _t in variants})
        for other_id, expected in self.before.items():
            if other_id != paragraph_id:
                self.assertEqual(expected, variant_fingerprint(self.storage, self.project_id)[other_id])

    def test_chapter_title_and_export_flag_saves_keep_variants(self):
        chapter_id = self.storage.get_book_structure(self.project_id)["chapters"][1]["chapterId"]
        self.assertEqual(200, self.api("PUT", f"/api/chapters/{chapter_id}/title", {"translationTitle": "Розділ", "reviewed": True})[0])
        self.assert_variants_intact()

    def test_restart_after_saves_keeps_variants_and_is_idempotent(self):
        self.api("PUT", f"/api/projects/{self.project_id}", self.api("GET", f"/api/projects/{self.project_id}")[1])
        for _ in range(3):  # every deploy restarts the service: initialize() runs all migrations again
            self.storage = Storage(self.database_path)
            self.assert_variants_intact()

    def test_reloading_the_same_epub_is_the_only_save_that_resets_the_book(self):
        # Documented behaviour: replacing the EPUB creates a new book (the UI asks first).
        self.storage.save_book_structure(self.project_id, "book.epub", "application/epub+zip", b"book", {"chapters": []})
        self.assertEqual({}, variant_fingerprint(self.storage, self.project_id))
        with sqlite3.connect(self.database_path) as connection:
            self.assertEqual(0, connection.execute("SELECT COUNT(*) FROM paragraph_translation_variants").fetchone()[0])


class MigrationIdempotencyTests(VariantsFixture):
    """initialize() runs on every service start (every deploy)."""

    def counts(self):
        with sqlite3.connect(self.database_path) as connection:
            return {
                table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ("book_paragraphs", "paragraph_translation_variants", "paragraph_footnotes", "book_chapters")
            }

    def test_repeated_initialize_changes_nothing(self):
        before = self.counts()
        for _ in range(3):
            Storage(self.database_path)
        self.assertEqual(before, self.counts())
        self.assert_variants_intact()

    def test_current_variant_is_created_once_and_only_for_paragraphs_without_variants(self):
        # A translated paragraph that never got variants gets exactly one "current" ...
        project_id = self.storage.create_project({"title": "Other", "status": "translation"})["projectId"]
        self.storage.save_book_structure(project_id, "o.epub", "application/epub+zip", b"o",
                                         {"chapters": [{"title": "A", "elements": [{"type": "paragraph", "text": "x"}]}]})
        paragraph_id = self.storage.get_book_structure(project_id)["chapters"][0]["elements"][0]["paragraphId"]
        self.storage.update_paragraph(paragraph_id, "Переклад", False)
        for _ in range(3):
            self.storage = Storage(self.database_path)
        variants = self.storage.get_paragraph(paragraph_id)["translationVariants"]
        self.assertEqual(["current"], [variant["engine"] for variant in variants])
        # ... and the paragraphs that already had variants were left alone.
        self.assert_variants_intact()

    def test_migration_never_recreates_or_removes_variants_the_user_dropped(self):
        paragraph_id = next(iter(self.before))
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("DELETE FROM paragraph_translation_variants WHERE paragraph_id = ? AND engine = 'gemini'", (paragraph_id,))
        Storage(self.database_path)
        engines = [variant["engine"] for variant in Storage(self.database_path).get_paragraph(paragraph_id)["translationVariants"]]
        self.assertEqual(["current", "claude", "openai"], engines)

    def test_upgrade_from_a_database_without_warnings_and_selected_columns_keeps_variants(self):
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("ALTER TABLE paragraph_translation_variants DROP COLUMN warnings")
            connection.execute("ALTER TABLE book_paragraphs DROP COLUMN selected_variant_id")
        before_variants = self.counts()["paragraph_translation_variants"]
        for _ in range(2):
            self.storage = Storage(self.database_path)
        self.assertEqual(before_variants, self.counts()["paragraph_translation_variants"])
        for paragraph in self.storage.get_book_structure(self.project_id)["chapters"][0]["elements"]:
            self.assertEqual({"claude", "openai", "gemini"} | {"current"}, {v["engine"] for v in paragraph["translationVariants"]} | {"current"})

    def test_legacy_not_null_chapter_titles_migration_keeps_paragraphs_and_variants(self):
        # Old schema: book_chapters.title NOT NULL. The migration rebuilds book_chapters; with
        # foreign keys on, DROP TABLE would cascade through paragraphs into the variants.
        before = self.counts()
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("PRAGMA foreign_keys = OFF")
            connection.execute("ALTER TABLE book_chapters RENAME TO book_chapters_old")
            connection.execute(
                "CREATE TABLE book_chapters (chapter_id TEXT PRIMARY KEY, book_id TEXT NOT NULL REFERENCES book_documents(book_id) ON DELETE CASCADE, "
                "chapter_index INTEGER NOT NULL, title TEXT NOT NULL, translation_title TEXT, title_reviewed INTEGER NOT NULL DEFAULT 0, "
                "exclude_from_export INTEGER NOT NULL DEFAULT 0, word_count INTEGER NOT NULL DEFAULT 0, paragraph_count INTEGER NOT NULL DEFAULT 0, "
                "ai_analysis_results TEXT NOT NULL DEFAULT '{}', UNIQUE(book_id, chapter_index))"
            )
            connection.execute("INSERT INTO book_chapters SELECT * FROM book_chapters_old")
            connection.execute("DROP TABLE book_chapters_old")
        for _ in range(2):
            self.storage = Storage(self.database_path)
        self.assertEqual(before, self.counts())
        self.assert_variants_intact()


class VariantsReportScriptTests(VariantsFixture):
    SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "diagnose_variants_db.sh"

    def run_script(self):
        return subprocess.run(["bash", str(self.SCRIPT), str(self.database_path)], capture_output=True, text=True, check=True).stdout

    def test_reports_counts_per_chapter_and_engine_without_any_text(self):
        report = self.run_script()
        self.assertIn("CHAPTER 38", report)
        row = next(line for line in report.splitlines() if "CHAPTER 38" in line)
        # paras, transl, sel, dangl | current, deepl, claude, openai, gemini, manual | other
        self.assertEqual(["3", "3", "3", "0", "3", "0", "3", "3", "3", "0", "0"], row.split()[-11:])
        self.assertIn("claude=6", report)
        for secret in ("Original 38", "Поточний", "Claude paragraph", "GPT paragraph", "Gemini paragraph"):
            self.assertNotIn(secret, report)

    def test_is_read_only(self):
        def snapshot():
            with sqlite3.connect(self.database_path) as connection:
                return [connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
                        for table in ("book_paragraphs", "paragraph_translation_variants", "book_chapters", "book_projects")]
        before = snapshot()
        self.run_script()
        self.assertEqual(before, snapshot())
        # and it could not write even if it tried: the connection is opened mode=ro
        script = self.SCRIPT.read_text(encoding="utf-8")
        self.assertIn("mode=ro", script)
        self.assertIn("query_only", script)


if __name__ == "__main__":
    unittest.main()
