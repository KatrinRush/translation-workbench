"""Deterministic paragraph chunking for translation preparation.

This module prepares translation units from chapter paragraphs.
It does not call providers and does not use credentials.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ParagraphUnit:
    paragraph_id: str
    original_text: str


@dataclass(frozen=True)
class ChunkParagraph:
    paragraph_id: str
    original_text: str


@dataclass(frozen=True)
class TranslationChunk:
    chunk_id: str
    chapter_id: str
    source_paragraphs: tuple[ChunkParagraph, ...]

    @property
    def source_paragraph_ids(self) -> tuple[str, ...]:
        return tuple(item.paragraph_id for item in self.source_paragraphs)

    @property
    def request_text(self) -> str:
        return "\n\n".join(item.original_text for item in self.source_paragraphs)

    def to_dict(self) -> dict[str, object]:
        return {
            "chunkId": self.chunk_id,
            "chapterId": self.chapter_id,
            "sourceParagraphIds": list(self.source_paragraph_ids),
            "sourceParagraphs": [
                {
                    "paragraphId": item.paragraph_id,
                    "originalText": item.original_text,
                }
                for item in self.source_paragraphs
            ],
            "requestText": self.request_text,
        }


class Chunker:
    """Build deterministic chapter-local chunks from paragraph units.

    Policy:
    - Keep source order.
    - Never split or merge across chapters.
    - Try to keep each chunk under max_chunk_chars measured on request text.
    - If a single paragraph is longer than max_chunk_chars, keep it as a single chunk.
    - Keep empty paragraphs as valid units.
    """

    def __init__(self, max_chunk_chars: int = 1800, paragraph_separator: str = "\n\n"):
        if max_chunk_chars <= 0:
            raise ValueError("max_chunk_chars must be a positive integer.")
        self._max_chunk_chars = max_chunk_chars
        self._separator = paragraph_separator

    def chunk_chapter(self, chapter_id: str, paragraphs: Sequence[ParagraphUnit]) -> list[TranslationChunk]:
        chunks: list[TranslationChunk] = []
        current: list[ChunkParagraph] = []
        current_size = 0

        def flush_current() -> None:
            nonlocal current
            nonlocal current_size
            if not current:
                return
            chunk_index = len(chunks) + 1
            chunks.append(
                TranslationChunk(
                    chunk_id=f"{chapter_id}:chunk:{chunk_index:04d}",
                    chapter_id=chapter_id,
                    source_paragraphs=tuple(current),
                )
            )
            current = []
            current_size = 0

        for unit in paragraphs:
            item = ChunkParagraph(paragraph_id=unit.paragraph_id, original_text=unit.original_text)
            additional = len(item.original_text)
            if current:
                additional += len(self._separator)

            # Start a new chunk when adding this paragraph would exceed budget.
            if current and current_size + additional > self._max_chunk_chars:
                flush_current()
                additional = len(item.original_text)

            current.append(item)
            current_size += additional

        flush_current()
        return chunks


def chapter_paragraph_units(chapter: Mapping[str, object]) -> list[ParagraphUnit]:
    """Extract paragraph units from a chapter structure returned by storage."""
    chapter_elements = chapter.get("elements")
    if not isinstance(chapter_elements, Iterable):
        return []

    units: list[ParagraphUnit] = []
    for element in chapter_elements:
        if not isinstance(element, Mapping):
            continue
        if element.get("type") != "paragraph":
            continue
        paragraph_id = element.get("paragraphId")
        if not isinstance(paragraph_id, str) or not paragraph_id:
            continue
        original_text = element.get("originalText")
        if not isinstance(original_text, str):
            original_text = ""
        units.append(ParagraphUnit(paragraph_id=paragraph_id, original_text=original_text))
    return units


def chunk_book_structure(book_structure: Mapping[str, object], chunker: Chunker | None = None) -> list[TranslationChunk]:
    """Chunk all chapters from a stored book structure without crossing chapter boundaries."""
    active_chunker = chunker or Chunker()
    chapters = book_structure.get("chapters")
    if not isinstance(chapters, Iterable):
        return []

    chunks: list[TranslationChunk] = []
    for chapter in chapters:
        if not isinstance(chapter, Mapping):
            continue
        chapter_id = chapter.get("chapterId")
        if not isinstance(chapter_id, str) or not chapter_id:
            continue
        units = chapter_paragraph_units(chapter)
        chunks.extend(active_chunker.chunk_chapter(chapter_id, units))
    return chunks


__all__ = [
    "ChunkParagraph",
    "Chunker",
    "ParagraphUnit",
    "TranslationChunk",
    "chapter_paragraph_units",
    "chunk_book_structure",
]
