from pathlib import Path

def create_file(file_path, content, label):
    path = Path(file_path)
    if path.exists():
        print(f"SKIP (вже існує): {label}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"OK: {label}")

def patch(file_path, old, new, label):
    path = Path(file_path)
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"[{label}] Очікував 1 збіг, знайшов {count}. Нічого не змінено.")
    path.write_text(text.replace(old, new), encoding="utf-8")
    print(f"OK: {label}")


# --- нові файли ---

create_file(
    "backend/qa/__init__.py",
    '''from .service import QaService

__all__ = ["QaService"]
''',
    "backend/qa/__init__.py",
)

create_file(
    "backend/qa/gender_agreement.py",
    '''"""Non-AI Layer 1 check: gender/number agreement between a character's name
and nearby past-tense verbs / short predicate adjectives in the Ukrainian
translation.

Deliberately does NOT use pymorphy3 to identify the character's own name
(it guesses unreliably on invented fantasy names) or to decline/inflect it
(same unreliability, confirmed empirically). Character identity and gender
come only from the glossary. pymorphy3 is used only to classify nearby
words that are already real Ukrainian dictionary words.
"""
from __future__ import annotations

import re

import pymorphy3

morph = pymorphy3.MorphAnalyzer(lang="uk")

_CLAUSE_BOUNDARY_WORDS = {
    "як", "що", "коли", "поки", "оскільки", "хоча", "якщо", "бо", "адже",
    "котрий", "котра", "котрі", "який", "яка", "які", "а", "але",
}

_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]?")
_TOKEN_RE = re.compile(r"[А-Яа-яІіЇїЄєҐґ'-]+|,")


def _tokenize(text: str) -> list[tuple[str, int, int]]:
    return [(m.group(0), m.start(), m.end()) for m in _TOKEN_RE.finditer(text)]


def _split_into_clauses(tokens: list[tuple[str, int, int]]) -> list[list[tuple[str, int, int]]]:
    clauses: list[list[tuple[str, int, int]]] = []
    current: list[tuple[str, int, int]] = []
    for tok in tokens:
        word, _start, _end = tok
        is_boundary = word == "," or word.lower() in _CLAUSE_BOUNDARY_WORDS
        if is_boundary and current:
            clauses.append(current)
            current = []
            if word != ",":
                current.append(tok)
            continue
        current.append(tok)
    if current:
        clauses.append(current)
    return [clause for clause in clauses if clause]


def _find_gender_bearing_words(clause: list[tuple[str, int, int]], exclude_index: int):
    candidates = []
    for i, (word, start, end) in enumerate(clause):
        if i == exclude_index:
            continue
        genders_found: dict[str, str] = {}
        for parse in morph.parse(word):
            tag_str = str(parse.tag)
            if "past" not in tag_str and "ADJS" not in tag_str:
                continue
            if "femn" in tag_str:
                genders_found["femn"] = tag_str
            elif "masc" in tag_str:
                genders_found["masc"] = tag_str
        # 0 варіантів -> слово не гендерне; 2+ з різним родом -> реальна
        # неоднозначність (pymorphy3 має тільки-однакового-скору омоніми) -
        # в обох випадках безпечніше промовчати, ніж вгадувати.
        if len(genders_found) == 1:
            gender, tag_str = next(iter(genders_found.items()))
            candidates.append((word, start, end, gender, tag_str))
    return candidates


def check_paragraph_gender_agreement(text: str, character_genders: dict[str, str]) -> list[dict]:
    """
    character_genders: {stem: 'femn'|'masc'|'plur'} — stem matched via
    case-insensitive str.startswith against each token in the text.

    Returns a list of issue dicts with character offsets into `text`,
    so the frontend can highlight the exact span without ambiguity when
    the same word repeats elsewhere in the paragraph.
    """
    if not character_genders or not text:
        return []

    issues = []
    for sentence_match in _SENTENCE_RE.finditer(text):
        sentence_text = sentence_match.group(0)
        sentence_offset = sentence_match.start()
        tokens = _tokenize(sentence_text)
        for clause in _split_into_clauses(tokens):
            for i, (word, _start, _end) in enumerate(clause):
                for stem, expected_gender in character_genders.items():
                    if not word.lower().startswith(stem.lower()):
                        continue
                    for cand_word, cand_start, cand_end, found_gender, tag_str in _find_gender_bearing_words(clause, i):
                        if expected_gender == "plur":
                            # для 'ви'-персонажа БУДЬ-ЯКЕ однинне (femn чи
                            # masc) дієслово поруч — помилка
                            mismatch = True
                        else:
                            mismatch = found_gender != expected_gender
                        if mismatch:
                            issues.append({
                                "name": word,
                                "word": cand_word,
                                "wordStart": sentence_offset + cand_start,
                                "wordEnd": sentence_offset + cand_end,
                                "expectedGender": expected_gender,
                                "foundGender": found_gender,
                                "tag": tag_str,
                            })
    return issues
''',
    "backend/qa/gender_agreement.py",
)

