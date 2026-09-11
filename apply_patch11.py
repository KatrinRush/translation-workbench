#!/usr/bin/env python3
"""
apply_patch11.py

Updates the glossary-limit test to match the new delete-before-create
ordering introduced by apply_patch10.py. The old test forced a
GlossaryLimitError on create() and expected the service to delete the
old remote glossary and retry — that was the old (buggy) ordering.
The new service deletes the known old glossary BEFORE attempting to
create the replacement, so a GlossaryLimitError at that point means
something untracked is occupying the slot, and must be reported as a
clean failure instead of retried blindly.

Run from the repository root (the directory containing
tests/test_translation_glossary_service.py):

    python3 apply_patch11.py

Idempotent: running it twice is safe.
"""
from pathlib import Path
import sys

TARGET = Path("tests/test_translation_glossary_service.py")

OLD = '''    def test_glossary_limit_reached_replaces_old_remote_glossary(self):
        item = self.storage.create_glossary_entry(
            {"source": "Dadzbog", "target": "Дажбог", "note": "", "active": True}
        )
        first = self.service.commit_project_glossary_draft(
            self.project["projectId"],
            {"sourceLanguage": "EN", "targetLanguage": "UK", "glossaryEntryIds": [item["glossaryEntryId"]]},
        )
        self.assertEqual("remote-1", first["providerSync"]["remoteGlossaryId"])

        second_item = self.storage.create_glossary_entry(
            {"source": "Jaga", "target": "Яга", "note": "", "active": True}
        )
        self.provider.limit_reached_once = True
        second = self.service.commit_project_glossary_draft(
            self.project["projectId"],
            {
                "glossaryRuleId": first["glossaryRuleId"],
                "sourceLanguage": "EN",
                "targetLanguage": "UK",
                "glossaryEntryIds": [item["glossaryEntryId"], second_item["glossaryEntryId"]],
            },
        )

        self.assertEqual("synced", second["providerSyncResult"]["status"])
        self.assertEqual(["remote-1"], self.provider.deleted)
        self.assertEqual("remote-2", second["providerSync"]["remoteGlossaryId"])'''

NEW = '''    def test_glossary_limit_reached_after_clearing_known_slot_reports_failure(self):
        item = self.storage.create_glossary_entry(
            {"source": "Dadzbog", "target": "Дажбог", "note": "", "active": True}
        )
        first = self.service.commit_project_glossary_draft(
            self.project["projectId"],
            {"sourceLanguage": "EN", "targetLanguage": "UK", "glossaryEntryIds": [item["glossaryEntryId"]]},
        )
        self.assertEqual("remote-1", first["providerSync"]["remoteGlossaryId"])

        second_item = self.storage.create_glossary_entry(
            {"source": "Jaga", "target": "Яга", "note": "", "active": True}
        )
        self.provider.limit_reached_once = True
        second = self.service.commit_project_glossary_draft(
            self.project["projectId"],
            {
                "glossaryRuleId": first["glossaryRuleId"],
                "sourceLanguage": "EN",
                "targetLanguage": "UK",
                "glossaryEntryIds": [item["glossaryEntryId"], second_item["glossaryEntryId"]],
            },
        )

        # The service must clear the slot it already knows about BEFORE attempting to
        # create the replacement — this is what lets an ordinary update succeed even on
        # DeepL's one-glossary-per-language-pair free plan. A GlossaryLimitError at this
        # point can only mean something the app doesn't track is occupying the slot, so
        # it must be reported cleanly rather than papered over with a blind retry.
        self.assertEqual(["remote-1"], self.provider.deleted)
        self.assertEqual("failed", second["providerSyncResult"]["status"])
        self.assertEqual("glossary_limit_reached", second["providerSyncResult"]["code"])

        found = self.storage.find_synced_project_glossary(
            self.project["projectId"], self.connection["connectionId"], "UK"
        )
        self.assertIsNone(found)'''


def main():
    if not TARGET.exists():
        sys.exit(f"Не знайдено {TARGET} — запусти скрипт з кореня репозиторію.")

    text = TARGET.read_text(encoding="utf-8")

    if OLD not in text and NEW in text:
        print(f"{TARGET}: патч уже застосовано, нічого робити не треба.")
        return

    if OLD not in text:
        sys.exit(
            f"Не знайшов очікуваний фрагмент у {TARGET} — файл, схоже, "
            "відрізняється від очікуваної версії. Патч не застосовано."
        )

    text = text.replace(OLD, NEW, 1)
    TARGET.write_text(text, encoding="utf-8")
    print(f"{TARGET}: патч успішно застосовано.")


if __name__ == "__main__":
    main()
