#!/usr/bin/env python3
"""
apply_patch9.py

Fixes the bug where saving a project's series/book number (or any partial
project update that doesn't include projectRuleIds/projectGlossaryEntryIds)
silently wipes project_rules and project_glossary.

Run from the repository root (the directory containing backend/storage.py):

    python3 apply_patch9.py

It's idempotent: running it twice is safe (the second run will detect the
patch is already applied and exit without changes).
"""
from pathlib import Path
import sys

TARGET = Path("backend/storage.py")

EDIT_1_OLD = '''    def create_project(self, data: dict[str, Any]) -> dict[str, Any]:
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
        return self.get_project(project_id)'''

EDIT_1_NEW = '''    def create_project(self, data: dict[str, Any]) -> dict[str, Any]:
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
        return self.get_project(project_id)'''

EDIT_2_OLD = '''    @staticmethod
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
        )'''

EDIT_2_NEW = '''    @staticmethod
    def _write_project(connection: sqlite3.Connection, project: dict[str, Any], replace: bool, raw_data: dict[str, Any] | None = None) -> None:
        if not project["title"]:
            raise ValueError("Project title is required.")
        operation = "INSERT OR REPLACE" if replace else "INSERT"
        connection.execute(
            f"{operation} INTO book_projects(project_id, title, author_id, series_id, status, file_name, file_format, file_size, book_number, analysis_result, translation_rules, ai_configuration, chapter_count, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (project["projectId"], project["title"], project["authorId"], project["seriesId"], project["status"], project["fileName"], project["fileFormat"], project["fileSize"], project["bookNumber"], json.dumps(project["analysisResult"], ensure_ascii=False) if project["analysisResult"] is not None else None, project["translationRules"], json.dumps(project["aiConfiguration"], ensure_ascii=False), project["chapterCount"], project["createdAt"], project["updatedAt"]),
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
            )'''

EDITS = [(EDIT_1_OLD, EDIT_1_NEW), (EDIT_2_OLD, EDIT_2_NEW)]


def main():
    if not TARGET.exists():
        sys.exit(f"Не знайдено {TARGET} — запусти скрипт з кореня репозиторію.")

    text = TARGET.read_text(encoding="utf-8")

    if "raw_data: dict[str, Any] | None = None" in text and "touches_glossary" in text:
        print(f"{TARGET}: патч уже застосовано, нічого робити не треба.")
        return

    for old, new in EDITS:
        if old not in text:
            sys.exit(
                f"Не знайшов очікуваний фрагмент у {TARGET} — файл, схоже, "
                "відрізняється від очікуваної версії. Патч не застосовано."
            )
        text = text.replace(old, new, 1)

    TARGET.write_text(text, encoding="utf-8")
    print(f"{TARGET}: патч успішно застосовано.")


if __name__ == "__main__":
    main()
