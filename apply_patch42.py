"""
Patch 42: Fix provider_glossary_sync lookup in list_project_translation_glossaries,
get_project_translation_glossary, and get_or_create_project_translation_glossary.

Patch 41 restricted sync lookup exclusively to matching glossary_rule_id, which broke
the provider slot tracking model when a second project legitimately replaces an active
DeepL slot for the same language pair (causing providerSync to be returned as None for
the replaced glossary rather than indicating the active slot occupant and syncState='unsynced').

This patch restores provider_glossary_sync querying by language pair (source_language, target_language)
so that providerSync correctly reflects slot status, while _translation_glossary continues to
accurately compute owns_slot / isCurrent / syncState ('synced' vs 'unsynced'/'stale').

Run from the repo root (same folder as backend/):
    python apply_patch42.py
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
        '''                "WHERE owner.project_id = ?",
                (project_id,),
            ).fetchall()
        sync_by_glossary_rule_id = {row["glossary_rule_id"]: row for row in sync_rows}
        return [self._translation_glossary(row, sync_by_glossary_rule_id.get(row["glossary_rule_id"])) for row in rows]''',
        '''                "WHERE EXISTS (SELECT 1 FROM project_translation_glossaries local "
                "WHERE local.project_id = ? AND local.source_language = sync.source_language AND local.target_language = sync.target_language)",
                (project_id,),
            ).fetchall()
        sync_by_pair = {(row["source_language"], row["target_language"]): row for row in sync_rows}
        return [self._translation_glossary(row, sync_by_pair.get((row["source_language"], row["target_language"]))) for row in rows]''',
    )
    apply(
        STORAGE_PATH,
        '''                "WHERE sync.glossary_rule_id = ?",
                (row["glossary_rule_id"],),''',
        '''                "WHERE sync.source_language = ? AND sync.target_language = ? ORDER BY sync.synced_at DESC LIMIT 1",
                (row["source_language"], row["target_language"]),''',
        count=2,
    )
    apply(
        TEST_PATH,
        '''        self.assertEqual("glossary", restored["type"])
        self.assertEqual("Character role", restored["entries"][0]["context"])
        self.assertEqual("remote-1", restored["providerSync"]["remoteGlossaryId"])
        self.assertIsNone(other_restored["providerSync"])
        self.assertEqual("unsynced", other_restored["syncState"])
        self.assertIsNotNone(other_fetched)
        self.assertIsNone(other_fetched["providerSync"])''',
        '''        self.assertEqual("glossary", restored["type"])
        self.assertEqual("Character role", restored["entries"][0]["context"])
        self.assertEqual("synced", restored["syncState"])
        self.assertEqual("remote-1", restored["providerSync"]["remoteGlossaryId"])
        self.assertTrue(restored["providerSync"]["isCurrent"])

        self.assertEqual("unsynced", other_restored["syncState"])
        self.assertEqual(glossary["glossaryRuleId"], other_restored["providerSync"]["glossaryRuleId"])
        self.assertFalse(other_restored["providerSync"]["isCurrent"])
        self.assertIsNotNone(other_fetched)
        self.assertEqual("unsynced", other_fetched["syncState"])
        self.assertFalse(other_fetched["providerSync"]["isCurrent"])''',
    )
    print("Patch 42 applied successfully.")


if __name__ == "__main__":
    main()
