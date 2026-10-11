"""Per-paragraph narrator gender/person, shared by AI QA and LLM translation."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

NARRATOR_GENDERS = ("masc", "femn", "third")
NARRATOR_LABELS = {"masc": "чоловік", "femn": "жінка", "third": "третя особа"}


def effective_narrators(default_narrator: str | None, paragraphs: Iterable[Mapping[str, Any]]) -> dict[str, str | None]:
    """Walks the chapter's paragraphs in order (as returned by
    get_chapter_paragraphs, i.e. ordered by paragraph_index) and resolves
    each paragraph's "effective" narrator gender/person: whatever the
    nearest preceding "narratorChange" marker set, carried forward, or
    the project default when no marker has appeared yet in the chapter.
    A book with no single default (mixed POV from paragraph one, no
    project-wide narratorGender set) legitimately has paragraphs with no
    known narrator until the first marker — those map to None rather than
    guessing "third", so callers can omit them instead of asserting a
    possibly-wrong gender/person."""
    current = default_narrator if default_narrator in NARRATOR_GENDERS else None
    effective: dict[str, str | None] = {}
    for paragraph in paragraphs:
        change = paragraph.get("narratorChange")
        if change in NARRATOR_GENDERS:
            current = change
        effective[paragraph["paragraphId"]] = current
    return effective


__all__ = ["NARRATOR_GENDERS", "NARRATOR_LABELS", "effective_narrators"]
