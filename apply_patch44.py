"""Patch 44 — backend foundation for the QA AI redesign (qa.py part).

Supersedes/completes patch 43: patch 43 already applied the storage.py
changes successfully (do NOT re-run patch_storage — the old_str patterns
it looks for no longer exist post-patch, it would just fail loudly and
harmlessly, but there is no need to run it again). This patch only fixes
the path for QaService, which lives at backend/qa/service.py (a package),
not backend/qa.py.

Run from the repo root: python apply_patch41.py

What this does:
1. storage.py
   - new `queued_for_qa` column on book_paragraphs (+ migration)
   - `update_paragraph` learns an optional `queued_for_qa` param (same
     "only touch if explicitly provided" pattern as `is_service`)
   - `queuedForQa` added to every paragraph serialization path
   - new `set_paragraphs_qa_queue()` bulk helper (used to auto-clear the
     flag after a successful targeted re-run)
2. qa.py
   - default QUALITY batch size lowered from 12 to 5, and made overridable
     per call (`batch_size` param)
   - `check_chapter_translation_quality` accepts an optional `paragraph_ids`
     list: when given, QA runs only over that explicit subset instead of
     the whole chapter (still batched the same way, so the existing
     batch-loop logic on the frontend can be reused unchanged)
   - `categories` param lets a caller scope a run to just critical /
     stylistic / typo instead of always bundling all three
   - after a successful (error-free) `paragraph_ids`-scoped batch, the
     paragraphs' `queued_for_qa` flag is cleared automatically; whole-
     chapter runs (paragraph_ids=None) never touch this flag
3. server.py
   - `qa-check` endpoint forwards `paragraphIds` / `categories` / `batchSize`
     from the request body
   - `PATCH/PUT /api/paragraphs/{id}` forwards an optional `queuedForQa`

This is backend-only. The QA AI tab / inline "queued for QA" checkbox UI
are separate follow-up patches.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"Expected exactly 1 match in {path} for a replacement, found {count}.\n"
            f"--- old_str ---\n{old}\n--- end ---"
        )
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_storage() -> None:
    path = REPO_ROOT / "backend" / "storage.py"

    # 1. Schema: new column
    replace_once(
        path,
        '''CREATE TABLE IF NOT EXISTS book_paragraphs (
    paragraph_id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL REFERENCES book_chapters(chapter_id) ON DELETE CASCADE,
    paragraph_index INTEGER NOT NULL,
    original_text TEXT NOT NULL,
    word_count INTEGER NOT NULL DEFAULT 0,
    translation_text TEXT,
    reviewed INTEGER NOT NULL DEFAULT 0,
    is_service INTEGER NOT NULL DEFAULT 0,
    UNIQUE(chapter_id, paragraph_index)
);''',
        '''CREATE TABLE IF NOT EXISTS book_paragraphs (
    paragraph_id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL REFERENCES book_chapters(chapter_id) ON DELETE CASCADE,
    paragraph_index INTEGER NOT NULL,
    original_text TEXT NOT NULL,
    word_count INTEGER NOT NULL DEFAULT 0,
    translation_text TEXT,
    reviewed INTEGER NOT NULL DEFAULT 0,
    is_service INTEGER NOT NULL DEFAULT 0,
    queued_for_qa INTEGER NOT NULL DEFAULT 0,
    UNIQUE(chapter_id, paragraph_index)
);''',
    )

    # 2. Migration
    replace_once(
        path,
        '''            if "is_service" not in paragraph_columns:
                connection.execute("ALTER TABLE book_paragraphs ADD COLUMN is_service INTEGER NOT NULL DEFAULT 0")''',
        '''            if "is_service" not in paragraph_columns:
                connection.execute("ALTER TABLE book_paragraphs ADD COLUMN is_service INTEGER NOT NULL DEFAULT 0")
            if "queued_for_qa" not in paragraph_columns:
                connection.execute("ALTER TABLE book_paragraphs ADD COLUMN queued_for_qa INTEGER NOT NULL DEFAULT 0")''',
    )

    # 3. get_book_structure: paragraph element serialization
    replace_once(
        path,
        '''                        row = connection.execute("SELECT paragraph_id, original_text, translation_text, reviewed, is_service FROM book_paragraphs WHERE paragraph_id = ?", (element["element_id"],)).fetchone()''',
        '''                        row = connection.execute("SELECT paragraph_id, original_text, translation_text, reviewed, is_service, queued_for_qa FROM book_paragraphs WHERE paragraph_id = ?", (element["element_id"],)).fetchone()''',
    )
    replace_once(
        path,
        '''                            elements.append({"type": "paragraph", "paragraphId": row["paragraph_id"], "originalText": row["original_text"], "translationText": row["translation_text"], "reviewed": bool(row["reviewed"]), "isService": bool(row["is_service"]), "footnotes": footnotes})''',
        '''                            elements.append({"type": "paragraph", "paragraphId": row["paragraph_id"], "originalText": row["original_text"], "translationText": row["translation_text"], "reviewed": bool(row["reviewed"]), "isService": bool(row["is_service"]), "queuedForQa": bool(row["queued_for_qa"]), "footnotes": footnotes})''',
    )

    # 4. update_paragraph: add queued_for_qa param, build SET clause dynamically
    replace_once(
        path,
        '''    def update_paragraph(self, paragraph_id: str, translation_text: str | None, reviewed: bool, is_service: bool | None = None) -> dict[str, Any] | None:
        with self.connection() as connection:
            if is_service is None:
                cursor = connection.execute("UPDATE book_paragraphs SET translation_text = ?, reviewed = ? WHERE paragraph_id = ?", (translation_text, int(reviewed), paragraph_id))
            else:
                cursor = connection.execute("UPDATE book_paragraphs SET translation_text = ?, reviewed = ?, is_service = ? WHERE paragraph_id = ?", (translation_text, int(reviewed), int(is_service), paragraph_id))
            if cursor.rowcount == 0:
                return None''',
        '''    def update_paragraph(self, paragraph_id: str, translation_text: str | None, reviewed: bool, is_service: bool | None = None, queued_for_qa: bool | None = None) -> dict[str, Any] | None:
        with self.connection() as connection:
            set_clauses = ["translation_text = ?", "reviewed = ?"]
            params: list[Any] = [translation_text, int(reviewed)]
            if is_service is not None:
                set_clauses.append("is_service = ?")
                params.append(int(is_service))
            if queued_for_qa is not None:
                set_clauses.append("queued_for_qa = ?")
                params.append(int(queued_for_qa))
            params.append(paragraph_id)
            cursor = connection.execute(
                f"UPDATE book_paragraphs SET {', '.join(set_clauses)} WHERE paragraph_id = ?",
                params,
            )
            if cursor.rowcount == 0:
                return None''',
    )

    # 5a. update_paragraph's return dict (also disambiguates it from get_paragraph's
    # identical return line below, so this must run before 5b)
    replace_once(
        path,
        '''        return {"paragraphId": row["paragraph_id"], "originalText": row["original_text"], "translationText": row["translation_text"], "reviewed": bool(row["reviewed"]), "isService": bool(row["is_service"])}

    def get_paragraph(self, paragraph_id: str) -> dict[str, Any] | None:''',
        '''        return {"paragraphId": row["paragraph_id"], "originalText": row["original_text"], "translationText": row["translation_text"], "reviewed": bool(row["reviewed"]), "isService": bool(row["is_service"]), "queuedForQa": bool(row["queued_for_qa"])}

    def get_paragraph(self, paragraph_id: str) -> dict[str, Any] | None:''',
    )

    # 5b. get_paragraph's return dict (now the only remaining match)
    replace_once(
        path,
        '''        return {"paragraphId": row["paragraph_id"], "originalText": row["original_text"], "translationText": row["translation_text"], "reviewed": bool(row["reviewed"]), "isService": bool(row["is_service"])}''',
        '''        return {"paragraphId": row["paragraph_id"], "originalText": row["original_text"], "translationText": row["translation_text"], "reviewed": bool(row["reviewed"]), "isService": bool(row["is_service"]), "queuedForQa": bool(row["queued_for_qa"])}''',
    )

    # 6. get_chapter_paragraphs (used by QaService) + new bulk helper right after it
    replace_once(
        path,
        '''    def get_chapter_paragraphs(self, chapter_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT paragraph_id, paragraph_index, original_text, translation_text, reviewed, is_service "
                "FROM book_paragraphs WHERE chapter_id = ? ORDER BY paragraph_index",
                (chapter_id,),
            ).fetchall()
        return [
            {
                "paragraphId": row["paragraph_id"],
                "paragraphIndex": row["paragraph_index"],
                "originalText": row["original_text"],
                "translationText": row["translation_text"],
                "reviewed": _bool(row["reviewed"]),
                "isService": _bool(row["is_service"]),
            }
            for row in rows
        ]''',
        '''    def get_chapter_paragraphs(self, chapter_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT paragraph_id, paragraph_index, original_text, translation_text, reviewed, is_service, queued_for_qa "
                "FROM book_paragraphs WHERE chapter_id = ? ORDER BY paragraph_index",
                (chapter_id,),
            ).fetchall()
        return [
            {
                "paragraphId": row["paragraph_id"],
                "paragraphIndex": row["paragraph_index"],
                "originalText": row["original_text"],
                "translationText": row["translation_text"],
                "reviewed": _bool(row["reviewed"]),
                "isService": _bool(row["is_service"]),
                "queuedForQa": _bool(row["queued_for_qa"]),
            }
            for row in rows
        ]

    def set_paragraphs_qa_queue(self, paragraph_ids: list[str], queued: bool) -> None:
        """Bulk-set the 'queued for QA' flag. Used to auto-clear it on the
        paragraphs covered by a successful targeted QA re-run (mode 2 in the
        QA AI tab); whole-chapter QA runs never call this."""
        if not paragraph_ids:
            return
        with self.connection() as connection:
            connection.executemany(
                "UPDATE book_paragraphs SET queued_for_qa = ? WHERE paragraph_id = ?",
                [(int(queued), paragraph_id) for paragraph_id in paragraph_ids],
            )''',
    )

    print(f"storage.py patched: {path}")


def patch_qa() -> None:
    path = REPO_ROOT / "backend" / "qa" / "service.py"

    # Batch size + signature: accept paragraph_ids / categories / batch_size
    replace_once(
        path,
        '''    _QUALITY_CATEGORIES = {"critical", "stylistic", "typo"}
    _QUALITY_BATCH_SIZE = 12

    _QUALITY_BATCH_ATTEMPTS = 2

    def check_chapter_translation_quality(self, project_id: str, chapter_id: str, connection_ids: list[str], batch_index: int = 0) -> dict[str, Any]:
        project = self._storage.get_project(project_id)
        if project is None:
            raise QaServiceError("Project not found.", 404, "not_found")
        if not isinstance(connection_ids, list) or not connection_ids or not all(isinstance(item, str) and item.strip() for item in connection_ids):
            raise QaServiceError("Choose at least one AI connection.", 400, "qa_invalid")
        if not isinstance(batch_index, int) or batch_index < 0:
            raise QaServiceError("Invalid batch index.", 400, "qa_invalid")

        paragraphs = self._storage.get_chapter_paragraphs(chapter_id)
        translatable = [p for p in paragraphs if not p["isService"] and p.get("translationText")]
        if not translatable:
            raise QaServiceError("Chapter has no translated paragraphs to check.", 400, "qa_empty")
        paragraph_by_id = {p["paragraphId"]: p for p in translatable}
        batches = [
            translatable[i:i + self._QUALITY_BATCH_SIZE]
            for i in range(0, len(translatable), self._QUALITY_BATCH_SIZE)
        ]
        if batch_index >= len(batches):
            raise QaServiceError("Batch index out of range.", 400, "qa_invalid")
        batch = batches[batch_index]

        speech_registers = self._storage.get_project_character_registers(project_id)''',
        '''    _QUALITY_CATEGORIES = {"critical", "stylistic", "typo"}
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

        speech_registers = self._storage.get_project_character_registers(project_id)''',
    )

    # Pass active_categories through to prompt building + response parsing
    replace_once(
        path,
        '''            prompt = self._build_quality_prompt(batch, speech_registers)
            parsed = None
            last_error: Exception | None = None
            for _attempt in range(self._QUALITY_BATCH_ATTEMPTS):
                try:
                    raw_text = provider.analyze(credentials, prompt)
                    parsed = self._parse_quality_response(raw_text)
                    break''',
        '''            prompt = self._build_quality_prompt(batch, speech_registers, active_categories)
            parsed = None
            last_error: Exception | None = None
            for _attempt in range(self._QUALITY_BATCH_ATTEMPTS):
                try:
                    raw_text = provider.analyze(credentials, prompt)
                    parsed = self._parse_quality_response(raw_text, active_categories)
                    break''',
    )

    # Auto-clear queued_for_qa after a successful targeted (mode 2) batch,
    # and report which categories this run actually covered
    replace_once(
        path,
        '''        if new_findings:
            self._storage.add_chapter_qa_findings(chapter_id, new_findings)
        current_findings = self._storage.list_chapter_qa_findings(chapter_id)

        return {
            "chapterId": chapter_id,
            "batchIndex": batch_index,
            "totalBatches": len(batches),
            "counts": self._count_findings(current_findings),
            "paragraphResults": self._group_findings_by_paragraph(current_findings),
            "errors": errors,
        }''',
        '''        if new_findings:
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
        }''',
    )

    # Prompt builder: parametrize by requested categories instead of always
    # bundling all three
    replace_once(
        path,
        '''    @staticmethod
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
            "Кожне значення полів (quote, explanation, suggestion) має бути одним рядком, "
            "без символів нового рядка всередині значення.\\n\\n"
            f"Абзаци для перевірки:\\n{pairs}"
        )''',
        '''    _CATEGORY_DESCRIPTIONS = {
        "critical": (
            "critical — значення слова/фрази, дія, роль персонажа, часова рамка або вид дієслова "
            "(одноразовість/повторюваність) у перекладі суттєво відрізняється від оригіналу, змінюючи те, "
            "що фактично стверджується. Приклад: гарчання перекладено як шепіт; \\"примусив\\" перекладено "
            "недоконаним видом \\"примушував\\" там, де йдеться про конкретний випадок, а не звичку."
        ),
        "stylistic": (
            "stylistic — факт і дія збережені, але втрачено тон, конотацію, грубість мовлення чи градацію. "
            "Пріоритетно позначай випадки, де груба/розмовна лексика оригіналу згладжена до нейтральної."
        ),
        "typo": "typo — слова, яких не існує в українській мові (одруківки, неправильно утворені форми).",
    }

    @classmethod
    def _build_quality_prompt(cls, paragraphs: list[dict[str, Any]], speech_registers: dict[str, str], categories: set[str]) -> str:
        pairs = "\\n\\n".join(
            f'[{paragraph["paragraphId"]}]\\nОригінал: {paragraph["originalText"]}\\nПереклад: {paragraph["translationText"]}'
            for paragraph in paragraphs
        )
        registers = "\\n".join(f"- {name}: {note}" for name, note in speech_registers.items()) or "Немає."
        ordered_categories = [item for item in ("critical", "stylistic", "typo") if item in categories]
        descriptions = "\\n\\n".join(cls._CATEGORY_DESCRIPTIONS[item] for item in ordered_categories)
        category_enum = "|".join(f'"{item}"' for item in ordered_categories)
        return (
            "Ти перевіряєш якість перекладу художньої прози з англійської на українську. "
            "Порівняй кожен абзац оригіналу з перекладом і знайди ТІЛЬКИ реальні проблеми "
            f"{'цього типу' if len(ordered_categories) == 1 else 'цих типів'}:\\n\\n"
            f"{descriptions}\\n\\n"
            "НЕ позначай: переформулювання, якщо сенс і тон збережені; ідіоматичні/жаргонні відповідники, "
            "дібрані функціонально, а не буквально; вибір слова, що узгоджується з гліосарієм проєкту, "
            "навіть якщо це відрізняється від буквального перекладу.\\n\\n"
            f"Мовний регістр персонажів (використовуй, щоб оцінити, чи згладжування грубості виправдане):\\n{registers}\\n\\n"
            "Поверни ЛИШЕ JSON-масив об'єктів без жодного іншого тексту (без пояснень, без markdown-огорожі). "
            "Кожен об'єкт має поля: paragraphId (рядок, точно як у квадратних дужках нижче), "
            f"category ({category_enum}), quote (коротка цитата з перекладу, що містить "
            "проблему), explanation (коротке пояснення українською, без спойлерів сюжету — лише про "
            "граматику/стиль/значення), suggestion (варіант виправлення або порожній рядок). "
            "Якщо проблем немає — поверни порожній масив [].\\n\\n"
            "Кожне значення полів (quote, explanation, suggestion) має бути одним рядком, "
            "без символів нового рядка всередині значення.\\n\\n"
            f"Абзаци для перевірки:\\n{pairs}"
        )''',
    )

    # Response parser: validate against the requested categories, not the
    # always-all-three constant
    replace_once(
        path,
        '''    @classmethod
    def _parse_quality_response(cls, raw_text: str) -> list[dict[str, Any]]:''',
        '''    @classmethod
    def _parse_quality_response(cls, raw_text: str, categories: set[str]) -> list[dict[str, Any]]:''',
    )
    replace_once(
        path,
        '''            if item.get("category") not in cls._QUALITY_CATEGORIES:
                continue
            if not item.get("paragraphId"):
                continue
            cleaned.append(item)
        return cleaned''',
        '''            if item.get("category") not in categories:
                continue
            if not item.get("paragraphId"):
                continue
            cleaned.append(item)
        return cleaned''',
    )

    print(f"qa.py patched: {path}")


def patch_server() -> None:
    path = REPO_ROOT / "backend" / "server.py"

    replace_once(
        path,
        '''            data = self.read_json()
            connection_ids = data.get("connectionIds", [])
            batch_index = data.get("batchIndex", 0)
            return 200, qa_service.check_chapter_translation_quality(parts[2], parts[4], connection_ids, batch_index)''',
        '''            data = self.read_json()
            connection_ids = data.get("connectionIds", [])
            batch_index = data.get("batchIndex", 0)
            return 200, qa_service.check_chapter_translation_quality(
                parts[2],
                parts[4],
                connection_ids,
                batch_index,
                paragraph_ids=data.get("paragraphIds"),
                categories=data.get("categories"),
                batch_size=data.get("batchSize"),
            )''',
    )

    replace_once(
        path,
        '''        if len(parts) == 3 and parts[:2] == ["api", "paragraphs"] and method in {"PUT", "PATCH"}:
            data = self.read_json()
            paragraph = storage.update_paragraph(
                parts[2],
                data.get("translationText"),
                bool(data.get("reviewed", False)),
                bool(data["isService"]) if "isService" in data else None,
            )
            return (200, paragraph) if paragraph else (404, {"error": "Paragraph not found."})''',
        '''        if len(parts) == 3 and parts[:2] == ["api", "paragraphs"] and method in {"PUT", "PATCH"}:
            data = self.read_json()
            paragraph = storage.update_paragraph(
                parts[2],
                data.get("translationText"),
                bool(data.get("reviewed", False)),
                bool(data["isService"]) if "isService" in data else None,
                bool(data["queuedForQa"]) if "queuedForQa" in data else None,
            )
            return (200, paragraph) if paragraph else (404, {"error": "Paragraph not found."})''',
    )

    print(f"server.py patched: {path}")


if __name__ == "__main__":
    patch_qa()
    patch_server()
    print("Patch 44 applied.")
