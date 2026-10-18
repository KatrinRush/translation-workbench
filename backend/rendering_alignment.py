"""Ukrainian word forms (pymorphy3) and the alignment of an English term with its rendering in a translation, without a model.

A rendering is looked for among candidates: the translation variants of the lemma (all senses of its inventory) and the
renderings already known for it in the project. A candidate is found in the translation in any of its forms; the paragraph
gets a rendering only when exactly one candidate is there. Several candidates or none: «не визначено».
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any, Iterable

try:
    from .translations.glossary_check import _APOSTROPHES
except ImportError:  # launched as `python server.py` from inside backend/
    from translations.glossary_check import _APOSTROPHES

_WORD = re.compile(r"[\w'’]+")
MIN_WORD = 3  # shorter words (у, в, ні) give noise in any form

_CASE_ENDINGS = tuple(sorted(("а", "у", "ові", "еві", "ом", "ем", "і", "е", "є", "ю", "ою", "ею", "єю", "ам", "ами", "ах", "ів", "ей", "и", "я", "ям", "ями", "ях", "ї"), key=len, reverse=True))


@lru_cache(maxsize=1)
def _analyzer():
    try:
        import pymorphy3
    except ImportError:
        return None
    return pymorphy3.MorphAnalyzer(lang="uk")


def ukrainian_stem(word: str) -> str:
    for ending in _CASE_ENDINGS:
        if word.endswith(ending) and len(word) - len(ending) >= 3:
            return word[: -len(ending)]
    return word


@lru_cache(maxsize=4096)
def ukrainian_forms(word: str) -> tuple[frozenset[str], str | None]:
    """(forms, stem): every form of the most probable lemmas of the word; for a word the analyzer does not know
    (a name), also its stem, which then matches by prefix."""
    word = word.casefold().translate(_APOSTROPHES)
    analyzer = _analyzer()
    forms = {word}
    stem = None
    if analyzer is None:
        return frozenset(forms), ukrainian_stem(word)
    parses = analyzer.parse(word)
    lemmas: list[Any] = []
    for parse in parses:  # all readings: «кочерги» is read first as a plural-only word, and only then as a form of «кочерга»
        if len(lemmas) < 4 and parse.normal_form not in {item.normal_form for item in lemmas} and (not lemmas or parse.score >= 0.3):
            lemmas.append(parse)
    for parse in lemmas:
        forms.update(form.word.translate(_APOSTROPHES) for form in parse.lexeme)
    if not parses or not parses[0].is_known:
        stem = ukrainian_stem(word)
    return frozenset(forms), stem


@lru_cache(maxsize=4096)
def canonical_rendering(text: str) -> str:
    """A rendering as one comparable string: the lemma of a single word (кочергу → кочерга), else the lowercase phrase.
    «кочерги» is read first as a plural-only word (Pltm), so such readings are the last choice: it is also a form of «кочерга»."""
    words = _WORD.findall((text or "").translate(_APOSTROPHES))
    if len(words) == 1:
        analyzer = _analyzer()
        word = words[0].casefold()
        if not analyzer:
            return word
        parses = analyzer.parse(word)
        regular = [parse for parse in parses if "Pltm" not in parse.tag]
        return (regular or parses)[0].normal_form
    return " ".join(word.casefold() for word in words) or (text or "").strip().casefold()


_CYRILLIC_WORD = re.compile(r"[Ѐ-ӿ]")


@lru_cache(maxsize=4096)
def unknown_word(word: str) -> bool:
    """True when pymorphy3 does not know a Ukrainian word from its dictionary (it only guessed it from a suffix: «баранння»).
    Latin words, numbers and a missing analyzer never count as unknown."""
    analyzer = _analyzer()
    if analyzer is None or not _CYRILLIC_WORD.search(word):
        return False
    return not any(parse.is_known for parse in analyzer.parse(word.casefold().translate(_APOSTROPHES)))


def has_unknown_words(text: str) -> bool:
    """A variant with a word the dictionary does not know. A hyphenated compound is checked by its parts."""
    return any(unknown_word(part) for word in _WORD.findall(text or "") for part in word.split("-") if part)


def _candidate_pattern(text: str) -> re.Pattern[str] | None:
    words = [word.casefold() for word in _WORD.findall((text or "").translate(_APOSTROPHES))]
    if not words or (len(words) == 1 and len(words[0]) < MIN_WORD):
        return None
    parts = []
    for word in words:
        forms, stem = ukrainian_forms(word)
        options = [re.escape(form) for form in sorted(forms, key=len, reverse=True)]
        if stem:
            options.append(re.escape(stem) + r"[\w'’]*")
        parts.append("(?:" + "|".join(options) + ")")
    return re.compile(r"(?<![\w'’])" + r"[^\w'’]+".join(parts) + r"(?![\w'’])", re.IGNORECASE)


def align_candidates(translation: str, candidates: Iterable[str]) -> dict[str, Any] | None:
    """The one candidate found in the translation: {"text": the form as written, "key": canonical form,
    "ranges": [[start, end], ...] of all its occurrences}. None when there are none or several different ones."""
    text = (translation or "").translate(_APOSTROPHES)
    hits: list[tuple[int, int, str]] = []
    for candidate in dict.fromkeys(candidates):
        pattern = _candidate_pattern(candidate)
        if pattern is None:
            continue
        key = canonical_rendering(candidate)
        hits.extend((match.start(), match.end(), key) for match in pattern.finditer(text))
    # a longer phrase swallows the shorter candidate inside it
    kept = [hit for hit in hits if not any(other[2] != hit[2] and other[0] <= hit[0] and hit[1] <= other[1] and (other[1] - other[0]) > (hit[1] - hit[0])
                                           for other in hits)]
    keys = {hit[2] for hit in kept}
    if len(keys) != 1:
        return None
    kept.sort()
    ranges = []
    for start, end, _key in kept:
        if not ranges or start >= ranges[-1][1]:
            ranges.append([start, end])
    return {"text": translation[ranges[0][0]:ranges[0][1]], "key": next(iter(keys)), "ranges": ranges}


def occurs(translation: str, rendering: str) -> list[list[int]]:
    """Where the rendering (in any form) stands in the translation."""
    found = align_candidates(translation, [rendering])
    return found["ranges"] if found else []


__all__ = ["has_unknown_words", "unknown_word", "align_candidates", "canonical_rendering", "occurs", "ukrainian_forms", "ukrainian_stem"]
