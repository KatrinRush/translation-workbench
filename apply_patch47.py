"""Patch 47 — QA AI mode 1: stepped batches instead of auto-loop.

Run from the repo root: python apply_patch47.py

Requires patches 44, 45, 46 already applied.

What this does (frontend/app.js only):
- Replaces the old auto-loop-through-every-batch behavior of the "AI QA"
  button with a stepped flow: clicking it now runs exactly ONE batch, then
  reveals "Наступний батч" / "Повторити батч" / "Скасувати" controls.
- Progress (batchIndex + the connection set used) is saved to
  localStorage after every batch completes — not only on Cancel — so a
  reload, a chapter switch, or closing the tab never loses your place.
  "Скасувати" just collapses the step controls back to the idle "AI QA"
  button; it does not discard the saved progress.
- The idle button's label reflects saved progress for the currently
  open chapter: "AI QA (сенс/стиль)" with nothing saved, or
  "Продовжити AI QA (з батчу N)" if there is. Resume only applies when
  the currently-checked model set matches the one the saved progress
  was made with; otherwise it's treated as a fresh start from batch 0.
- Progress is cleared automatically once the last batch of a run
  completes, and also by the existing "Скинути AI QA" button (which now
  also exits any active stepped run).
- Model checkboxes are disabled while a stepped run is active, so the
  connection set can't change mid-run out from under the saved progress.

Mode 2 ("Прогнати вибрані", patch 45) is untouched — it already ran as
a single explicit batch set and didn't need stepping.
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

    # 1. New step-control DOM elements, chained after patch 45's "Прогнати вибрані"
    replace_once(
        path,
        '''const runSelectedQaButton = document.createElement('button');
runSelectedQaButton.type = 'button';
runSelectedQaButton.className = 'secondary-btn';
runSelectedQaButton.id = 'run-selected-qa-button';
runSelectedQaButton.textContent = 'Прогнати вибрані';
aiQaCounters.insertAdjacentElement('afterend', runSelectedQaButton);
runSelectedQaButton.addEventListener('click', () => checkSelectedParagraphsAiQa());''',
        '''const runSelectedQaButton = document.createElement('button');
runSelectedQaButton.type = 'button';
runSelectedQaButton.className = 'secondary-btn';
runSelectedQaButton.id = 'run-selected-qa-button';
runSelectedQaButton.textContent = 'Прогнати вибрані';
aiQaCounters.insertAdjacentElement('afterend', runSelectedQaButton);
runSelectedQaButton.addEventListener('click', () => checkSelectedParagraphsAiQa());

const aiQaStepControls = document.createElement('div');
aiQaStepControls.className = 'ai-qa-step-controls';
aiQaStepControls.id = 'ai-qa-step-controls';
aiQaStepControls.hidden = true;
runSelectedQaButton.insertAdjacentElement('afterend', aiQaStepControls);

const aiQaStepStatus = document.createElement('span');
aiQaStepStatus.className = 'ai-qa-step-status muted';
aiQaStepStatus.id = 'ai-qa-step-status';

const aiQaNextBatchButton = document.createElement('button');
aiQaNextBatchButton.type = 'button';
aiQaNextBatchButton.className = 'secondary-btn';
aiQaNextBatchButton.id = 'ai-qa-next-batch-button';
aiQaNextBatchButton.textContent = 'Наступний батч';
aiQaNextBatchButton.addEventListener('click', () => advanceAiQaBatch());

const aiQaRepeatBatchButton = document.createElement('button');
aiQaRepeatBatchButton.type = 'button';
aiQaRepeatBatchButton.className = 'secondary-btn';
aiQaRepeatBatchButton.id = 'ai-qa-repeat-batch-button';
aiQaRepeatBatchButton.textContent = 'Повторити батч';
aiQaRepeatBatchButton.addEventListener('click', () => { void runAiQaBatch(); });

const aiQaCancelBatchButton = document.createElement('button');
aiQaCancelBatchButton.type = 'button';
aiQaCancelBatchButton.className = 'text-btn';
aiQaCancelBatchButton.id = 'ai-qa-cancel-batch-button';
aiQaCancelBatchButton.textContent = 'Скасувати';
aiQaCancelBatchButton.addEventListener('click', () => exitAiQaActiveRun());

aiQaStepControls.append(aiQaStepStatus, aiQaNextBatchButton, aiQaRepeatBatchButton, aiQaCancelBatchButton);''',
    )

    # 2. Drop the old in-memory-only resume map; add persisted-progress
    # helpers and the active-run state.
    replace_once(
        path,
        '''const aiQaResumeBatchIndex = new Map();''',
        '''let aiQaActiveRun = null; // { connectionIds, batchIndex, totalBatches } | null

const AI_QA_PROGRESS_STORAGE_PREFIX = 'workbench:qaBatchProgress:';

function aiQaProgressKey(projectId, chapterId) {
    return `${AI_QA_PROGRESS_STORAGE_PREFIX}${projectId}:${chapterId}`;
}

function loadAiQaProgress(projectId, chapterId) {
    try {
        const raw = window.localStorage.getItem(aiQaProgressKey(projectId, chapterId));
        if (!raw) {
            return null;
        }
        const parsed = JSON.parse(raw);
        if (typeof parsed?.batchIndex === 'number' && Array.isArray(parsed?.connectionIds)) {
            return parsed;
        }
    } catch (error) {
        // Corrupt or outdated entry — treat as no saved progress.
    }
    return null;
}

function saveAiQaProgress(projectId, chapterId, batchIndex, connectionIds) {
    try {
        window.localStorage.setItem(aiQaProgressKey(projectId, chapterId), JSON.stringify({ batchIndex, connectionIds }));
    } catch (error) {
        // Best-effort only; a failed save just means no resume offer next time.
    }
}

function clearAiQaProgress(projectId, chapterId) {
    try {
        window.localStorage.removeItem(aiQaProgressKey(projectId, chapterId));
    } catch (error) {
        // ignore
    }
}

function sameConnectionSet(a, b) {
    if (a.length !== b.length) {
        return false;
    }
    const sortedA = [...a].sort();
    const sortedB = [...b].sort();
    return sortedA.every((value, index) => value === sortedB[index]);
}

function setAiQaConnectionsDisabled(disabled) {
    aiQaConnections.querySelectorAll('input').forEach((checkbox) => {
        checkbox.disabled = disabled;
    });
}

function setAiQaStepButtonsDisabled(disabled) {
    aiQaNextBatchButton.disabled = disabled;
    aiQaRepeatBatchButton.disabled = disabled;
    aiQaCancelBatchButton.disabled = disabled;
}

function updateAiQaResumeLabel() {
    const chapter = loadedChapters[selectedChapterIndex];
    if (!chapter?.chapterId || !currentProject?.projectId) {
        checkAiQaButton.textContent = 'AI QA (сенс/стиль)';
        return;
    }
    const saved = loadAiQaProgress(currentProject.projectId, chapter.chapterId);
    checkAiQaButton.textContent = saved ? `Продовжити AI QA (з батчу ${saved.batchIndex + 1})` : 'AI QA (сенс/стиль)';
}

function exitAiQaActiveRun() {
    aiQaActiveRun = null;
    aiQaStepControls.hidden = true;
    aiQaStepStatus.textContent = '';
    aiQaNextBatchButton.hidden = false;
    setAiQaConnectionsDisabled(false);
    checkAiQaButton.hidden = false;
    updateAiQaResumeLabel();
}

async function runAiQaBatch() {
    const chapter = loadedChapters[selectedChapterIndex];
    if (!chapter?.chapterId || !currentProject?.projectId || !aiQaActiveRun) {
        return;
    }
    const { connectionIds, batchIndex } = aiQaActiveRun;
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
        saveAiQaProgress(currentProject.projectId, chapter.chapterId, batchIndex, connectionIds);
        const isLastBatch = batchIndex + 1 >= totalBatches;
        aiQaStepStatus.textContent = hadError
            ? `Батч ${batchIndex + 1} з ${totalBatches} — з помилками (див. статус вище).`
            : `Батч ${batchIndex + 1} з ${totalBatches} перевірено.`;
        aiQaNextBatchButton.hidden = isLastBatch;
        if (isLastBatch) {
            clearAiQaProgress(currentProject.projectId, chapter.chapterId);
        }
    } catch (error) {
        aiQaStepStatus.textContent = `Помилка перевірки: ${error.message}`;
    } finally {
        setAiQaStepButtonsDisabled(false);
    }
}

async function advanceAiQaBatch() {
    if (!aiQaActiveRun) {
        return;
    }
    aiQaActiveRun.batchIndex += 1;
    await runAiQaBatch();
}''',
    )

    # 3. checkCurrentChapterAiQa: start-or-resume, run one batch, then hand
    # off to the stepping controls (was: auto-loop through every batch).
    replace_once(
        path,
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
    const saved = loadAiQaProgress(currentProject.projectId, chapter.chapterId);
    const resumable = saved && sameConnectionSet(saved.connectionIds, connectionIds);
    const startBatchIndex = resumable ? saved.batchIndex : 0;
    aiQaActiveRun = { connectionIds, batchIndex: startBatchIndex, totalBatches: startBatchIndex + 1 };
    aiQaStatus.textContent = '';
    setAiQaConnectionsDisabled(true);
    checkAiQaButton.hidden = true;
    aiQaStepControls.hidden = false;
    await runAiQaBatch();
}''',
    )

    # 4. clearAiQaIssues ("Скинути AI QA"): also drop saved progress and
    # exit any active stepped run.
    replace_once(
        path,
        '''function clearAiQaIssues() {
    exitAiQaFilter();
    translationRows.querySelectorAll('.ai-qa-issues').forEach((panel) => panel.remove());
    aiQaCounters.replaceChildren();
    aiQaFlatFindings = [];
    const chapter = loadedChapters[selectedChapterIndex];
    if (chapter?.chapterId) {
        const prefix = `${chapter.chapterId}:`;
        [...aiQaResumeBatchIndex.keys()].forEach((key) => {
            if (key.startsWith(prefix)) {
                aiQaResumeBatchIndex.delete(key);
            }
        });
    }
}''',
        '''function clearAiQaIssues() {
    exitAiQaFilter();
    translationRows.querySelectorAll('.ai-qa-issues').forEach((panel) => panel.remove());
    aiQaCounters.replaceChildren();
    aiQaFlatFindings = [];
    const chapter = loadedChapters[selectedChapterIndex];
    if (chapter?.chapterId && currentProject?.projectId) {
        clearAiQaProgress(currentProject.projectId, chapter.chapterId);
    }
    exitAiQaActiveRun();
}''',
    )

    # 5. renderChapterText: reset the stepping UI and refresh the idle
    # button's resume label whenever the selected chapter changes.
    replace_once(
        path,
        '''    checkAiQaButton.disabled = !chapter.chapterId || aiQaConnections.querySelectorAll('input').length === 0;
    aiQaStatus.textContent = '';
    exitAiQaFilter();
    aiQaCounters.replaceChildren();
    aiQaFlatFindings = [];
    if (chapter.chapterId && currentProject?.projectId) {
        void loadChapterAiQaFindings(chapter.chapterId);
    }''',
        '''    checkAiQaButton.disabled = !chapter.chapterId || aiQaConnections.querySelectorAll('input').length === 0;
    aiQaStatus.textContent = '';
    exitAiQaFilter();
    aiQaCounters.replaceChildren();
    aiQaFlatFindings = [];
    if (chapter.chapterId && currentProject?.projectId) {
        void loadChapterAiQaFindings(chapter.chapterId);
    }
    aiQaActiveRun = null;
    aiQaStepControls.hidden = true;
    aiQaStepStatus.textContent = '';
    aiQaNextBatchButton.hidden = false;
    setAiQaConnectionsDisabled(false);
    checkAiQaButton.hidden = false;
    updateAiQaResumeLabel();''',
    )

    print(f"app.js patched: {path}")


if __name__ == "__main__":
    patch_app()
    print("Patch 47 applied.")
