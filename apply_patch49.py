"""Patch 49 — "Скинути AI QA" also clears the queue.

Run from the repo root: python apply_patch49.py

Requires patches 44-48 already applied.

Until now, "Скинути AI QA" only cleared findings/counters and the
batch-progress resume state — it left any paragraphs still marked
"У черзі на QA" untouched. This patch makes it also uncheck and
persist-clear those, one PATCH /api/paragraphs/{id} per currently
queued paragraph in the open chapter (reusing the same field values
— translationText/reviewed/isService read straight from each row's
own controls — the queued-for-QA checkbox's own handler already uses
to avoid clobbering unsaved edits).

If a paragraph's clear-save fails, that one checkbox is left checked
(and re-enabled) rather than silently dropped from the queue.
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

    replace_once(
        path,
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
        '''async function clearAiQaIssues() {
    exitAiQaFilter();
    translationRows.querySelectorAll('.ai-qa-issues').forEach((panel) => panel.remove());
    aiQaCounters.replaceChildren();
    aiQaFlatFindings = [];
    const chapter = loadedChapters[selectedChapterIndex];
    if (chapter?.chapterId && currentProject?.projectId) {
        clearAiQaProgress(currentProject.projectId, chapter.chapterId);
    }
    exitAiQaActiveRun();
    await clearAiQaQueueInCurrentChapter();
}

async function clearAiQaQueueInCurrentChapter() {
    const checkboxes = [...translationRows.querySelectorAll('.qa-queue-checkbox:checked')];
    if (checkboxes.length === 0) {
        return;
    }
    await Promise.all(checkboxes.map(async (checkbox) => {
        const paragraphId = checkbox.dataset.paragraphId;
        if (!paragraphId) {
            return;
        }
        const row = checkbox.closest('.translation-row');
        const translationText = row ? serializeRichText(row.querySelector('.translation-paragraph')) : null;
        const reviewed = row ? Boolean(row.querySelector('.paragraph-review input')?.checked) : false;
        const isService = row ? Boolean(row.querySelector('.paragraph-service input')?.checked) : false;
        checkbox.disabled = true;
        try {
            const saved = await WorkbenchApi.updateParagraph(paragraphId, {
                translationText,
                reviewed,
                isService,
                queuedForQa: false,
            });
            checkbox.checked = Boolean(saved.queuedForQa);
            const chapter = loadedChapters[selectedChapterIndex];
            const element = chapter?.elements.find((item) => item.type === 'paragraph' && item.paragraphId === paragraphId);
            if (element) {
                element.queuedForQa = Boolean(saved.queuedForQa);
            }
        } catch (error) {
            // Leave it checked — clearing the queue here is a convenience,
            // not something that should silently drop a paragraph the user
            // deliberately queued if the save fails.
        } finally {
            checkbox.disabled = false;
        }
    }));
}''',
    )

    print(f"app.js patched: {path}")


if __name__ == "__main__":
    patch_app()
    print("Patch 49 applied.")
