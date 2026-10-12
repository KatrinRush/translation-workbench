"""«Знайти й замінити» in the translation text, as in Word, for Ukrainian text.

The stored translation is a small HTML (inline tags such as <b>/<i>, &amp; &lt; &gt;) with footnote
markers (\\uE000id\\uE000) inside. A replacement only ever touches the text between tags and markers:
a match is looked for inside one such piece, so formatting and footnotes cannot be broken. A match
that would cross a tag or a marker is not replaced; it is only counted (`across`).

Match modes:
  any    — any part of a word (no limits, Word's default);
  word   — a whole word: no letter, digit or apostrophe right before or after;
  start  — the beginning of a word with a Ukrainian case ending after it ("Дрейвен" finds "Дрейвена",
           "Дрейвену", "Дрейвеном" but not "Дрейвенський"); names in -ій/-ей also find their oblique
           forms ("Андрій" → "Андрія", "Андрієві"). For several words only the last one is inflected.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re

MODES = ("any", "word", "start")
MAX_QUERY_CHARS = 200
MAX_REPLACEMENT_CHARS = 500

# Case endings a noun/name may take after its stem (the empty ending is the stem itself).
ENDINGS = ("ові", "еві", "єві", "ами", "ями", "ом", "ем", "єм", "ою", "ею", "ям", "ах", "ях", "ів", "ам",
           "а", "у", "і", "ю", "я", "и", "ї")
# Oblique endings of names whose nominative ends in -ій / -ей (the й drops out of the stem).
SOFT_ENDINGS = ("єві", "єм", "я", "ю", "ї")
_HARD_TO_SOFT = {"а": "я", "у": "ю", "ові": "єві", "еві": "єві", "ом": "єм", "ем": "єм", "і": "ї"}
_SOFT_TO_HARD = {"я": "а", "ю": "у", "єві": "ові", "єм": "ом", "ї": "і"}

_APOSTROPHES = str.maketrans({"’": "'", "‘": "'", "ʼ": "'", "′": "'", "`": "'"})
_SPLIT = re.compile(r"(<[^>]*>|[^]*)")
_ENTITY = re.compile(r"&amp;|&lt;|&gt;|.", re.S)
_ENTITIES = {"&amp;": "&", "&lt;": "<", "&gt;": ">"}


def escape_text(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def normalize_apostrophes(text: str) -> str:
    return text.translate(_APOSTROPHES)


@dataclass
class Match:
    """One replaceable match. `start`/`end` count in the decoded text of its piece, `visibleStart`/
    `visibleEnd` in the text of the whole paragraph without tags and markers."""

    piece: int
    start: int
    end: int
    visible_start: int
    visible_end: int
    old: str
    new: str


@dataclass
class Scan:
    matches: list[Match] = field(default_factory=list)
    across: int = 0
    visible: str = ""


def _soft_name(word: str) -> bool:
    lowered = word.lower()
    return len(lowered) >= 3 and (lowered.endswith("ій") or lowered.endswith("ей"))


class Matcher:
    def __init__(self, query: str, replacement: str, match_case: bool = False, mode: str = "start"):
        if mode not in MODES:
            raise ValueError("Режим збігу має бути any, word або start.")
        query = normalize_apostrophes(" ".join(query.split()))
        if not query:
            raise ValueError("Вкажіть, що шукати.")
        self.query = query
        self.replacement = replacement
        self.match_case = bool(match_case)
        self.mode = mode
        flags = 0 if self.match_case else re.IGNORECASE
        words = query.split(" ")
        body = r"\s+".join(re.escape(word) for word in words)
        self._soft = mode == "start" and _soft_name(words[-1])
        self._soft_stem_len = len(query) - 1
        if mode == "any":
            self._primary = re.compile(body, flags)
        elif mode == "word":
            self._primary = re.compile(rf"(?<![\w']){body}(?![\w'])", flags)
        else:
            endings = "|".join(sorted(ENDINGS, key=len, reverse=True))
            self._primary = re.compile(rf"(?<![\w']){body}(?i:(?:{endings})?)(?![\w'])", flags)
        self._oblique = None
        if self._soft:
            stem = r"\s+".join(re.escape(word) for word in words[:-1] + [words[-1][:-1]])
            oblique = "|".join(sorted(SOFT_ENDINGS, key=len, reverse=True))
            self._oblique = re.compile(rf"(?<![\w']){stem}(?i:(?:{oblique}))(?![\w'])", flags)
        self._replacement_soft = _soft_name(replacement.split()[-1]) if replacement.split() else False

    # ------------------------------------------------------------------ one decoded piece

    def _spans(self, text: str) -> list[tuple[int, int, bool]]:
        """(start, end, oblique) of the matches in a decoded piece, in order, not overlapping."""
        spans = [(m.start(), m.end(), False) for m in self._primary.finditer(text)]
        if self._oblique is not None:
            taken = {start for start, _end, _flag in spans}
            spans.extend((m.start(), m.end(), True) for m in self._oblique.finditer(text) if m.start() not in taken)
            spans.sort()
        result: list[tuple[int, int, bool]] = []
        last_end = -1
        for span in spans:
            if span[0] >= last_end:
                result.append(span)
                last_end = span[1]
        return result

    def _new_text(self, old: str, oblique: bool) -> str:
        replacement = self.replacement
        if replacement and self.mode == "start":
            stem_len = self._soft_stem_len if oblique else len(self.query)
            suffix = old[stem_len:].lower() if len(old) >= stem_len else ""
            if oblique:
                replacement = (replacement[:-1] + suffix) if self._replacement_soft else (replacement + _SOFT_TO_HARD.get(suffix, suffix))
            elif suffix:
                if self._replacement_soft and not self._soft:
                    replacement = replacement[:-1] + _HARD_TO_SOFT.get(suffix, suffix)
                else:
                    replacement = replacement + suffix
        if replacement and not self.match_case and old:
            first = old[0]
            if first.isupper() and not replacement[0].isupper():
                replacement = replacement[0].upper() + replacement[1:]
            elif first.islower() and not replacement[0].islower():
                replacement = replacement[0].lower() + replacement[1:]
        return replacement

    # ------------------------------------------------------------------ a whole stored text

    @staticmethod
    def _pieces(stored: str) -> list[tuple[int, str, list[int]]]:
        """(index in the split text, decoded text, decoded index → raw index) of every text piece."""
        parts = _SPLIT.split(stored)
        pieces = []
        for index in range(0, len(parts), 2):
            raw = parts[index]
            decoded: list[str] = []
            mapping: list[int] = []
            for token in _ENTITY.finditer(raw):
                mapping.append(token.start())
                decoded.append(_ENTITIES.get(token.group(), token.group()))
            mapping.append(len(raw))
            pieces.append((index, "".join(decoded), mapping))
        return pieces

    def scan(self, stored: str) -> Scan:
        """The matches in a stored text and how many more cross a tag or a footnote marker."""
        result = Scan()
        pieces = self._pieces(stored or "")
        offset = 0
        boundaries: list[tuple[int, int]] = []
        for index, decoded, _mapping in pieces:
            normalized = normalize_apostrophes(decoded)
            for start, end, oblique in self._spans(normalized):
                old = decoded[start:end]
                result.matches.append(Match(index, start, end, offset + start, offset + end, old, self._new_text(old, oblique)))
            boundaries.append((offset, offset + len(decoded)))
            offset += len(decoded)
        result.visible = "".join(decoded for _index, decoded, _mapping in pieces)
        if len(pieces) > 1:
            joined = normalize_apostrophes(result.visible)
            inner = [edge for _start, edge in boundaries[:-1] if 0 < edge < len(joined)]
            replaced = [(match.visible_start, match.visible_end) for match in result.matches]
            for start, end, _oblique in self._spans(joined):
                crosses = any(start < edge < end for edge in inner)
                overlapped = any(start < b and a < end for a, b in replaced)
                if crosses and not overlapped:
                    result.across += 1
        return result

    def replace(self, stored: str, matches: list[Match] | None = None, only: int | None = None) -> tuple[str, list[Match]]:
        """The stored text with the matches replaced (`only` = the index of the one to replace) and the
        matches that were replaced. Tags, markers and untouched text stay byte for byte."""
        scan_matches = matches if matches is not None else self.scan(stored).matches
        chosen = [match for number, match in enumerate(scan_matches) if only is None or number == only]
        if not chosen:
            return stored, []
        parts = _SPLIT.split(stored)
        mappings = {index: mapping for index, _decoded, mapping in self._pieces(stored)}
        by_piece: dict[int, list[Match]] = {}
        for match in chosen:
            by_piece.setdefault(match.piece, []).append(match)
        for index, piece_matches in by_piece.items():
            raw = parts[index]
            mapping = mappings[index]
            out: list[str] = []
            cursor = 0
            for match in sorted(piece_matches, key=lambda item: item.start):
                out.append(raw[cursor:mapping[match.start]])
                out.append(escape_text(match.new))
                cursor = mapping[match.end]
            out.append(raw[cursor:])
            parts[index] = "".join(out)
        return "".join(parts), chosen


def context(visible: str, start: int, end: int, shown: str, radius: int = 40) -> str:
    """A short excerpt around a match with `shown` (the old or the new text) in ⟦ ⟧."""
    left = max(0, start - radius)
    right = min(len(visible), end + radius)
    prefix = "…" if left > 0 else ""
    suffix = "…" if right < len(visible) else ""
    return f"{prefix}{visible[left:start]}⟦{shown}⟧{visible[end:right]}{suffix}".replace("\n", " ")
