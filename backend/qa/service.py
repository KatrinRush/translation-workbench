"""Non-AI QA orchestration: pulls translated paragraphs and character
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
