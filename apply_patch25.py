"""
Patch 25: character speech-register field on glossary entries.

Adds an optional free-text "speech_register" column to glossary_entries
(e.g. "Зодіак — постійна лайка", "Віктор — формальна мова, лайка виключена"),
alongside the existing character_gender field. Used later by the AI QA
style check (priority rule: flag softened profanity/register only when it
doesn't match the character's known register).

Run from the backend/ directory (same folder as storage.py):
    python apply_patch25.py
"""
from pathlib import Path

STORAGE_PATH = Path("storage.py")


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
    # 1. Schema: new column next to character_gender
    apply(
        STORAGE_PATH,
        '''CREATE TABLE IF NOT EXISTS glossary_entries (
    glossary_entry_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    target TEXT NOT NULL,
    note TEXT,
    character_gender TEXT,
    indeclinable INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL
);''',
        '''CREATE TABLE IF NOT EXISTS glossary_entries (
    glossary_entry_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    target TEXT NOT NULL,
    note TEXT,
    character_gender TEXT,
    speech_register TEXT,
    indeclinable INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL
);''',
    )

    # 2. Migration: add column to existing databases (same guarded-ALTER pattern
    #    already used for character_gender/indeclinable just above it)
    apply(
        STORAGE_PATH,
        '''            if "character_gender" not in glossary_entry_columns:
                connection.execute("ALTER TABLE glossary_entries ADD COLUMN character_gender TEXT")
            if "indeclinable" not in glossary_entry_columns:''',
        '''            if "character_gender" not in glossary_entry_columns:
                connection.execute("ALTER TABLE glossary_entries ADD COLUMN character_gender TEXT")
            if "speech_register" not in glossary_entry_columns:
                connection.execute("ALTER TABLE glossary_entries ADD COLUMN speech_register TEXT")
            if "indeclinable" not in glossary_entry_columns:''',
    )

    # 3. create_glossary_entry: accept + insert the new field
    apply(
        STORAGE_PATH,
        '''            "note": data.get("note"),
            "characterGender": _validated_character_gender(data.get("characterGender")),
            "indeclinable": bool(data.get("indeclinable", False)),
            "active": bool(data.get("active", True)),
            "updatedAt": _now(),
        }
        if not entry["source"] or not entry["target"]:
            raise ValueError("Glossary source and target are required.")
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO glossary_entries(glossary_entry_id, source, target, note, character_gender, indeclinable, active, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (entry["glossaryEntryId"], entry["source"], entry["target"], entry["note"], entry["characterGender"], int(entry["indeclinable"]), int(entry["active"]), entry["updatedAt"]),
            )
        return entry''',
        '''            "note": data.get("note"),
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
        return entry''',
    )

    # 4. update_glossary_entry: accept + persist the new field
    apply(
        STORAGE_PATH,
        '''            "note": data.get("note"),
            "characterGender": _validated_character_gender(data.get("characterGender")),
            "indeclinable": bool(data.get("indeclinable", False)),
            "active": bool(data.get("active", True)),
            "updatedAt": _now(),
        }
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE glossary_entries SET source = ?, target = ?, note = ?, character_gender = ?, indeclinable = ?, active = ?, updated_at = ? WHERE glossary_entry_id = ?",
                (updated["source"], updated["target"], updated["note"], updated["characterGender"], int(updated["indeclinable"]), int(updated["active"]), updated["updatedAt"], entry_id),
            )''',
        '''            "note": data.get("note"),
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
            )''',
    )

    # 5. _glossary_from_row: surface the field to the API/frontend
    apply(
        STORAGE_PATH,
        '''            "note": row["note"],
            "characterGender": row["character_gender"],
            "indeclinable": _bool(row["indeclinable"]),
            "active": _bool(row["active"]),
            "updatedAt": row["updated_at"],
        }

    def get_series_author_context''',
        '''            "note": row["note"],
            "characterGender": row["character_gender"],
            "speechRegister": row["speech_register"],
            "indeclinable": _bool(row["indeclinable"]),
            "active": _bool(row["active"]),
            "updatedAt": row["updated_at"],
        }

    def get_series_author_context''',
    )

    # 6. Validation helper, next to _validated_character_gender
    apply(
        STORAGE_PATH,
        '''def _validated_character_gender(value):
    if value is None:
        return None
    if value not in ("masc", "femn", "plur"):
        raise ValueError("Character gender must be 'masc', 'femn', 'plur', or omitted.")
    return value''',
        '''def _validated_character_gender(value):
    if value is None:
        return None
    if value not in ("masc", "femn", "plur"):
        raise ValueError("Character gender must be 'masc', 'femn', 'plur', or omitted.")
    return value


def _cleaned_speech_register(value):
    """Free-text note on how a character speaks (e.g. profanity level,
    formality) — no fixed vocabulary, just trimmed to None-or-text so a
    blank string doesn't get stored as a meaningless empty note."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None''',
    )

    # 7. New read helper for the future AI QA style check, next to
    #    get_project_character_genders (same project-scoped glossary lookup,
    #    but keyed by full target name -> register note, no stemming needed
    #    since this is just passed to the LLM as context text, not matched
    #    against inflected forms).
    apply(
        STORAGE_PATH,
        '''            genders[stem] = gender
        return genders

    def save_chapter_ai_analysis''',
        '''            genders[stem] = gender
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

    def save_chapter_ai_analysis''',
    )

    print("Patch 25 applied successfully.")


if __name__ == "__main__":
    main()
