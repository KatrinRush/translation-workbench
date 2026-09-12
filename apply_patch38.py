"""
Patch 38: split AI QA requests by connection too, not just by batch.

Patch 37 made each HTTP call handle one batch — but if 2+ QA models are
checked, that one call still ran ALL of them sequentially inside itself
(Claude then Gemini, each with retries), so a single request could still
run long enough to risk another Cloudflare 524. Now the frontend loops
model-by-model AND batch-by-batch, so every request does exactly one
model's one batch. No backend change needed — check_chapter_translation_quality
already accepts a single-connection list and its totalBatches is
independent of how many connections are passed.

Resume tracking is now keyed by chapter+connection together, so a failure
partway through Gemini's run doesn't affect Claude's already-completed
progress (and vice versa).

Depends on patch 37 already being applied.

Run from the repo root (same folder as frontend/):
    python apply_patch38.py
"""
from pathlib import Path

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
    const providerLabelByConnectionId = new Map(
        [...aiQaConnections.querySelectorAll('input')].map((checkbox) => [checkbox.value, checkbox.parentElement.textContent.trim()]),
    );
    const previousText = checkAiQaButton.textContent;
    checkAiQaButton.disabled = true;
    aiQaStatus.textContent = '';
    try {
        for (const connectionId of connectionIds) {
            const resumeKey = `${chapter.chapterId}:${connectionId}`;
            const modelLabel = providerLabelByConnectionId.get(connectionId) || '';
            let batchIndex = aiQaResumeBatchIndex.get(resumeKey) || 0;
            let totalBatches = batchIndex + 1;
            while (batchIndex < totalBatches) {
                const progress = totalBatches > 1 ? ` (${batchIndex + 1} з ${totalBatches})` : '';
                checkAiQaButton.textContent = connectionIds.length > 1 ? `Перевіряємо ${modelLabel}${progress}…` : `Перевіряємо${progress}…`;
                const result = await WorkbenchApi.checkChapterTranslationQuality(currentProject.projectId, chapter.chapterId, [connectionId], batchIndex);
                renderAiQaResults(result);
                totalBatches = result.totalBatches;
                batchIndex += 1;
                aiQaResumeBatchIndex.set(resumeKey, batchIndex);
            }
            aiQaResumeBatchIndex.delete(resumeKey);
        }
    } catch (error) {
        aiQaStatus.textContent = `Помилка перевірки: ${error.message}. Натисни ще раз, щоб продовжити з цього місця.`;
    } finally {
        checkAiQaButton.disabled = false;
        checkAiQaButton.textContent = previousText;
    }
}''',
    )

    apply(
        APP_JS_PATH,
        '''    const chapter = loadedChapters[selectedChapterIndex];
    if (chapter?.chapterId) {
        aiQaResumeBatchIndex.delete(chapter.chapterId);
    }
}''',
        '''    const chapter = loadedChapters[selectedChapterIndex];
    if (chapter?.chapterId) {
        const prefix = `${chapter.chapterId}:`;
        [...aiQaResumeBatchIndex.keys()].forEach((key) => {
            if (key.startsWith(prefix)) {
                aiQaResumeBatchIndex.delete(key);
            }
        });
    }
}''',
    )

    print("Patch 38 applied successfully.")


if __name__ == "__main__":
    main()
