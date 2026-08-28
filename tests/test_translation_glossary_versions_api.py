import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from cryptography.fernet import Fernet

from backend.integrations.credentials import CredentialVault
from backend.integrations.registry import ProviderRegistry
from backend.storage import Storage
from backend.translations.service import TranslationService


class TranslationGlossaryVersionsApiTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")
        self.service = TranslationService(
            self.storage,
            CredentialVault(Fernet(Fernet.generate_key())),
            ProviderRegistry([]),
        )
        self.project = self.storage.create_project({"title": "Version API", "status": "translation"})

        self.initial_entries = [
            {"source": "alpha", "target": "альфа", "context": "ctx-a"},
            {"source": "beta", "target": "бета", "context": "ctx-b"},
        ]
        self.initial_hash = self._legacy_hash("EN", "UK", self.initial_entries)
        glossary = self.storage.upsert_project_translation_glossary(
            self.project["projectId"],
            {
                "sourceLanguage": "EN",
                "targetLanguage": "UK",
                "entries": self.initial_entries,
                "contentHash": self.initial_hash,
            },
        )
        self.glossary_rule_id = glossary["glossaryRuleId"]

        # Build Version #1 from legacy entries.
        self.storage.initialize()

    def tearDown(self):
        self.temporary_directory.cleanup()

    @staticmethod
    def _legacy_hash(source_language: str, target_language: str, entries: list[dict[str, str]]) -> str:
        payload = {
            "sourceLanguage": source_language,
            "targetLanguage": target_language,
            "entries": [{"source": item["source"], "target": item["target"]} for item in entries],
        }
        return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()

    def _version_count(self) -> int:
        with self.storage.connection() as connection:
            return connection.execute(
                "SELECT COUNT(*) FROM project_translation_glossary_versions WHERE glossary_rule_id = ?",
                (self.glossary_rule_id,),
            ).fetchone()[0]

    def test_gets_current_version_with_ordered_item_ids(self):
        current = self.service.get_project_glossary_current_version(self.project["projectId"], self.glossary_rule_id)

        self.assertEqual(1, current["versionNumber"])
        self.assertEqual(2, len(current["glossaryEntryIds"]))

        materialized = self.service.materialize_project_glossary_version(self.project["projectId"], self.glossary_rule_id)
        self.assertEqual(["alpha", "beta"], [item["source"] for item in materialized["entries"]])

    def test_materialize_returns_legacy_compatible_hash(self):
        materialized = self.service.materialize_project_glossary_version(self.project["projectId"], self.glossary_rule_id)

        self.assertEqual(materialized["contentHash"], materialized["materializedContentHash"])
        self.assertEqual(self.initial_hash, materialized["contentHash"])

    def test_commit_creates_new_version_on_item_set_change_and_preserves_order(self):
        current = self.service.get_project_glossary_current_version(self.project["projectId"], self.glossary_rule_id)
        reversed_ids = list(reversed(current["glossaryEntryIds"]))

        committed = self.service.commit_project_glossary_version(
            self.project["projectId"],
            self.glossary_rule_id,
            reversed_ids,
        )

        self.assertTrue(committed["createdNewVersion"])
        self.assertEqual(2, committed["versionNumber"])
        self.assertEqual(reversed_ids, committed["glossaryEntryIds"])

        materialized = self.service.materialize_project_glossary_version(self.project["projectId"], self.glossary_rule_id)
        self.assertEqual(["beta", "alpha"], [item["source"] for item in materialized["entries"]])

    def test_repeated_commit_without_changes_does_not_create_new_version(self):
        current = self.service.get_project_glossary_current_version(self.project["projectId"], self.glossary_rule_id)
        before_versions = self._version_count()

        committed = self.service.commit_project_glossary_version(
            self.project["projectId"],
            self.glossary_rule_id,
            current["glossaryEntryIds"],
        )

        self.assertFalse(committed["createdNewVersion"])
        self.assertEqual(before_versions, self._version_count())
        self.assertEqual(1, committed["versionNumber"])

    def test_add_and_remove_item_create_versions_only_on_commit(self):
        extra = self.storage.create_glossary_entry(
            {
                "source": "gamma",
                "target": "гамма",
                "note": "ctx-c",
                "active": True,
            }
        )

        current = self.service.get_project_glossary_current_version(self.project["projectId"], self.glossary_rule_id)
        before_versions = self._version_count()

        # Draft-only manipulation (no commit) does not touch DB versions.
        draft_ids = current["glossaryEntryIds"] + [extra["glossaryEntryId"]]
        self.assertEqual(before_versions, self._version_count())

        added = self.service.commit_project_glossary_version(
            self.project["projectId"],
            self.glossary_rule_id,
            draft_ids,
        )
        self.assertTrue(added["createdNewVersion"])
        self.assertEqual(before_versions + 1, self._version_count())

        removed = self.service.commit_project_glossary_version(
            self.project["projectId"],
            self.glossary_rule_id,
            [draft_ids[0], draft_ids[2]],
        )
        self.assertTrue(removed["createdNewVersion"])
        self.assertEqual(before_versions + 2, self._version_count())

    def test_new_glossary_is_created_only_on_commit(self):
        with self.storage.connection() as connection:
            before = connection.execute(
                "SELECT COUNT(*) FROM project_translation_glossaries WHERE project_id = ? AND source_language = 'DE' AND target_language = 'UK'",
                (self.project["projectId"],),
            ).fetchone()[0]
        self.assertEqual(0, before)

        item = self.storage.create_glossary_entry(
            {
                "source": "Haus",
                "target": "будинок",
                "note": "noun",
                "active": True,
            }
        )
        committed = self.service.commit_project_glossary_draft(
            self.project["projectId"],
            {
                "sourceLanguage": "DE",
                "targetLanguage": "UK",
                "glossaryEntryIds": [item["glossaryEntryId"]],
            },
        )

        self.assertEqual("DE", committed["sourceLanguage"])
        self.assertEqual("UK", committed["targetLanguage"])
        self.assertIsNotNone(committed["currentVersionId"])
        materialized = self.service.materialize_project_glossary_version(
            self.project["projectId"],
            committed["glossaryRuleId"],
        )
        self.assertEqual(["Haus"], [entry["source"] for entry in materialized["entries"]])


if __name__ == "__main__":
    unittest.main()
