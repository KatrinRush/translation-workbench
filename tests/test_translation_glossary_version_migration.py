import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from backend.storage import Storage


class TranslationGlossaryVersionMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")

    def tearDown(self):
        self.temporary_directory.cleanup()

    @staticmethod
    def _hash(source_language: str, target_language: str, entries: list[dict[str, str]]) -> str:
        payload = {
            "sourceLanguage": source_language,
            "targetLanguage": target_language,
            "entries": [{"source": item["source"], "target": item["target"]} for item in entries],
        }
        return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()

    def test_migration_creates_version_and_reuses_existing_global_item(self):
        project = self.storage.create_project({"title": "Version Migration", "status": "translation"})

        reused = self.storage.create_glossary_entry(
            {
                "source": "dominant",
                "target": "домінант",
                "note": "role",
                "active": True,
            }
        )

        entries = [
            {"source": "dominant", "target": "домінант", "context": "role"},
            {"source": "river", "target": "ріка", "context": "nature"},
        ]
        content_hash = self._hash("EN", "UK", entries)
        glossary = self.storage.upsert_project_translation_glossary(
            project["projectId"],
            {
                "sourceLanguage": "EN",
                "targetLanguage": "UK",
                "entries": entries,
                "contentHash": content_hash,
            },
        )
        self.storage.save_provider_glossary_sync(
            glossary["glossaryRuleId"],
            "connection-1",
            "deepl",
            "remote-1",
            content_hash,
        )

        # Re-run initialization to invoke idempotent migration against existing data.
        self.storage.initialize()

        with self.storage.connection() as connection:
            migrated = connection.execute(
                "SELECT current_version_id FROM project_translation_glossaries WHERE glossary_rule_id = ?",
                (glossary["glossaryRuleId"],),
            ).fetchone()
            self.assertIsNotNone(migrated["current_version_id"])

            version = connection.execute(
                "SELECT version_number, content_hash FROM project_translation_glossary_versions WHERE version_id = ?",
                (migrated["current_version_id"],),
            ).fetchone()
            self.assertEqual(1, version["version_number"])
            self.assertEqual(content_hash, version["content_hash"])

            links = connection.execute(
                "SELECT glossary_entry_id, position FROM project_translation_glossary_version_items WHERE version_id = ? ORDER BY position",
                (migrated["current_version_id"],),
            ).fetchall()
            self.assertEqual(2, len(links))
            self.assertEqual(0, links[0]["position"])
            self.assertEqual(1, links[1]["position"])
            self.assertEqual(reused["glossaryEntryId"], links[0]["glossary_entry_id"])

            sync = connection.execute(
                "SELECT remote_glossary_id, content_hash FROM provider_glossary_sync WHERE glossary_rule_id = ?",
                (glossary["glossaryRuleId"],),
            ).fetchone()
            self.assertEqual("remote-1", sync["remote_glossary_id"])
            self.assertEqual(content_hash, sync["content_hash"])

    def test_migration_is_idempotent(self):
        project = self.storage.create_project({"title": "Idempotent", "status": "translation"})
        entries = [{"source": "sky", "target": "небо", "context": ""}]
        content_hash = self._hash("EN", "UK", entries)
        glossary = self.storage.upsert_project_translation_glossary(
            project["projectId"],
            {
                "sourceLanguage": "EN",
                "targetLanguage": "UK",
                "entries": entries,
                "contentHash": content_hash,
            },
        )

        self.storage.initialize()
        self.storage.initialize()

        with self.storage.connection() as connection:
            versions = connection.execute(
                "SELECT COUNT(*) AS total FROM project_translation_glossary_versions WHERE glossary_rule_id = ?",
                (glossary["glossaryRuleId"],),
            ).fetchone()
            self.assertEqual(1, versions["total"])

            links = connection.execute(
                "SELECT COUNT(*) AS total FROM project_translation_glossary_version_items",
            ).fetchone()
            self.assertEqual(1, links["total"])


if __name__ == "__main__":
    unittest.main()
