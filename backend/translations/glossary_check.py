"""Glossary term matching for LLM translation: which terms a source text contains, and
whether the translation used their required Ukrainian equivalents.

Source matching normalizes typography first (’ ‘ ʼ → ', “ ” „ « » → ") and ignores case,
so "fled Justice’s court" matches the glossary term "Justice's Court". When terms
overlap, the longest match wins: "court" and "Justice" are not reported inside an
occurrence of "Justice's Court".

The translation check lemmatizes Ukrainian words (pymorphy3), so an equivalent in any
case or number counts: "Двору Правосуддя" satisfies "Двір Правосуддя".

pymorphy3 does not know most proper names and may reduce a case form to a wrong lemma
("Ларка" → "ларьок", while "Ларк" stays "ларк"). So a word also counts when its stem
matches: the common case endings are cut off both words and what is left is compared
("Ларк", "Ларка", "Ларку", "Ларком", "Ларкові" all have the stem "ларк").
"""

from __future__ import annotations

from functools import lru_cache
import re
from typing import Any, Iterable, Mapping, Sequence

_APOSTROPHES = str.maketrans({"’": "'", "‘": "'", "ʼ": "'", "′": "'", "`": "'", "“": '"', "”": '"', "„": '"', "«": '"', "»": '"'})
_TAG_RE = re.compile(r"<[^>]+>")
_FOOTNOTE_RE = re.compile("[0-9a-zA-Z_-]+")
_WORD_RE = re.compile(r"[^\W\d_]+(?:['-][^\W\d_]+)*")


def normalize_for_match(text: str) -> str:
    """Plain, comparable text: tags and footnote markers removed, typographic apostrophes
    and quotes made straight, whitespace collapsed, case folded."""
    plain = _FOOTNOTE_RE.sub("", _TAG_RE.sub(" ", text or ""))
    return " ".join(plain.translate(_APOSTROPHES).split()).casefold()


def _source(entry: Mapping[str, Any]) -> str:
    return " ".join(str(entry.get("source") or "").split())


def find_glossary_hits(entries: Iterable[Mapping[str, Any]], text: str) -> list[Mapping[str, Any]]:
    """Entries whose source occurs in `text` as whole words, longest match first-come:
    an occurrence that lies inside an already matched longer term does not count."""
    haystack = normalize_for_match(text)
    taken: list[tuple[int, int]] = []
    hits: list[Mapping[str, Any]] = []
    for entry in sorted(entries, key=lambda item: len(_source(item)), reverse=True):
        needle = normalize_for_match(_source(entry))
        if not needle:
            continue
        found = False
        for match in re.finditer(r"(?<!\w)" + re.escape(needle) + r"(?!\w)", haystack):
            span = match.span()
            if any(start <= span[0] and span[1] <= end for start, end in taken):
                continue
            taken.append(span)
            found = True
        if found:
            hits.append(entry)
    order = {id(entry): index for index, entry in enumerate(entries)} if isinstance(entries, Sequence) else {}
    return sorted(hits, key=lambda entry: order.get(id(entry), 0)) if order else hits


@lru_cache(maxsize=1)
def _morph():
    try:
        import pymorphy3
    except ImportError:  # the check degrades to exact word forms without the analyzer
        return None
    return pymorphy3.MorphAnalyzer(lang="uk")


@lru_cache(maxsize=20000)
def _lemmas(word: str) -> frozenset[str]:
    word = word.casefold()
    analyzer = _morph()
    forms = {word}
    if analyzer is not None:
        forms.update(parse.normal_form for parse in analyzer.parse(word))
    return frozenset(forms)


# Common Ukrainian case endings, longest first, cut off to get a word's stem.
_CASE_ENDINGS = tuple(sorted(("а", "у", "ові", "ом", "і", "е", "ю", "ою", "ам", "ами", "ах", "ів", "ей"), key=len, reverse=True))
_MIN_STEM = 3


def _stem(word: str) -> str:
    word = word.casefold()
    for ending in _CASE_ENDINGS:
        if word.endswith(ending) and len(word) - len(ending) >= _MIN_STEM:
            return word[: -len(ending)]
    return word


def _content_words(text: str) -> list[str]:
    # One- and two-letter words (з, і, та…) say nothing about whether a term was used.
    return [word for word in _WORD_RE.findall(normalize_for_match(text)) if len(word) > 2]


def missing_terms(entries: Iterable[Mapping[str, Any]], translation: str) -> list[Mapping[str, Any]]:
    """Entries whose target is not in `translation` in any grammatical form: each content
    word of the target must appear, lemmatized or by stem, somewhere in the translated paragraph."""
    available: set[str] = set()
    available_stems: set[str] = set()
    for word in _content_words(translation):
        available.update(_lemmas(word))
        available_stems.add(_stem(word))
    missing = []
    for entry in entries:
        target_words = _content_words(str(entry.get("target") or ""))
        if target_words and not all(_lemmas(word) & available or _stem(word) in available_stems for word in target_words):
            missing.append(entry)
    return missing


__all__ = ["find_glossary_hits", "missing_terms", "normalize_for_match"]
