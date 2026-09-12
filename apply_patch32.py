"""
Patch 32: two independent fixes reported after testing patch 29-31.

1. FRONTEND UX (Катя's feedback: model choice for QA required a trip to
   project settings — "зайві рухи"): the QA connection picker now renders
   as inline checkboxes right under the "AI QA" button, exactly like the
   existing "Моделі для AI-аналізу" checkboxes already work for the
   pre-translation brief tool. Still reads its eligible-connections pool
   from the same project.aiConfiguration.qaConnectionIds set in Settings
   (that one-time setup step stays, same as for AI-analysis) — only the
   per-run picker moves next to the button. The old "Запустити з усіма
   QA-моделями" text link is removed; running with 2 models now just means
   checking 2 boxes.

2. BACKEND ROBUSTNESS ("AI QA response was not valid JSON: Unterminated
   string..." — Gemini's response got cut off mid-array on an 82-paragraph
   chapter): check_chapter_translation_quality now sends paragraphs in
   batches (12 at a time) instead of the whole chapter in one call, so no
   single response has to hold findings for dozens of paragraphs at once.
   _parse_quality_response also gets a best-effort repair pass (escaping
   stray raw newlines inside string values, a common non-strict-JSON-mode
   LLM mistake) before giving up and raising. Per-connection errors are now
   collected as a list across batches instead of being overwritten by the
   last batch's error.

Depends on patches 25-31 already being applied.

Run from the repo root (same folder as backend/ and frontend/):
    python apply_patch32.py
"""
from pathlib import Path

