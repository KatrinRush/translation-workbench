"""
Patch 29: backend for the combined LLM AI-QA check (three categories:
critical meaning distortions, stylistic deviations, typos/nonexistent
words), building on the rubric worked out earlier.

Lives in QaService (backend/qa/), next to the existing non-AI
check_chapter_gender_agreement — both are "QA of the translation",
distinct from TranslationService.analyze_chapter (which is the
pre-translation ORIGINAL-text brief/ТЗ tool, a different feature despite
the similar name).

Adds:
  - QaServiceError (same shape as TranslationServiceError/ChatServiceError)
  - QaService now takes the credential vault + provider registry too, so it
    can call provider.analyze() the same way TranslationService/ChatService do
  - QaService.check_chapter_translation_quality(project_id, chapter_id,
    connection_ids): builds one prompt per chapter (original+translation
    pairs, plus character speech-register notes from patch 25), calls each
    requested connection's provider.analyze(), parses the JSON array each
    model returns, and returns per-paragraph findings tagged with category
    and sourceModel, plus the three counts by category
  - New endpoint: POST /api/projects/{projectId}/chapters/{chapterId}/qa-check
    body: { "connectionIds": [...] } — pass 1 id for a single-model run, 2+
    for the dual-run option

Run from the repo root (same folder as backend/):
    python apply_patch29.py
"""
from pathlib import Path

QA_SERVICE_PATH = Path("backend/qa/service.py")
QA_INIT_PATH = Path("backend/qa/__init__.py")
SERVER_PATH = Path("backend/server.py")