create_file(
    "backend/qa/service.py",
    '''"""Non-AI QA orchestration: pulls translated paragraphs and character
gender facts from storage, runs the checks in gender_agreement.py, and
returns per-paragraph findings for the frontend to highlight."""
from __future__ import annotations

from typing import Any

from .gender_agreement import check_paragraph_gender_agreement


class QaService:
    def __init__(self, storage):
        self._storage = storage

    def check_chapter_gender_agreement(self, project_id: str, chapter_id: str) -> dict[str, Any]:
        character_genders = self._storage.get_project_character_genders(project_id)
        paragraphs = self._storage.get_chapter_paragraphs(chapter_id)

        paragraph_results = []
        for paragraph in paragraphs:
            if paragraph["isService"]:
                continue
            text = paragraph["translationText"]
            if not text:
                continue
            issues = check_paragraph_gender_agreement(text, character_genders)
            if issues:
                paragraph_results.append({
                    "paragraphId": paragraph["paragraphId"],
                    "issues": issues,
                })

        return {
            "chapterId": chapter_id,
            "characterGendersChecked": character_genders,
            "paragraphResults": paragraph_results,
        }
''',
    "backend/qa/service.py",
)


# --- requirements.txt ---

patch(
    "requirements.txt",
    "pytest>=9.0",
    "pytest>=9.0\npymorphy3>=2.0\npymorphy3-dicts-uk>=2.4",
    "requirements.txt: pymorphy3",
)


# --- backend/server.py ---

patch(
    "backend/server.py",
    '''    from .logging_utils import configure_logging, read_recent_lines
    from .parsers import parse_epub
    from .storage import Storage
    from .translations import TranslationService, TranslationServiceError
except ImportError:''',
    '''    from .logging_utils import configure_logging, read_recent_lines
    from .parsers import parse_epub
    from .qa import QaService
    from .storage import Storage
    from .translations import TranslationService, TranslationServiceError
except ImportError:''',
    "server.py: import (relative branch)",
)

patch(
    "backend/server.py",
    '''    from logging_utils import configure_logging, read_recent_lines
    from parsers import parse_epub
    from storage import Storage
    from translations import TranslationService, TranslationServiceError''',
    '''    from logging_utils import configure_logging, read_recent_lines
    from parsers import parse_epub
    from qa import QaService
    from storage import Storage
    from translations import TranslationService, TranslationServiceError''',
    "server.py: import (bare branch)",
)

patch(
    "backend/server.py",
    '''translation_service = TranslationService(storage, credential_vault, provider_registry)
chat_service = ChatService(storage, credential_vault, provider_registry)
export_service = ExportService(storage)''',
    '''translation_service = TranslationService(storage, credential_vault, provider_registry)
chat_service = ChatService(storage, credential_vault, provider_registry)
export_service = ExportService(storage)
qa_service = QaService(storage)''',
    "server.py: instantiate QaService",
)

patch(
    "backend/server.py",
    '''            return 200, translation_service.translate_chapter(parts[2], parts[4], self.read_json())''',
    '''            return 200, translation_service.translate_chapter(parts[2], parts[4], self.read_json())
        if (
            len(parts) == 6
            and parts[0] == "api"
            and parts[1] == "projects"
            and parts[3] == "chapters"
            and parts[5] == "check-gender-agreement"
            and method == "POST"
        ):
            return 200, qa_service.check_chapter_gender_agreement(parts[2], parts[4])''',
    "server.py: check-gender-agreement route",
)


# --- backend/storage.py ---

patch(
    "backend/storage.py",
    '''    def get_chapter(self, chapter_id: str) -> dict[str, Any] | None:
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

    def save_chapter_ai_analysis''',
    '''    def get_chapter(self, chapter_id: str) -> dict[str, Any] | None:
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
                "SELECT paragraph_id, paragraph_index, original_text, translation_text, reviewed, is_service "
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
                "isService": _bool(row["is_service"]),
            }
            for row in rows
        ]

    def get_project_character_genders(self, project_id: str) -> dict[str, str]:
        """Стем перекладеного імені персонажа -> \'femn\'|\'masc\'|\'plur\', зібрані
        з власного і успадкованого глосарія проєкту. Стем для жіночого роду
        отримується відкиданням кінцевого \'а\'/\'я\' (звичайне українське
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

    def save_chapter_ai_analysis''',
    "storage.py: get_chapter_paragraphs + get_project_character_genders",
)

print("\nГотово, всі 8 кроків виконано.")
