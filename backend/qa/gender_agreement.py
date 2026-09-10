"""Non-AI Layer 1 check: gender/number agreement between a character's name
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