APP_JS_PATH = Path("frontend/app.js")
QA_SERVICE_PATH = Path("backend/qa/service.py")


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
    # === FRONTEND ===

    # 1. Replace the button-pair DOM setup with a checkbox container + single button
    apply(
        APP_JS_PATH,
        '''const checkAiQaButton = document.createElement('button');
checkAiQaButton.type = 'button';
checkAiQaButton.className = 'secondary-btn';
checkAiQaButton.id = 'check-ai-qa-button';
checkAiQaButton.textContent = 'AI QA (сенс/стиль)';
genderAgreementStatus.insertAdjacentElement('afterend', checkAiQaButton);
checkAiQaButton.addEventListener('click', () => checkCurrentChapterAiQa(false));

const checkAiQaDualButton = document.createElement('button');
checkAiQaDualButton.type = 'button';
checkAiQaDualButton.className = 'text-btn';
checkAiQaDualButton.id = 'check-ai-qa-dual-button';
checkAiQaDualButton.textContent = 'Запустити з усіма QA-моделями';
checkAiQaButton.insertAdjacentElement('afterend', checkAiQaDualButton);
checkAiQaDualButton.addEventListener('click', () => checkCurrentChapterAiQa(true));

const aiQaStatus = document.createElement('span');
aiQaStatus.className = 'ai-qa-status';
aiQaStatus.id = 'ai-qa-status';
checkAiQaDualButton.insertAdjacentElement('afterend', aiQaStatus);''',
        '''const aiQaConnections = document.createElement('div');
aiQaConnections.className = 'ai-qa-connections';
aiQaConnections.id = 'ai-qa-connections';
genderAgreementStatus.insertAdjacentElement('afterend', aiQaConnections);

const checkAiQaButton = document.createElement('button');
checkAiQaButton.type = 'button';
checkAiQaButton.className = 'secondary-btn';
checkAiQaButton.id = 'check-ai-qa-button';
checkAiQaButton.textContent = 'AI QA (сенс/стиль)';
aiQaConnections.insertAdjacentElement('afterend', checkAiQaButton);
checkAiQaButton.addEventListener('click', () => checkCurrentChapterAiQa());

const aiQaStatus = document.createElement('span');
aiQaStatus.className = 'ai-qa-status';
aiQaStatus.id = 'ai-qa-status';
checkAiQaButton.insertAdjacentElement('afterend', aiQaStatus);''',
    )

    # 2. Render the checkboxes off the same connections fetch the AI-analysis
    #    checkboxes already use, so no extra network round-trip
    apply(
        APP_JS_PATH,
        '''async function loadChapterAIAnalysisConnections() {
    if (!currentProject) return;
    try {
        integrationConnections = await WorkbenchApi.listConnections();
        renderChapterAIAnalysis(loadedChapters[selectedChapterIndex]);
    } catch (error) {
        chapterAIAnalysisStatus.textContent = error.message;
    }
}''',
        '''async function loadChapterAIAnalysisConnections() {
    if (!currentProject) return;
    try {
        integrationConnections = await WorkbenchApi.listConnections();
        renderChapterAIAnalysis(loadedChapters[selectedChapterIndex]);
        renderAiQaConnections();
    } catch (error) {
        chapterAIAnalysisStatus.textContent = error.message;
    }
}

function renderAiQaConnections() {
    aiQaConnections.replaceChildren();
    const configuredIds = new Set(
        (currentProject?.aiConfiguration?.qaConnectionIds || [])
            .filter((connectionId) => typeof connectionId === 'string' && connectionId),
    );
    const providerNames = { openai: 'GPT', gemini: 'Gemini', claude: 'Claude' };
    integrationConnections
        .filter((connection) => (
            configuredIds.has(connection.connectionId)
            && connection.enabled
            && connection.statusCode === 'ok'
            && Object.hasOwn(providerNames, connection.providerId)
        ))
        .forEach((connection) => {
            const label = document.createElement('label');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = connection.connectionId;
            checkbox.checked = true;
            label.append(checkbox, document.createTextNode(`${providerNames[connection.providerId]} (${connection.displayName})`));
            aiQaConnections.append(label);
        });
    const chapter = loadedChapters[selectedChapterIndex];
    checkAiQaButton.disabled = !chapter?.chapterId || aiQaConnections.querySelectorAll('input').length === 0;
}''',
    )

    # 3. Chapter-select reset: drop the dual-button reference, keep the
    #    checkbox-driven disabled state consistent
    apply(
        APP_JS_PATH,
        '''    checkAiQaButton.disabled = !chapter.chapterId;
    checkAiQaDualButton.disabled = !chapter.chapterId || (currentProject?.aiConfiguration?.qaConnectionIds || []).length < 2;
    aiQaStatus.textContent = '';''',
        '''    checkAiQaButton.disabled = !chapter.chapterId || aiQaConnections.querySelectorAll('input').length === 0;
    aiQaStatus.textContent = '';''',
    )

    # 4. checkCurrentChapterAiQa: read checked boxes instead of the old
    #    single-vs-all-models split
    apply(
        APP_JS_PATH,
        '''async function checkCurrentChapterAiQa(useAllModels) {
    const chapter = loadedChapters[selectedChapterIndex];
    if (!chapter?.chapterId || !currentProject?.projectId) {
        return;
    }
    const qaConnectionIds = currentProject.aiConfiguration?.qaConnectionIds || [];
    if (qaConnectionIds.length === 0) {
        aiQaStatus.textContent = 'Оберіть QA-моделі в налаштуваннях проєкту.';
        return;
    }
    const connectionIds = useAllModels ? qaConnectionIds : qaConnectionIds.slice(0, 1);
    const previousText = checkAiQaButton.textContent;
    checkAiQaButton.disabled = true;
    checkAiQaDualButton.disabled = true;
    checkAiQaButton.textContent = 'Перевіряємо…';
    aiQaStatus.textContent = '';
    clearAiQaIssues();
    try {
        const result = await WorkbenchApi.checkChapterTranslationQuality(currentProject.projectId, chapter.chapterId, connectionIds);
        renderAiQaResults(result);
    } catch (error) {
        aiQaStatus.textContent = `Помилка перевірки: ${error.message}`;
    } finally {
        checkAiQaButton.disabled = false;
        checkAiQaDualButton.disabled = qaConnectionIds.length < 2;
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
    checkAiQaButton.textContent = 'Перевіряємо…';
    aiQaStatus.textContent = '';
    clearAiQaIssues();
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
    )

    # === BACKEND ===

    # 5. Batch paragraphs per LLM call instead of sending the whole chapter
    #    at once, and accumulate errors across batches instead of
    #    overwriting them.
    apply(
        QA_SERVICE_PATH,
        '''    _QUALITY_CATEGORIES = {"critical", "stylistic", "typo"}

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
        }''',
        '''    _QUALITY_CATEGORIES = {"critical", "stylistic", "typo"}
    _QUALITY_BATCH_SIZE = 12

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
        batches = [
            translatable[i:i + self._QUALITY_BATCH_SIZE]
            for i in range(0, len(translatable), self._QUALITY_BATCH_SIZE)
        ]

        speech_registers = self._storage.get_project_character_registers(project_id)

        connections = {item["connectionId"]: item for item in self._storage.list_integration_connections()}
        findings_by_paragraph: dict[str, list[dict[str, Any]]] = {}
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
                try:
                    raw_text = provider.analyze(credentials, prompt)
                    parsed = self._parse_quality_response(raw_text)
                except (ValueError, QaServiceError) as error:
                    error_messages.setdefault(connection_id, []).append(str(error))
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

        errors = {
            connection_id: f"{len(messages)} з {len(batches)} частин розділу не вдалося перевірити: {messages[0]}" if len(messages) > 1 else messages[0]
            for connection_id, messages in error_messages.items()
        }

        return {
            "chapterId": chapter_id,
            "counts": counts,
            "paragraphResults": [
                {"paragraphId": paragraph_id, "findings": findings}
                for paragraph_id, findings in findings_by_paragraph.items()
            ],
            "errors": errors,
        }''',
    )

    # 6. Strengthen the prompt (single-line field values — this is what was
    #    almost certainly breaking Gemini's JSON) and add a best-effort
    #    repair pass in the parser before giving up.
    apply(
        QA_SERVICE_PATH,
        '''            "Якщо проблем немає — поверни порожній масив [].\\n\\n"
            f"Абзаци для перевірки:\\n{pairs}"
        )''',
        '''            "Якщо проблем немає — поверни порожній масив [].\\n\\n"
            "Кожне значення полів (quote, explanation, suggestion) має бути одним рядком, "
            "без символів нового рядка всередині значення.\\n\\n"
            f"Абзаци для перевірки:\\n{pairs}"
        )

    @staticmethod
    def _repair_json_newlines(text: str) -> str:
        """Best-effort fix for a common non-strict-JSON-mode LLM mistake:
        a literal raw newline/tab inside a string value, which is invalid
        per the JSON spec and makes json.loads fail (often surfacing as
        \\"Unterminated string...\\"). Walks the text tracking whether we're
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
                elif char == "\\\\":
                    result.append(char)
                    escaped = True
                elif char == \'"\':
                    in_string = False
                    result.append(char)
                elif char == "\\n":
                    result.append("\\\\n")
                elif char == "\\r":
                    result.append("\\\\r")
                elif char == "\\t":
                    result.append("\\\\t")
                else:
                    result.append(char)
            else:
                if char == \'"\':
                    in_string = True
                result.append(char)
        return "".join(result)''',
    )
    apply(
        QA_SERVICE_PATH,
        '''        try:
            data = json.loads(text)
        except json.JSONDecodeError as error:
            raise QaServiceError(f"AI QA response was not valid JSON: {error}") from error''',
        '''        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            try:
                data = json.loads(cls._repair_json_newlines(text))
            except json.JSONDecodeError as error:
                raise QaServiceError(f"AI QA response was not valid JSON: {error}") from error''',
    )

    print("Patch 32 applied successfully.")


if __name__ == "__main__":
    main()