def apply(path: Path, old: str, new: str, count: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    occurrences = text.count(old)
    if occurrences != count:
        raise SystemExit(
            f"Expected {count} occurrence(s) of snippet in {path}, found {occurrences}.\n"
            f"--- snippet ---\n{old}\n---------------"
        )
    path.write_text(text.replace(old, new, count), encoding="utf-8")


def main() -> None:
    # 1. qa/service.py: imports + error class + constructor
    apply(
        QA_SERVICE_PATH,
        '''from __future__ import annotations

from typing import Any

from .gender_agreement import check_paragraph_gender_agreement


class QaService:
    def __init__(self, storage):
        self._storage = storage''',
        '''from __future__ import annotations

import json
from typing import Any

from .gender_agreement import check_paragraph_gender_agreement


class QaServiceError(RuntimeError):
    def __init__(self, message: str, http_status: int = 400, code: str = "qa_error"):
        super().__init__(message)
        self.http_status = http_status
        self.code = code


class QaService:
    def __init__(self, storage, vault=None, registry=None):
        self._storage = storage
        self._vault = vault
        self._registry = registry''',
    )

    # 2. qa/service.py: new method appended right after check_chapter_gender_agreement
    apply(
        QA_SERVICE_PATH,
        '''        return {
            "chapterId": chapter_id,
            "characterGendersChecked": character_genders,
            "paragraphResults": paragraph_results,
        }''',
        '''        return {
            "chapterId": chapter_id,
            "characterGendersChecked": character_genders,
            "paragraphResults": paragraph_results,
        }

    _QUALITY_CATEGORIES = {"critical", "stylistic", "typo"}

    def check_chapter_translation_quality(self, project_id: str, chapter_id: str, connection_ids: list[str]) -> dict[str, Any]:
        project = self._storage.get_project(project_id)
        if project is None:
            raise QaServiceError("Project not found.", 404, "not_found")
        if not isinstance(connection_ids, list) or not connection_ids or not all(isinstance(item, str) and item.strip() for item in connection_ids):
            raise QaServiceError("Choose at least one AI connection.", 400, "qa_invalid")

        paragraphs = self._storage.get_chapter_paragraphs(chapter_id)
        translatable = [p for p in paragraphs if not p["isService"] and p.get("translationText")]
        if not translatable:
            raise QaServiceError("Chapter has no translated paragraphs to check.", 400, "qa_empty")
        paragraph_by_id = {p["paragraphId"]: p for p in translatable}

        speech_registers = self._storage.get_project_character_registers(project_id)
        prompt = self._build_quality_prompt(translatable, speech_registers)

        connections = {item["connectionId"]: item for item in self._storage.list_integration_connections()}
        findings_by_paragraph: dict[str, list[dict[str, Any]]] = {}
        errors: dict[str, str] = {}

        for connection_id in dict.fromkeys(connection_ids):
            connection = connections.get(connection_id)
            if connection is None or not connection["enabled"] or connection["testStatus"] != "connected":
                errors[connection_id] = "AI connection is not active and tested."
                continue
            provider_id = connection["providerId"]
            if provider_id == "deepl":
                errors[connection_id] = "This connection cannot run AI QA."
                continue
            try:
                provider, credentials = self._provider_credentials(connection)
                raw_text = provider.analyze(credentials, prompt)
                parsed = self._parse_quality_response(raw_text)
            except (ValueError, QaServiceError) as error:
                errors[connection_id] = str(error)
                continue
            for item in parsed:
                paragraph_id = item.get("paragraphId")
                if paragraph_id not in paragraph_by_id:
                    continue
                findings_by_paragraph.setdefault(paragraph_id, []).append({
                    "category": item["category"],
                    "quote": item.get("quote", ""),
                    "explanation": item.get("explanation", ""),
                    "suggestion": item.get("suggestion", ""),
                    "sourceModel": provider_id,
                })

        counts = {"critical": 0, "stylistic": 0, "typo": 0}
        for findings in findings_by_paragraph.values():
            for finding in findings:
                counts[finding["category"]] += 1

        return {
            "chapterId": chapter_id,
            "counts": counts,
            "paragraphResults": [
                {"paragraphId": paragraph_id, "findings": findings}
                for paragraph_id, findings in findings_by_paragraph.items()
            ],
            "errors": errors,
        }

    @staticmethod
    def _build_quality_prompt(paragraphs: list[dict[str, Any]], speech_registers: dict[str, str]) -> str:
        pairs = "\\n\\n".join(
            f'[{paragraph["paragraphId"]}]\\nОригінал: {paragraph["originalText"]}\\nПереклад: {paragraph["translationText"]}'
            for paragraph in paragraphs
        )
        registers = "\\n".join(f"- {name}: {note}" for name, note in speech_registers.items()) or "Немає."
        return (
            "Ти перевіряєш якість перекладу художньої прози з англійської на українську. "
            "Порівняй кожен абзац оригіналу з перекладом і знайди ТІЛЬКИ реальні проблеми трьох типів:\\n\\n"
            "critical — значення слова/фрази, дія, роль персонажа, часова рамка або вид дієслова "
            "(одноразовість/повторюваність) у перекладі суттєво відрізняється від оригіналу, змінюючи те, "
            "що фактично стверджується. Приклад: гарчання перекладено як шепіт; \\"примусив\\" перекладено "
            "недоконаним видом \\"примушував\\" там, де йдеться про конкретний випадок, а не звичку.\\n\\n"
            "stylistic — факт і дія збережені, але втрачено тон, конотацію, грубість мовлення чи градацію. "
            "Пріоритетно позначай випадки, де груба/розмовна лексика оригіналу згладжена до нейтральної.\\n\\n"
            "typo — слова, яких не існує в українській мові (одруківки, неправильно утворені форми).\\n\\n"
            "НЕ позначай: переформулювання, якщо сенс і тон збережені; ідіоматичні/жаргонні відповідники, "
            "дібрані функціонально, а не буквально; вибір слова, що узгоджується з гліосарієм проєкту, "
            "навіть якщо це відрізняється від буквального перекладу.\\n\\n"
            f"Мовний регістр персонажів (використовуй, щоб оцінити, чи згладжування грубості виправдане):\\n{registers}\\n\\n"
            "Поверни ЛИШЕ JSON-масив об'єктів без жодного іншого тексту (без пояснень, без markdown-огорожі). "
            "Кожен об'єкт має поля: paragraphId (рядок, точно як у квадратних дужках нижче), "
            "category (\\"critical\\"|\\"stylistic\\"|\\"typo\\"), quote (коротка цитата з перекладу, що містить "
            "проблему), explanation (коротке пояснення українською, без спойлерів сюжету — лише про "
            "граматику/стиль/значення), suggestion (варіант виправлення або порожній рядок). "
            "Якщо проблем немає — поверни порожній масив [].\\n\\n"
            f"Абзаци для перевірки:\\n{pairs}"
        )

    @classmethod
    def _parse_quality_response(cls, raw_text: str) -> list[dict[str, Any]]:
        text = raw_text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
            text = text.strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError as error:
            raise QaServiceError(f"AI QA response was not valid JSON: {error}") from error
        if not isinstance(data, list):
            raise QaServiceError("AI QA response must be a JSON array.")
        cleaned = []
        for item in data:
            if not isinstance(item, dict):
                continue
            if item.get("category") not in cls._QUALITY_CATEGORIES:
                continue
            if not item.get("paragraphId"):
                continue
            cleaned.append(item)
        return cleaned

    def _provider_credentials(self, connection: dict[str, Any]):
        provider = self._registry.get(connection["providerId"]) if self._registry else None
        if provider is None:
            raise QaServiceError("AI QA provider is unavailable.", 503, "provider_unavailable")
        if not self._vault or not self._vault.available:
            raise QaServiceError("Credential storage is unavailable.", 503, "credential_storage_unavailable")
        record = self._storage.get_integration_connection_record(connection["connectionId"])
        try:
            credentials = self._vault.decrypt(record["credentialsCiphertext"])
        except Exception as error:
            raise QaServiceError("Stored credentials are unavailable.", 503, "credentials_locked") from error
        return provider, credentials''',
    )

    # 3. qa/__init__.py: export the new error class too
    apply(
        QA_INIT_PATH,
        '''from .service import QaService

__all__ = ["QaService"]''',
        '''from .service import QaService, QaServiceError

__all__ = ["QaService", "QaServiceError"]''',
    )

    # 4. server.py: import QaServiceError (both the "as package" and
    #    "as script" import branches)
    apply(
        SERVER_PATH,
        "    from .qa import QaService\n",
        "    from .qa import QaService, QaServiceError\n",
    )
    apply(
        SERVER_PATH,
        "    from qa import QaService\n",
        "    from qa import QaService, QaServiceError\n",
    )

    # 5. server.py: QaService now gets the vault + registry too
    apply(
        SERVER_PATH,
        "qa_service = QaService(storage)",
        "qa_service = QaService(storage, credential_vault, provider_registry)",
    )

    # 6. server.py: new route, right after the existing check-gender-agreement one
    apply(
        SERVER_PATH,
        '''            return 200, qa_service.check_chapter_gender_agreement(parts[2], parts[4])''',
        '''            return 200, qa_service.check_chapter_gender_agreement(parts[2], parts[4])
        if (
            len(parts) == 6
            and parts[0] == "api"
            and parts[1] == "projects"
            and parts[3] == "chapters"
            and parts[5] == "qa-check"
            and method == "POST"
        ):
            data = self.read_json()
            connection_ids = data.get("connectionIds", [])
            return 200, qa_service.check_chapter_translation_quality(parts[2], parts[4], connection_ids)''',
    )

    # 7. server.py: handle QaServiceError the same way the sibling *ServiceErrors are handled
    apply(
        SERVER_PATH,
        '''        except ChatServiceError as error:
            self.send_json(error.http_status, {"error": str(error), "code": error.code})''',
        '''        except ChatServiceError as error:
            self.send_json(error.http_status, {"error": str(error), "code": error.code})
        except QaServiceError as error:
            self.send_json(error.http_status, {"error": str(error), "code": error.code})''',
    )

    print("Patch 29 applied successfully.")


if __name__ == "__main__":
    main()
