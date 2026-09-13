"""
Patch 41: keep DeepL provider sync metadata scoped to its owning glossary.

Run from the repo root (same folder as backend/):
    python apply_patch41.py
"""
from pathlib import Path


STORAGE_PATH = Path("backend/storage.py")
TEST_PATH = Path("tests/test_projects_api.py")


def apply(path: Path, old: str, new: str, count: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    occurrences = text.count(old)
    if occurrences != count:
        raise SystemExit(
            f"Expected {count} occurrence(s) of snippet in {path}, found {occurrences}.\n"
            f"--- snippet ---\n{old}\n---------------"
        )
    path.write_text(text.replace(old, new, count), encoding="utf-8")


def main() -> None:
    apply(
        STORAGE_PATH,
        '''                "WHERE EXISTS (SELECT 1 FROM project_translation_glossaries local "
                "WHERE local.project_id = ? AND local.source_language = sync.source_language AND local.target_language = sync.target_language)",
                (project_id,),
            ).fetchall()
        sync_by_pair = {(row["source_language"], row["target_language"]): row for row in sync_rows}
        return [self._translation_glossary(row, sync_by_pair.get((row["source_language"], row["target_language"]))) for row in rows]''',
        '''                "WHERE owner.project_id = ?",
                (project_id,),
            ).fetchall()
        sync_by_glossary_rule_id = {row["glossary_rule_id"]: row for row in sync_rows}
        return [self._translation_glossary(row, sync_by_glossary_rule_id.get(row["glossary_rule_id"])) for row in rows]''',
    )
    apply(
        STORAGE_PATH,
        '''                "WHERE sync.source_language = ? AND sync.target_language = ? ORDER BY sync.synced_at DESC LIMIT 1",
                (row["source_language"], row["target_language"]),''',
        '''                "WHERE sync.glossary_rule_id = ?",
                (row["glossary_rule_id"],),''',
        count=2,
    )
    apply(
        TEST_PATH,
        '''    def test_structured_translation_glossary_and_provider_sync_persist(self):
        glossary = self.storage.upsert_project_translation_glossary(self.project["projectId"], {
            "sourceLanguage": "EN",
            "targetLanguage": "UK",
            "entries": [
                {"source": "dominant", "target": "домінант", "context": "Character role"},
            ],
            "contentHash": "content-hash",
        })
        self.storage.save_provider_glossary_sync(
            glossary["glossaryRuleId"], "connection-1", "deepl", "remote-1", "content-hash"
        )

        restored = self.storage.list_project_translation_glossaries(self.project["projectId"])[0]

        self.assertEqual("glossary", restored["type"])
        self.assertEqual("Character role", restored["entries"][0]["context"])
        self.assertEqual("remote-1", restored["providerSync"]["remoteGlossaryId"])''',
        '''    def test_provider_sync_is_returned_only_to_its_own_translation_glossary(self):
        glossary = self.storage.upsert_project_translation_glossary(self.project["projectId"], {
            "sourceLanguage": "EN",
            "targetLanguage": "UK",
            "entries": [
                {"source": "dominant", "target": "домінант", "context": "Character role"},
            ],
            "contentHash": "content-hash",
        })
        self.storage.save_provider_glossary_sync(
            glossary["glossaryRuleId"], "connection-1", "deepl", "remote-1", "content-hash"
        )
        second_project = self.storage.create_project({"title": "Other project", "status": "analysis"})
        second_glossary = self.storage.upsert_project_translation_glossary(second_project["projectId"], {
            "sourceLanguage": "EN",
            "targetLanguage": "UK",
            "entries": [
                {"source": "submissive", "target": "сабмісив", "context": "Character role"},
            ],
            "contentHash": "second-content-hash",
        })

        restored = self.storage.list_project_translation_glossaries(self.project["projectId"])[0]
        other_restored = self.storage.list_project_translation_glossaries(second_project["projectId"])[0]
        other_fetched = self.storage.get_project_translation_glossary(second_glossary["glossaryRuleId"])

        self.assertEqual("glossary", restored["type"])
        self.assertEqual("Character role", restored["entries"][0]["context"])
        self.assertEqual("remote-1", restored["providerSync"]["remoteGlossaryId"])
        self.assertIsNone(other_restored["providerSync"])
        self.assertEqual("unsynced", other_restored["syncState"])
        self.assertIsNotNone(other_fetched)
        self.assertIsNone(other_fetched["providerSync"])''',
    )
    print("Patch 41 applied successfully.")


if __name__ == "__main__":
    main()
