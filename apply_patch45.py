"""Patch 45 — frontend mode 2: targeted paragraph re-run for AI QA.

Run from the repo root: python apply_patch45.py

Requires patch 44 already applied (backend: paragraph_ids/queuedForQa
support in backend/storage.py and backend/qa/service.py).

What this does:
1. frontend/api.js
   - `checkChapterTranslationQuality` gains an optional 5th `options`
     param ({ paragraphIds, categories, batchSize }), sent in the request
     body when present. Existing (batchIndex-only) callers are untouched.
2. frontend/app.js
   - loaded chapter paragraphs now carry `queuedForQa` (from the backend)
   - each paragraph row gets a third checkbox, "У черзі на QA", next to
     "Перевірено"/"Службовий текст" — toggling it saves immediately via
     the existing PATCH /api/paragraphs/{id} (same pattern as the
     "Службовий текст" checkbox). It is intentionally NOT wired into the
     translation-draft/undo/dirty-tracking system (createParagraphDraft /
     readTranslationDraft / paragraphDraftsEqual) since it's an
     independent workflow flag, not translated content.
   - a new "Прогнати вибрані" button (next to the existing AI QA
     controls) collects every currently-checked "у черзі" checkbox in
     the open chapter and runs AI QA on just that set, reusing the same
     batch-loop shape as the whole-chapter run. On a clean run (no
     connection errors at all across the whole call), the checkboxes are
     unchecked locally to mirror the backend's own auto-clear of
     queued_for_qa; if any connection reported an error, checkboxes are
     left checked so nothing silently drops off the queue.

This is UI-only wiring on top of patch 44's backend support; it does not
touch the QA AI tab / mode 1 batch-stepping controls (separate patch).
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


def patch_api() -> None:
    path = REPO_ROOT / "frontend" / "api.js"

    replace_once(
        path,
        '''    checkChapterTranslationQuality(projectId, chapterId, connectionIds, batchIndex = 0) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/chapters/${encodeURIComponent(chapterId)}/qa-check`, {
            method: 'POST',
            body: JSON.stringify({ connectionIds, batchIndex })
        });
    },''',
        '''    checkChapterTranslationQuality(projectId, chapterId, connectionIds, batchIndex = 0, options = {}) {
        const { paragraphIds, categories, batchSize } = options;
        const body = { connectionIds, batchIndex };
        if (paragraphIds) body.paragraphIds = paragraphIds;
        if (categories) body.categories = categories;
        if (batchSize) body.batchSize = batchSize;
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/chapters/${encodeURIComponent(chapterId)}/qa-check`, {
            method: 'POST',
            body: JSON.stringify(body)
        });
    },''',
    )

    print(f"api.js patched: {path}")


def patch_app() -> None:
    path = REPO_ROOT / "frontend" / "app.js"

    # 1. Carry queuedForQa through chapter normalization on load
    replace_once(
        path,
        '''                if (typeof rawParagraph !== 'string') {
                    return {
                        type: 'paragraph',
                        paragraphId: rawParagraph.paragraphId || null,
                        originalText: rawParagraph.originalText || '',
                        translationText: rawParagraph.translationText || null,
                        reviewed: Boolean(rawParagraph.reviewed),
                        isService: Boolean(rawParagraph.isService),
                        footnotes: Array.isArray(rawParagraph.footnotes) ? rawParagraph.footnotes : [],
                    };
                }''',
        '''                if (typeof rawParagraph !== 'string') {
                    return {
                        type: 'paragraph',
                        paragraphId: rawParagraph.paragraphId || null,
                        originalText: rawParagraph.originalText || '',
                        translationText: rawParagraph.translationText || null,
                        reviewed: Boolean(rawParagraph.reviewed),
                        isService: Boolean(rawParagraph.isService),
                        queuedForQa: Boolean(rawParagraph.queuedForQa),
                        footnotes: Array.isArray(rawParagraph.footnotes) ? rawParagraph.footnotes : [],
                    };
                }''',
    )

    # 2. New per-paragraph "queued for QA" checkbox, inserted right after
    # the existing "Службовий текст" checkbox and before it's wired into
    # `actions`.
    replace_once(
        path,
        '''        const serviceText = document.createElement('span');
        serviceText.textContent = 'Службовий текст';
        service.append(serviceCheckbox, serviceText);
        const status = document.createElement('span');
        status.className = 'paragraph-status';
        const actions = document.createElement('div');
        actions.className = 'paragraph-actions';
        actions.append(translateButton, review, service);''',
        '''        const serviceText = document.createElement('span');
        serviceText.textContent = 'Службовий текст';
        service.append(serviceCheckbox, serviceText);
        const qaQueue = document.createElement('label');
        qaQueue.className = 'paragraph-review paragraph-qa-queue';
        const qaQueueCheckbox = document.createElement('input');
        qaQueueCheckbox.type = 'checkbox';
        qaQueueCheckbox.className = 'qa-queue-checkbox';
        qaQueueCheckbox.dataset.paragraphId = paragraph.paragraphId || '';
        qaQueueCheckbox.checked = Boolean(paragraph.queuedForQa);
        qaQueueCheckbox.disabled = !paragraph.paragraphId;
        qaQueueCheckbox.addEventListener('focus', () => setCurrentParagraph(paragraph.paragraphId));
        qaQueueCheckbox.addEventListener('change', async () => {
            const nextQueued = qaQueueCheckbox.checked;
            if (!paragraph.paragraphId) {
                return;
            }
            qaQueueCheckbox.disabled = true;
            try {
                const currentDraft = state.draft[currentParagraphIndex];
                const saved = await WorkbenchApi.updateParagraph(paragraph.paragraphId, {
                    translationText: currentDraft?.translationText || null,
                    reviewed: currentDraft?.reviewed ?? Boolean(paragraph.reviewed),
                    isService: currentDraft?.isService ?? Boolean(paragraph.isService),
                    queuedForQa: nextQueued,
                });
                paragraph.queuedForQa = Boolean(saved.queuedForQa);
                qaQueueCheckbox.checked = Boolean(saved.queuedForQa);
            } catch (error) {
                qaQueueCheckbox.checked = !nextQueued;
                window.alert(`Не вдалося зберегти позначку QA: ${error.message}`);
            } finally {
                qaQueueCheckbox.disabled = false;
            }
        });
        const qaQueueText = document.createElement('span');
        qaQueueText.textContent = 'У черзі на QA';
        qaQueue.append(qaQueueCheckbox, qaQueueText);
        const status = document.createElement('span');
        status.className = 'paragraph-status';
        const actions = document.createElement('div');
        actions.className = 'paragraph-actions';
        actions.append(translateButton, review, service, qaQueue);''',
    )

    # 3. New "Прогнати вибрані" button, next to the existing AI QA controls
    replace_once(
        path,
        '''aiQaStatus.insertAdjacentElement('afterend', aiQaCounters);''',
        '''aiQaStatus.insertAdjacentElement('afterend', aiQaCounters);

const runSelectedQaButton = document.createElement('button');
runSelectedQaButton.type = 'button';
runSelectedQaButton.className = 'secondary-btn';
runSelectedQaButton.id = 'run-selected-qa-button';
runSelectedQaButton.textContent = 'Прогнати вибрані';
aiQaCounters.insertAdjacentElement('afterend', runSelectedQaButton);
runSelectedQaButton.addEventListener('click', () => checkSelectedParagraphsAiQa());''',
    )

    # 4. Handler for the new button, right after checkCurrentChapterAiQa
    replace_once(
        path,
        '''    } catch (error) {
        aiQaStatus.textContent = `Помилка перевірки: ${error.message}. Натисни ще раз, щоб продовжити з цього місця.`;
    } finally {
        checkAiQaButton.disabled = false;
        checkAiQaButton.textContent = previousText;
    }
}

async function loadChapterAiQaFindings(chapterId) {''',
        '''    } catch (error) {
        aiQaStatus.textContent = `Помилка перевірки: ${error.message}. Натисни ще раз, щоб продовжити з цього місця.`;
    } finally {
        checkAiQaButton.disabled = false;
        checkAiQaButton.textContent = previousText;
    }
}

async function checkSelectedParagraphsAiQa() {
    const chapter = loadedChapters[selectedChapterIndex];
    if (!chapter?.chapterId || !currentProject?.projectId) {
        return;
    }
    const paragraphIds = [...translationRows.querySelectorAll('.qa-queue-checkbox:checked')]
        .map((checkbox) => checkbox.dataset.paragraphId)
        .filter(Boolean);
    if (paragraphIds.length === 0) {
        aiQaStatus.textContent = 'Познач абзаци чекбоксом «У черзі на QA».';
        return;
    }
    const connectionIds = [...aiQaConnections.querySelectorAll('input:checked')].map((checkbox) => checkbox.value);
    if (connectionIds.length === 0) {
        aiQaStatus.textContent = 'Оберіть хоча б одну QA-модель.';
        return;
    }
    const previousText = runSelectedQaButton.textContent;
    runSelectedQaButton.disabled = true;
    aiQaStatus.textContent = '';
    let hadErrors = false;
    try {
        for (const connectionId of connectionIds) {
            let batchIndex = 0;
            let totalBatches = 1;
            while (batchIndex < totalBatches) {
                const progress = totalBatches > 1 ? ` (${batchIndex + 1} з ${totalBatches})` : '';
                runSelectedQaButton.textContent = `Перевіряємо вибрані${progress}…`;
                const result = await WorkbenchApi.checkChapterTranslationQuality(
                    currentProject.projectId,
                    chapter.chapterId,
                    [connectionId],
                    batchIndex,
                    { paragraphIds },
                );
                renderAiQaResults(result);
                if (Object.keys(result.errors || {}).length > 0) {
                    hadErrors = true;
                }
                totalBatches = result.totalBatches;
                batchIndex += 1;
            }
        }
        if (!hadErrors) {
            // Mirrors the backend auto-clearing queued_for_qa once every
            // requested connection has checked this set without error.
            translationRows.querySelectorAll('.qa-queue-checkbox').forEach((checkbox) => {
                if (paragraphIds.includes(checkbox.dataset.paragraphId)) {
                    checkbox.checked = false;
                }
            });
            chapter.elements.forEach((element) => {
                if (element.type === 'paragraph' && paragraphIds.includes(element.paragraphId)) {
                    element.queuedForQa = false;
                }
            });
        }
    } catch (error) {
        aiQaStatus.textContent = `Помилка перевірки вибраних: ${error.message}`;
    } finally {
        runSelectedQaButton.disabled = false;
        runSelectedQaButton.textContent = previousText;
    }
}

async function loadChapterAiQaFindings(chapterId) {''',
    )

    print(f"app.js patched: {path}")


if __name__ == "__main__":
    patch_api()
    patch_app()
    print("Patch 45 applied.")
