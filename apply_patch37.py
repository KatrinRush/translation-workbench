"""
Patch 37: fix HTTP 524 (Cloudflare edge timeout) on chapters with many
paragraphs. check_chapter_translation_quality used to process every batch
of the chapter inside a single HTTP request/response cycle — fine for a
small chapter, but a 152-paragraph chapter (13 batches) could easily run
past Cloudflare Tunnel's edge timeout before the backend ever got to send
a response back.

Fix: the endpoint now processes exactly ONE batch per call (selected by a
new batchIndex parameter) and reports totalBatches in its response. The
frontend drives the loop itself, firing one short-lived request per batch
and rendering progressively as each one completes — so no single HTTP
round-trip does more than one batch's worth of LLM calls. If a request
fails partway through (network blip, one bad batch), the frontend
remembers which batch it was on per chapter, so clicking "AI QA" again
resumes from there instead of re-running (and re-billing) batches already
completed.

Depends on patches 25-36 already being applied.

Run from the repo root (same folder as backend/ and frontend/):
    python apply_patch37.py
"""
from pathlib import Path

QA_SERVICE_PATH = Path("backend/qa/service.py")
SERVER_PATH = Path("backend/server.py")
API_JS_PATH = Path("frontend/api.js")
APP_JS_PATH = Path("frontend/app.js")


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
    # === backend/qa/service.py ===

    apply(
        QA_SERVICE_PATH,
        '''    def check_chapter_translation_quality(self, project_id: str, chapter_id: str, connection_ids: list[str]) -> dict[str, Any]:
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
        batches = [
            translatable[i:i + self._QUALITY_BATCH_SIZE]
            for i in range(0, len(translatable), self._QUALITY_BATCH_SIZE)
        ]

        speech_registers = self._storage.get_project_character_registers(project_id)

        connections = {item["connectionId"]: item for item in self._storage.list_integration_connections()}
        new_findings: list[dict[str, Any]] = []
        error_messages: dict[str, list[str]] = {}

        for connection_id in dict.fromkeys(connection_ids):
            connection = connections.get(connection_id)
            if connection is None or not connection["enabled"] or connection["testStatus"] != "connected":
                error_messages[connection_id] = ["AI connection is not active and tested."]
                continue
            provider_id = connection["providerId"]
            if provider_id == "deepl":
                error_messages[connection_id] = ["This connection cannot run AI QA."]
                continue
            try:
                provider, credentials = self._provider_credentials(connection)
            except QaServiceError as error:
                error_messages[connection_id] = [str(error)]
                continue
            for batch in batches:
                prompt = self._build_quality_prompt(batch, speech_registers)
                parsed = None
                last_error: Exception | None = None
                for _attempt in range(self._QUALITY_BATCH_ATTEMPTS):
                    try:
                        raw_text = provider.analyze(credentials, prompt)
                        parsed = self._parse_quality_response(raw_text)
                        break
                    except (ValueError, QaServiceError) as error:
                        last_error = error
                if parsed is None:
                    error_messages.setdefault(connection_id, []).append(str(last_error))
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

        errors = {
            connection_id: f"{len(messages)} з {len(batches)} частин розділу не вдалося перевірити: {messages[0]}"
            for connection_id, messages in error_messages.items()
        }

        return {
            "chapterId": chapter_id,
            "counts": self._count_findings(current_findings),
            "paragraphResults": self._group_findings_by_paragraph(current_findings),
            "errors": errors,
        }''',
        '''    def check_chapter_translation_quality(self, project_id: str, chapter_id: str, connection_ids: list[str], batch_index: int = 0) -> dict[str, Any]:
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
            prompt = self._build_quality_prompt(batch, speech_registers)
            parsed = None
            last_error: Exception | None = None
            for _attempt in range(self._QUALITY_BATCH_ATTEMPTS):
                try:
                    raw_text = provider.analyze(credentials, prompt)
                    parsed = self._parse_quality_response(raw_text)
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

        return {
            "chapterId": chapter_id,
            "batchIndex": batch_index,
            "totalBatches": len(batches),
            "counts": self._count_findings(current_findings),
            "paragraphResults": self._group_findings_by_paragraph(current_findings),
            "errors": errors,
        }''',
    )

    # === backend/server.py ===

    apply(
        SERVER_PATH,
        '''            data = self.read_json()
            connection_ids = data.get("connectionIds", [])
            return 200, qa_service.check_chapter_translation_quality(parts[2], parts[4], connection_ids)''',
        '''            data = self.read_json()
            connection_ids = data.get("connectionIds", [])
            batch_index = data.get("batchIndex", 0)
            return 200, qa_service.check_chapter_translation_quality(parts[2], parts[4], connection_ids, batch_index)''',
    )

    # === frontend/api.js ===

    apply(
        API_JS_PATH,
        '''    checkChapterTranslationQuality(projectId, chapterId, connectionIds) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/chapters/${encodeURIComponent(chapterId)}/qa-check`, {
            method: 'POST',
            body: JSON.stringify({ connectionIds })
        });
    },''',
        '''    checkChapterTranslationQuality(projectId, chapterId, connectionIds, batchIndex = 0) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/chapters/${encodeURIComponent(chapterId)}/qa-check`, {
            method: 'POST',
            body: JSON.stringify({ connectionIds, batchIndex })
        });
    },''',
    )

    # === frontend/app.js ===

    # Per-chapter resume position, next to the other AI QA module state
    apply(
        APP_JS_PATH,
        '''let aiQaFlatFindings = [];
let aiQaFilterCategory = null;
let aiQaFilterIndex = 0;''',
        '''let aiQaFlatFindings = [];
let aiQaFilterCategory = null;
let aiQaFilterIndex = 0;
const aiQaResumeBatchIndex = new Map();''',
    )

    apply(
        APP_JS_PATH,
        '''async function checkCurrentChapterAiQa() {
    const chapter = loadedChapters[selectedChapterIndex];
    if (!chapter?.chapterId || !currentProject?.projectId) {
        return;
    }
    const connectionIds = [...aiQaConnections.querySelectorAll('input:checked')].map((checkbox) => checkbox.value);
    if (connectionIds.length === 0) {
        aiQaStatus.textContent = 'Оберіть хоча б одну QA-модель.';
        return;
    }
    const previousText = checkAiQaButton.textContent;
    checkAiQaButton.disabled = true;
    checkAiQaButton.textContent = 'Перевіряємо…';
    aiQaStatus.textContent = '';
    try {
        const result = await WorkbenchApi.checkChapterTranslationQuality(currentProject.projectId, chapter.chapterId, connectionIds);
        renderAiQaResults(result);
    } catch (error) {
        aiQaStatus.textContent = `Помилка перевірки: ${error.message}`;
    } finally {
        checkAiQaButton.disabled = false;
        checkAiQaButton.textContent = previousText;
    }
}''',
        '''async function checkCurrentChapterAiQa() {
    const chapter = loadedChapters[selectedChapterIndex];
    if (!chapter?.chapterId || !currentProject?.projectId) {
        return;
    }
    const connectionIds = [...aiQaConnections.querySelectorAll('input:checked')].map((checkbox) => checkbox.value);
    if (connectionIds.length === 0) {
        aiQaStatus.textContent = 'Оберіть хоча б одну QA-модель.';
        return;
    }
    const previousText = checkAiQaButton.textContent;
    checkAiQaButton.disabled = true;
    aiQaStatus.textContent = '';
    let batchIndex = aiQaResumeBatchIndex.get(chapter.chapterId) || 0;
    try {
        let totalBatches = batchIndex + 1;
        while (batchIndex < totalBatches) {
            checkAiQaButton.textContent = totalBatches > 1 ? `Перевіряємо (${batchIndex + 1} з ${totalBatches})…` : 'Перевіряємо…';
            const result = await WorkbenchApi.checkChapterTranslationQuality(currentProject.projectId, chapter.chapterId, connectionIds, batchIndex);
            renderAiQaResults(result);
            totalBatches = result.totalBatches;
            batchIndex += 1;
            aiQaResumeBatchIndex.set(chapter.chapterId, batchIndex);
        }
        aiQaResumeBatchIndex.delete(chapter.chapterId);
    } catch (error) {
        aiQaStatus.textContent = `Помилка перевірки (частина ${batchIndex + 1}): ${error.message}. Натисни ще раз, щоб продовжити з цього місця.`;
    } finally {
        checkAiQaButton.disabled = false;
        checkAiQaButton.textContent = previousText;
    }
}''',
    )

    # Manual "Скинути AI QA" and chapter switch should also drop resume progress
    apply(
        APP_JS_PATH,
        '''function clearAiQaIssues() {
    exitAiQaFilter();
    translationRows.querySelectorAll('.ai-qa-issues').forEach((panel) => panel.remove());
    aiQaCounters.replaceChildren();
    aiQaFlatFindings = [];
}''',
        '''function clearAiQaIssues() {
    exitAiQaFilter();
    translationRows.querySelectorAll('.ai-qa-issues').forEach((panel) => panel.remove());
    aiQaCounters.replaceChildren();
    aiQaFlatFindings = [];
    const chapter = loadedChapters[selectedChapterIndex];
    if (chapter?.chapterId) {
        aiQaResumeBatchIndex.delete(chapter.chapterId);
    }
}''',
    )

    print("Patch 37 applied successfully.")


if __name__ == "__main__":
    main()
