"""Non-AI QA orchestration: pulls translated paragraphs and character
gender facts from storage, runs the checks in gender_agreement.py, and
returns per-paragraph findings for the frontend to highlight."""
from __future__ import annotations

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
        self._registry = registry

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

    _QUALITY_CATEGORIES = {"critical", "stylistic", "typo"}
    _QUALITY_BATCH_SIZE = 5

    _QUALITY_BATCH_ATTEMPTS = 2

    def check_chapter_translation_quality(
        self,
        project_id: str,
        chapter_id: str,
        connection_ids: list[str],
        batch_index: int = 0,
        paragraph_ids: list[str] | None = None,
        categories: list[str] | None = None,
        batch_size: int | None = None,
    ) -> dict[str, Any]:
        project = self._storage.get_project(project_id)
        if project is None:
            raise QaServiceError("Project not found.", 404, "not_found")
        if not isinstance(connection_ids, list) or not connection_ids or not all(isinstance(item, str) and item.strip() for item in connection_ids):
            raise QaServiceError("Choose at least one AI connection.", 400, "qa_invalid")
        if not isinstance(batch_index, int) or batch_index < 0:
            raise QaServiceError("Invalid batch index.", 400, "qa_invalid")
        if categories is None:
            active_categories = set(self._QUALITY_CATEGORIES)
        else:
            if not isinstance(categories, list) or not categories or not set(categories).issubset(self._QUALITY_CATEGORIES):
                raise QaServiceError("Invalid QA categories.", 400, "qa_invalid")
            active_categories = set(categories)
        effective_batch_size = batch_size if isinstance(batch_size, int) and batch_size > 0 else self._QUALITY_BATCH_SIZE

        paragraphs = self._storage.get_chapter_paragraphs(chapter_id)
        narrator_by_paragraph = self._effective_narrators(project.get("narratorGender"), paragraphs)
        translatable = [p for p in paragraphs if not p["isService"] and p.get("translationText")]
        if paragraph_ids is not None:
            if not isinstance(paragraph_ids, list) or not paragraph_ids or not all(isinstance(item, str) and item.strip() for item in paragraph_ids):
                raise QaServiceError("Invalid paragraph selection.", 400, "qa_invalid")
            wanted = set(paragraph_ids)
            translatable = [p for p in translatable if p["paragraphId"] in wanted]
        if not translatable:
            raise QaServiceError("Chapter has no translated paragraphs to check.", 400, "qa_empty")
        paragraph_by_id = {p["paragraphId"]: p for p in translatable}
        batches = [
            translatable[i:i + effective_batch_size]
            for i in range(0, len(translatable), effective_batch_size)
        ]
        if batch_index >= len(batches):
            raise QaServiceError("Batch index out of range.", 400, "qa_invalid")
        batch = batches[batch_index]

        speech_registers = self._storage.get_project_character_registers(project_id)

        connections = {item["connectionId"]: item for item in self._storage.list_integration_connections()}
        new_findings: list[dict[str, Any]] = []
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
            except QaServiceError as error:
                errors[connection_id] = str(error)
                continue
            prompt = self._build_quality_prompt(batch, speech_registers, active_categories, narrator_by_paragraph)
            parsed = None
            last_error: Exception | None = None
            for _attempt in range(self._QUALITY_BATCH_ATTEMPTS):
                try:
                    raw_text = provider.analyze(credentials, prompt)
                    parsed = self._parse_quality_response(raw_text, active_categories)
                    break
                except (ValueError, QaServiceError) as error:
                    last_error = error
            if parsed is None:
                errors[connection_id] = str(last_error)
                continue
            for item in parsed:
                paragraph_id = item.get("paragraphId")
                if paragraph_id not in paragraph_by_id:
                    continue
                new_findings.append({
                    "paragraphId": paragraph_id,
                    "category": item["category"],
                    "quote": item.get("quote", ""),
                    "explanation": item.get("explanation", ""),
                    "suggestion": item.get("suggestion", ""),
                    "sourceModel": provider_id,
                })

        if new_findings:
            self._storage.add_chapter_qa_findings(chapter_id, new_findings)
        current_findings = self._storage.list_chapter_qa_findings(chapter_id)

        # Targeted re-run (mode 2, explicit paragraph_ids): once this batch of
        # manually-queued paragraphs has been checked by every requested
        # connection without error, clear their "queued for QA" flag. Whole-
        # chapter runs (mode 1, paragraph_ids is None) never touch this flag.
        if paragraph_ids is not None and not errors:
            self._storage.set_paragraphs_qa_queue([p["paragraphId"] for p in batch], False)

        return {
            "chapterId": chapter_id,
            "batchIndex": batch_index,
            "totalBatches": len(batches),
            "categories": sorted(active_categories),
            "counts": self._count_findings(current_findings),
            "paragraphResults": self._group_findings_by_paragraph(current_findings),
            "errors": errors,
        }

    def list_chapter_qa_findings(self, chapter_id: str) -> dict[str, Any]:
        current_findings = self._storage.list_chapter_qa_findings(chapter_id)
        return {
            "chapterId": chapter_id,
            "counts": self._count_findings(current_findings),
            "paragraphResults": self._group_findings_by_paragraph(current_findings),
        }

    def resolve_chapter_qa_finding(self, finding_id: str) -> None:
        if not self._storage.delete_chapter_qa_finding(finding_id):
            raise QaServiceError("Finding not found.", 404, "not_found")

    @staticmethod
    def _count_findings(findings: list[dict[str, Any]]) -> dict[str, int]:
        counts = {"critical": 0, "stylistic": 0, "typo": 0}
        for finding in findings:
            if finding["category"] in counts:
                counts[finding["category"]] += 1
        return counts

    @staticmethod
    def _group_findings_by_paragraph(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for finding in findings:
            grouped.setdefault(finding["paragraphId"], []).append({
                "findingId": finding["findingId"],
                "category": finding["category"],
                "quote": finding["quote"],
                "explanation": finding.get("explanation") or "",
                "suggestion": finding.get("suggestion") or "",
                "sourceModel": finding["sourceModel"],
            })
        return [
            {"paragraphId": paragraph_id, "findings": findings}
            for paragraph_id, findings in grouped.items()
        ]

    _NARRATOR_GENDERS = ("masc", "femn", "third")
    _NARRATOR_LABELS = {"masc": "чоловік", "femn": "жінка", "third": "третя особа"}

    _CATEGORY_DESCRIPTIONS = {
        "critical": (
            "critical — значення слова/фрази, дія, роль персонажа, часова рамка або вид дієслова "
            "(одноразовість/повторюваність) у перекладі суттєво відрізняється від оригіналу, змінюючи те, "
            "що фактично стверджується. Приклад: гарчання перекладено як шепіт; \"примусив\" перекладено "
            "недоконаним видом \"примушував\" там, де йдеться про конкретний випадок, а не звичку. Сюди ж "
            "належить невідповідність роду/особи ОПОВІДАЧА в наративних реченнях (не в репліках персонажів "
            "у прямій мові) статі/особі, вказаній для абзацу в секції \"стать/особа оповідача\" нижче — "
            "наприклад, дієслово чи прикметник минулого часу в наративі узгоджено з чоловічим родом, хоча "
            "оповідач жінка. Це critical, бо це змінює те, що фактично стверджується про самого оповідача."
        ),
        "stylistic": (
            "stylistic — факт і дія збережені, але втрачено тон, конотацію чи звучання оригіналу. "
            "Це охоплює декілька різних втрат, перевіряй усі: (1) згладжування грубої/розмовної лексики "
            "оригіналу до нейтральної; (2) втрату фізичної конкретики дієслів — коли тілесна, конкретна дія "
            "оригіналу передана абстрактним чи загальним дієсловом (напр. \"grabbed\" → \"взяв\" замість "
            "\"схопив\", \"stormed out\" → \"вийшов\" замість \"вилетів\"); (3) втрату ідіоматичності — "
            "буквальний/калькований переклад ідіоми чи сталого виразу замість природного українського "
            "відповідника; (4) втрату голосу персонажа — мовлення звучить не так, як типово для цього "
            "персонажа (надто літературно, надто формально чи невідповідно його віку/статусу/характеру)."
        ),
        "typo": "typo — слова, яких не існує в українській мові (одруківки, неправильно утворені форми).",
    }

    @classmethod
    def _effective_narrators(cls, default_narrator: str | None, paragraphs: list[dict[str, Any]]) -> dict[str, str]:
        """Walks the chapter's paragraphs in order (as returned by
        get_chapter_paragraphs, i.e. ordered by paragraph_index) and resolves
        each paragraph's "effective" narrator gender/person: whatever the
        nearest preceding "narratorChange" marker set, carried forward, or
        the project default when no marker has appeared yet in the chapter."""
        current = default_narrator if default_narrator in cls._NARRATOR_GENDERS else "third"
        effective: dict[str, str] = {}
        for paragraph in paragraphs:
            change = paragraph.get("narratorChange")
            if change in cls._NARRATOR_GENDERS:
                current = change
            effective[paragraph["paragraphId"]] = current
        return effective

    @classmethod
    def _build_quality_prompt(
        cls,
        paragraphs: list[dict[str, Any]],
        speech_registers: dict[str, str],
        categories: set[str],
        narrators: dict[str, str],
    ) -> str:
        pairs = "\n\n".join(
            f'[{paragraph["paragraphId"]}]\nОригінал: {paragraph["originalText"]}\nПереклад: {paragraph["translationText"]}'
            for paragraph in paragraphs
        )
        registers = "\n".join(f"- {name}: {note}" for name, note in speech_registers.items()) or "Немає."
        narrator_lines = "\n".join(
            f'[{paragraph["paragraphId"]}]: оповідач — '
            f'{cls._NARRATOR_LABELS.get(narrators.get(paragraph["paragraphId"], "third"), "третя особа")}'
            for paragraph in paragraphs
        )
        ordered_categories = [item for item in ("critical", "stylistic", "typo") if item in categories]
        descriptions = "\n\n".join(cls._CATEGORY_DESCRIPTIONS[item] for item in ordered_categories)
        category_enum = "|".join(f'"{item}"' for item in ordered_categories)
        return (
            "=== СТАТЬ/ОСОБА ОПОВІДАЧА ===\n"
            "Стать/особа оповідача в наративних реченнях (НЕ мовлення персонажів у репліках) для кожного "
            f"абзацу нижче:\n{narrator_lines}\n"
            "=== КІНЕЦЬ СТАТІ/ОСОБИ ОПОВІДАЧА ===\n\n"
            "Ти перевіряєш якість перекладу художньої прози з англійської на українську. "
            "Порівняй кожен абзац оригіналу з перекладом і знайди ТІЛЬКИ реальні проблеми "
            f"{'цього типу' if len(ordered_categories) == 1 else 'цих типів'}:\n\n"
            f"{descriptions}\n\n"
            "НЕ позначай: переформулювання, якщо сенс і тон збережені; ідіоматичні/жаргонні відповідники, "
            "дібрані функціонально, а не буквально; вибір слова, що узгоджується з гліосарієм проєкту, "
            "навіть якщо це відрізняється від буквального перекладу.\n\n"
            f"Мовний регістр персонажів (використовуй, щоб оцінити, чи згладжування грубості виправдане):\n{registers}\n\n"
            "Спочатку зроби чернетку-аналіз (це робочі нотатки, вони не потраплять у фінальну відповідь): "
            "пройдися по кожному абзацу речення за реченням і для кожного речення оригіналу коротко "
            "зафіксуй, чи є проблема одного з перелічених типів, чи ні. Перевіряй так навіть речення, "
            "що на перший погляд виглядають гладко й без проблем — не обмежуйся лише очевидними "
            "випадками, бо саме неочевидні найлегше пропустити.\n\n"
            "Після чернетки постав на окремому рядку маркер ===JSON=== і виведи після нього ЛИШЕ "
            "фінальний JSON-масив об'єктів без жодного іншого тексту (без пояснень, без markdown-огорожі) "
            "— усе, що стоїть після цього маркера, буде розпарсено як JSON. "
            "Кожен об'єкт має поля: paragraphId (рядок, точно як у квадратних дужках нижче), "
            f"category ({category_enum}), quote (коротка цитата з перекладу, що містить "
            "проблему), explanation (коротке пояснення українською, без спойлерів сюжету — лише про "
            "граматику/стиль/значення), suggestion (варіант виправлення або порожній рядок). "
            "Якщо проблем немає — поверни порожній масив [].\n\n"
            "Кожне значення полів (quote, explanation, suggestion) має бути одним рядком, "
            "без символів нового рядка всередині значення.\n\n"
            f"Абзаци для перевірки:\n{pairs}"
        )

    @staticmethod
    def _repair_json_newlines(text: str) -> str:
        """Best-effort fix for a common non-strict-JSON-mode LLM mistake:
        a literal raw newline/tab inside a string value, which is invalid
        per the JSON spec and makes json.loads fail (often surfacing as
        \"Unterminated string...\"). Walks the text tracking whether we're
        inside a string (respecting backslash escapes) and escapes any raw
        control character found there."""
        result = []
        in_string = False
        escaped = False
        for char in text:
            if in_string:
                if escaped:
                    result.append(char)
                    escaped = False
                elif char == "\\":
                    result.append(char)
                    escaped = True
                elif char == '"':
                    in_string = False
                    result.append(char)
                elif char == "\n":
                    result.append("\\n")
                elif char == "\r":
                    result.append("\\r")
                elif char == "\t":
                    result.append("\\t")
                else:
                    result.append(char)
            else:
                if char == '"':
                    in_string = True
                result.append(char)
        return "".join(result)

    @classmethod
    def _parse_quality_response(cls, raw_text: str, categories: set[str]) -> list[dict[str, Any]]:
        text = raw_text.strip()
        marker = "===JSON==="
        marker_index = text.rfind(marker)
        if marker_index != -1:
            text = text[marker_index + len(marker):].strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
            text = text.strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            try:
                data = json.loads(cls._repair_json_newlines(text))
            except json.JSONDecodeError as error:
                raise QaServiceError(f"AI QA response was not valid JSON: {error}") from error
        if not isinstance(data, list):
            raise QaServiceError("AI QA response must be a JSON array.")
        cleaned = []
        for item in data:
            if not isinstance(item, dict):
                continue
            if item.get("category") not in categories:
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
        return provider, credentials
