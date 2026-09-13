"""Patch 48 — QA AI category (напрям) selection in the UI.

Run from the repo root: python apply_patch48.py

Requires patches 44-47 already applied.

The backend (patch 44) has supported a `categories` param since the
start; this patch just adds the missing UI for it — checkboxes for
critical / stylistic / typo, defaulting to all three checked (so
existing behavior is unchanged until someone unchecks something).

What this does (frontend/app.js only):
- New "Категорії" checkbox group (critical/stylistic/typo), inserted
  right after the model checkboxes in the QA AI tab.
- Both run paths (mode 1's stepped batches and mode 2's "Прогнати
  вибрані") now read the checked categories and send them as
  `categories` to the API; both refuse to run with zero categories
  checked, same as zero models checked.
- Category checkboxes are disabled while a mode-1 run is active,
  same as model checkboxes, so the scope can't change mid-run.
- Saved batch progress (localStorage) now also records which
  categories the run used; resuming only offers to continue when both
  the model set AND the category set match what's currently checked.
  Progress saved before this patch (no categories field) is simply
  treated as not-resumable — a harmless fresh start, not an error.
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


def patch_app() -> None:
    path = REPO_ROOT / "frontend" / "app.js"

    # 1. New category checkboxes, right after the model checkboxes container
    replace_once(
        path,
        '''const aiQaConnections = document.createElement('div');
aiQaConnections.className = 'ai-qa-connections';
aiQaConnections.id = 'ai-qa-connections';
translationQaContent.append(aiQaConnections);''',
        '''const aiQaConnections = document.createElement('div');
aiQaConnections.className = 'ai-qa-connections';
aiQaConnections.id = 'ai-qa-connections';
translationQaContent.append(aiQaConnections);

const AI_QA_CATEGORY_OPTIONS = [
    { value: 'critical', label: 'Критично' },
    { value: 'stylistic', label: 'Стилістично' },
    { value: 'typo', label: 'Одруківка' },
];

const aiQaCategories = document.createElement('div');
aiQaCategories.className = 'ai-qa-categories';
aiQaCategories.id = 'ai-qa-categories';
AI_QA_CATEGORY_OPTIONS.forEach(({ value, label }) => {
    const optionLabel = document.createElement('label');
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = value;
    checkbox.checked = true;
    optionLabel.append(checkbox, document.createTextNode(` ${label}`));
    aiQaCategories.append(optionLabel);
});
aiQaConnections.insertAdjacentElement('afterend', aiQaCategories);

function getSelectedAiQaCategories() {
    return [...aiQaCategories.querySelectorAll('input:checked')].map((checkbox) => checkbox.value);
}''',
    )

    # 2. Persisted progress now also carries + validates `categories`
    replace_once(
        path,
        '''        const parsed = JSON.parse(raw);
        if (typeof parsed?.batchIndex === 'number' && Array.isArray(parsed?.connectionIds)) {
            return parsed;
        }''',
        '''        const parsed = JSON.parse(raw);
        if (typeof parsed?.batchIndex === 'number' && Array.isArray(parsed?.connectionIds) && Array.isArray(parsed?.categories)) {
            return parsed;
        }''',
    )
    replace_once(
        path,
        '''function saveAiQaProgress(projectId, chapterId, batchIndex, connectionIds) {
    try {
        window.localStorage.setItem(aiQaProgressKey(projectId, chapterId), JSON.stringify({ batchIndex, connectionIds }));
    } catch (error) {''',
        '''function saveAiQaProgress(projectId, chapterId, batchIndex, connectionIds, categories) {
    try {
        window.localStorage.setItem(aiQaProgressKey(projectId, chapterId), JSON.stringify({ batchIndex, connectionIds, categories }));
    } catch (error) {''',
    )

    # 3. Disable/enable categories alongside connections
    replace_once(
        path,
        '''function setAiQaConnectionsDisabled(disabled) {
    aiQaConnections.querySelectorAll('input').forEach((checkbox) => {
        checkbox.disabled = disabled;
    });
}''',
        '''function setAiQaConnectionsDisabled(disabled) {
    aiQaConnections.querySelectorAll('input').forEach((checkbox) => {
        checkbox.disabled = disabled;
    });
    aiQaCategories.querySelectorAll('input').forEach((checkbox) => {
        checkbox.disabled = disabled;
    });
}''',
    )

    # 4. runAiQaBatch: pass categories through, save them with progress
    replace_once(
        path,
        '''    const { connectionIds, batchIndex } = aiQaActiveRun;
    setAiQaStepButtonsDisabled(true);
    aiQaStepStatus.textContent = `Перевіряємо батч ${batchIndex + 1}…`;
    let hadError = false;
    let totalBatches = aiQaActiveRun.totalBatches;
    try {
        for (const connectionId of connectionIds) {
            const result = await WorkbenchApi.checkChapterTranslationQuality(
                currentProject.projectId,
                chapter.chapterId,
                [connectionId],
                batchIndex,
            );
            renderAiQaResults(result);
            totalBatches = result.totalBatches;
            if (Object.keys(result.errors || {}).length > 0) {
                hadError = true;
            }
        }
        aiQaActiveRun.totalBatches = totalBatches;
        saveAiQaProgress(currentProject.projectId, chapter.chapterId, batchIndex, connectionIds);''',
        '''    const { connectionIds, categories, batchIndex } = aiQaActiveRun;
    setAiQaStepButtonsDisabled(true);
    aiQaStepStatus.textContent = `Перевіряємо батч ${batchIndex + 1}…`;
    let hadError = false;
    let totalBatches = aiQaActiveRun.totalBatches;
    try {
        for (const connectionId of connectionIds) {
            const result = await WorkbenchApi.checkChapterTranslationQuality(
                currentProject.projectId,
                chapter.chapterId,
                [connectionId],
                batchIndex,
                { categories },
            );
            renderAiQaResults(result);
            totalBatches = result.totalBatches;
            if (Object.keys(result.errors || {}).length > 0) {
                hadError = true;
            }
        }
        aiQaActiveRun.totalBatches = totalBatches;
        saveAiQaProgress(currentProject.projectId, chapter.chapterId, batchIndex, connectionIds, categories);''',
    )

    # 5. checkCurrentChapterAiQa: read + validate categories, factor them
    # into the resumable check and the active-run state
    replace_once(
        path,
        '''    const connectionIds = [...aiQaConnections.querySelectorAll('input:checked')].map((checkbox) => checkbox.value);
    if (connectionIds.length === 0) {
        aiQaStatus.textContent = 'Оберіть хоча б одну QA-модель.';
        return;
    }
    const saved = loadAiQaProgress(currentProject.projectId, chapter.chapterId);
    const resumable = saved && sameConnectionSet(saved.connectionIds, connectionIds);
    const startBatchIndex = resumable ? saved.batchIndex : 0;
    aiQaActiveRun = { connectionIds, batchIndex: startBatchIndex, totalBatches: startBatchIndex + 1 };''',
        '''    const connectionIds = [...aiQaConnections.querySelectorAll('input:checked')].map((checkbox) => checkbox.value);
    if (connectionIds.length === 0) {
        aiQaStatus.textContent = 'Оберіть хоча б одну QA-модель.';
        return;
    }
    const categories = getSelectedAiQaCategories();
    if (categories.length === 0) {
        aiQaStatus.textContent = 'Оберіть хоча б один напрям перевірки.';
        return;
    }
    const saved = loadAiQaProgress(currentProject.projectId, chapter.chapterId);
    const resumable = saved
        && sameConnectionSet(saved.connectionIds, connectionIds)
        && sameConnectionSet(saved.categories, categories);
    const startBatchIndex = resumable ? saved.batchIndex : 0;
    aiQaActiveRun = { connectionIds, categories, batchIndex: startBatchIndex, totalBatches: startBatchIndex + 1 };''',
    )

    # 6. checkSelectedParagraphsAiQa: read + validate categories, pass through
    replace_once(
        path,
        '''    const connectionIds = [...aiQaConnections.querySelectorAll('input:checked')].map((checkbox) => checkbox.value);
    if (connectionIds.length === 0) {
        aiQaStatus.textContent = 'Оберіть хоча б одну QA-модель.';
        return;
    }
    const previousText = runSelectedQaButton.textContent;''',
        '''    const connectionIds = [...aiQaConnections.querySelectorAll('input:checked')].map((checkbox) => checkbox.value);
    if (connectionIds.length === 0) {
        aiQaStatus.textContent = 'Оберіть хоча б одну QA-модель.';
        return;
    }
    const categories = getSelectedAiQaCategories();
    if (categories.length === 0) {
        aiQaStatus.textContent = 'Оберіть хоча б один напрям перевірки.';
        return;
    }
    const previousText = runSelectedQaButton.textContent;''',
    )
    replace_once(
        path,
        '''                    [connectionId],
                    batchIndex,
                    { paragraphIds },
                );''',
        '''                    [connectionId],
                    batchIndex,
                    { paragraphIds, categories },
                );''',
    )

    print(f"app.js patched: {path}")


if __name__ == "__main__":
    patch_app()
    print("Patch 48 applied.")
