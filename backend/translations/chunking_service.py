"""Application orchestration for preparing chapter translation chunks."""

from __future__ import annotations

from typing import Any, Mapping

from .chunker import Chunker, chapter_paragraph_units


class ChunkPreparationService:
    def __init__(self, storage: Any, chunker: Chunker | None = None):
        self._storage = storage
        self._chunker = chunker or Chunker()

    def build_chapter_payload(self, project_id: str, chapter_id: str) -> dict[str, object]:
        book_structure = self._storage.get_book_structure(project_id)
        if book_structure is None:
            raise ValueError("Book structure not found.")

        chapter = self._find_chapter(book_structure, chapter_id)
        if chapter is None:
            raise ValueError("Chapter not found.")

        paragraph_units = chapter_paragraph_units(chapter)
        chunks = self._chunker.chunk_chapter(chapter_id, paragraph_units)

        return {
            "chapterId": chapter_id,
            "chunks": [
                {
                    "chunkId": chunk.chunk_id,
                    "sourceParagraphIds": list(chunk.source_paragraph_ids),
                    "requestText": chunk.request_text,
                }
                for chunk in chunks
            ],
        }

    @staticmethod
    def _find_chapter(book_structure: Mapping[str, object], chapter_id: str) -> Mapping[str, object] | None:
        chapters = book_structure.get("chapters")
        if not isinstance(chapters, list):
            return None
        return next(
            (
                chapter
                for chapter in chapters
                if isinstance(chapter, Mapping) and chapter.get("chapterId") == chapter_id
            ),
            None,
        )


__all__ = ["ChunkPreparationService"]
