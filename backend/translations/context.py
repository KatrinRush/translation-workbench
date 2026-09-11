"""Build DeepL context from the source text surrounding a translation unit."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import re


_CLOSING_PUNCTUATION = "\"')]}"
_ABBREVIATIONS = {"mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "etc", "e.g", "i.e"}
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_tags(text: str) -> str:
    """Remove inline rich-text tags (<i>, </b>, <s>...) before sentence splitting.

    DeepL context is plain guidance text, not rendered output — it doesn't
    need formatting. Splitting on tag-containing text is what produced
    orphaned opening/closing tags when a single <i>...</i> run spanned
    several sentences (the sentence boundary lands *inside* the tag pair).
    """
    return _TAG_RE.sub("", text)


def _sentences(text: str) -> list[str]:
    sentences: list[str] = []
    start = 0
    index = 0
    while index < len(text):
        if text[index] not in ".!?":
            index += 1
            continue

        end = index + 1
        while end < len(text) and text[end] in ".!?" + _CLOSING_PUNCTUATION:
            end += 1
        candidate = text[start:end].strip()
        word_before_punctuation = re.search(r"([A-Za-z]+(?:['-][A-Za-z]+)?)$", text[start:index])
        is_abbreviation = (
            text[index] == "."
            and word_before_punctuation is not None
            and word_before_punctuation.group(1).lower() in _ABBREVIATIONS
        )
        next_is_boundary = end == len(text) or text[end].isspace()
        if candidate and next_is_boundary and not is_abbreviation:
            sentences.append(candidate)
            start = end
        index = end

    remainder = text[start:].strip()
    if remainder:
        sentences.append(remainder)
    return sentences


def _source_sentences(
    book_structure: Mapping[str, object],
) -> tuple[list[str], list[str]]:
    """Return source sentences and the paragraph ID owning each sentence."""
    sentences: list[str] = []
    paragraph_ids: list[str] = []
    chapters = book_structure.get("chapters")
    if not isinstance(chapters, Sequence) or isinstance(chapters, (str, bytes)):
        return sentences, paragraph_ids

    for chapter in chapters:
        if not isinstance(chapter, Mapping):
            continue
        elements = chapter.get("elements")
        if not isinstance(elements, Sequence) or isinstance(elements, (str, bytes)):
            continue
        for element in elements:
            if not isinstance(element, Mapping) or element.get("type") != "paragraph":
                continue
            paragraph_id = element.get("paragraphId")
            original_text = element.get("originalText")
            if (
                not isinstance(paragraph_id, str)
                or not isinstance(original_text, str)
            ):
                continue
            if element.get("isService", False):
                continue
            paragraph_sentences = _sentences(_strip_tags(original_text))
            sentences.extend(paragraph_sentences)
            paragraph_ids.extend([paragraph_id] * len(paragraph_sentences))
    return sentences, paragraph_ids


def build_deepl_context(
    book_structure: Mapping[str, object],
    current_paragraph_ids: Sequence[str],
    sentences_each_side: int = 3,
) -> str | None:
    """Return surrounding source sentences for a paragraph or translation chunk."""
    if sentences_each_side <= 0:
        return None

    current_ids = set(current_paragraph_ids)
    sentences, paragraph_ids = _source_sentences(book_structure)
    if not sentences:
        return None

    target_boundaries = [
        index
        for index, paragraph_id in enumerate(paragraph_ids)
        if paragraph_id in current_ids
    ]
    if not target_boundaries:
        return None

    first_target = min(target_boundaries)
    last_target = max(target_boundaries)
    before = sentences[:first_target][-sentences_each_side:]
    after = sentences[last_target + 1:][:sentences_each_side]
    return " ".join(before + after) or None


__all__ = ["build_deepl_context"]
