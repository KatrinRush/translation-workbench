"""
Patch 33: two more fixes from testing patch 32.

1. Катя's decision: a new AI QA run should ADD its findings to whatever is
   already shown (even from a different model), not wipe the previous run.
   renderAiQaResults now merges into the existing per-paragraph panel
   instead of clearing everything first, with a light dedup (same
   paragraph + category + quote + model = skip) so re-running the same
   model on unchanged text doesn't duplicate. Counters are recomputed from
   the merged set, not just the latest response's own counts.
   The old "clear everything" behavior is kept as an explicit manual
   action (new small "Скинути AI QA" control), since accumulating forever
   would go stale once paragraphs get re-translated.

2. Backend error-message bug: check_chapter_translation_quality's "X з Y
   частин не вдалося перевірити" context was only added when 2+ batches
   failed for a connection — a single failed batch (the common case) showed
   the raw JSON error with no context at all. Now always includes the
   batch count.

Depends on patches 25-32 already being applied.

Run from the repo root (same folder as backend/ and frontend/):
    python apply_patch33.py
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
    # === BACKEND ===

    # 1. Always show the "X з Y частин" context, not just when 2+ batches failed
    apply(
        QA_SERVICE_PATH,
        '''        errors = {
            connection_id: f"{len(messages)} з {len(batches)} частин розділу не вдалося перевірити: {messages[0]}" if len(messages) > 1 else messages[0]
            for connection_id, messages in error_messages.items()
        }''',
        '''        errors = {
            connection_id: f"{len(messages)} з {len(batches)} частин розділу не вдалося перевірити: {messages[0]}"
            for connection_id, messages in error_messages.items()
        }''',
    )

    # === FRONTEND ===

    # 2. Stop wiping results before a new run — accumulation happens in
    #    renderAiQaResults now, not by clearing first.
    apply(
        APP_JS_PATH,
        '''    checkAiQaButton.textContent = 'Перевіряємо…';
    aiQaStatus.textContent = '';
    clearAiQaIssues();
    try {
        const result = await WorkbenchApi.checkChapterTranslationQuality(currentProject.projectId, chapter.chapterId, connectionIds);''',
        '''    checkAiQaButton.textContent = 'Перевіряємо…';
    aiQaStatus.textContent = '';
    try {
        const result = await WorkbenchApi.checkChapterTranslationQuality(currentProject.projectId, chapter.chapterId, connectionIds);''',
    )

    # 3. Give the (now purely manual) reset a visible control next to the status
    apply(
        APP_JS_PATH,
        '''const aiQaStatus = document.createElement('span');
aiQaStatus.className = 'ai-qa-status';
aiQaStatus.id = 'ai-qa-status';
checkAiQaButton.insertAdjacentElement('afterend', aiQaStatus);''',
        '''const aiQaStatus = document.createElement('span');
aiQaStatus.className = 'ai-qa-status';
aiQaStatus.id = 'ai-qa-status';
checkAiQaButton.insertAdjacentElement('afterend', aiQaStatus);

const clearAiQaButton = document.createElement('button');
clearAiQaButton.type = 'button';
clearAiQaButton.className = 'text-btn';
clearAiQaButton.id = 'clear-ai-qa-button';
clearAiQaButton.textContent = 'Скинути AI QA';
aiQaStatus.insertAdjacentElement('afterend', clearAiQaButton);
clearAiQaButton.addEventListener('click', clearAiQaIssues);''',
    )

    # 4. Reset AI QA state properly on chapter change (rows get rebuilt, so
    #    stale DOM references in aiQaFlatFindings must go with them)
    apply(
        APP_JS_PATH,
        '''    checkAiQaButton.disabled = !chapter.chapterId || aiQaConnections.querySelectorAll('input').length === 0;
    aiQaStatus.textContent = '';''',
        '''    checkAiQaButton.disabled = !chapter.chapterId || aiQaConnections.querySelectorAll('input').length === 0;
    aiQaStatus.textContent = '';
    exitAiQaFilter();
    aiQaCounters.replaceChildren();
    aiQaFlatFindings = [];''',
    )

    # 5. renderAiQaResults: merge into existing panels/state instead of
    #    replacing them, with dedup and counters recomputed from the merge.
    apply(
        APP_JS_PATH,
        '''function renderAiQaResults(result) {
    clearAiQaIssues();
    exitAiQaFilter();
    const counts = result.counts || { critical: 0, stylistic: 0, typo: 0 };
    const errorMessages = Object.values(result.errors || {});
    aiQaStatus.textContent = errorMessages.length > 0 ? errorMessages.join(' ') : '';
    aiQaFlatFindings = [];

    ['critical', 'stylistic', 'typo'].forEach((category) => {
        const badge = document.createElement('button');
        badge.type = 'button';
        badge.className = `ai-qa-counter ai-qa-counter-${category}`;
        badge.textContent = `${AI_QA_CATEGORY_LABELS[category]}: ${counts[category] || 0}`;
        badge.disabled = !counts[category];
        badge.addEventListener('click', () => startAiQaFilter(category));
        aiQaCounters.append(badge);
    });

    const paragraphResults = result.paragraphResults || [];
    let findingSequence = 0;
    paragraphResults.forEach((paragraphResult) => {
        const row = translationRows.querySelector(`.translation-row[data-paragraph-id="${CSS.escape(paragraphResult.paragraphId)}"]`);
        if (!row) {
            return;
        }
        const panel = document.createElement('div');
        panel.className = 'ai-qa-issues';
        paragraphResult.findings.forEach((finding) => {
            const findingId = `finding-${findingSequence += 1}`;
            finding.findingId = findingId;
            finding.paragraphId = paragraphResult.paragraphId;

            const item = document.createElement('div');
            item.className = `ai-qa-finding ai-qa-finding-${finding.category}`;
            item.dataset.findingId = findingId;

            const chip = document.createElement('button');
            chip.type = 'button';
            chip.className = 'ai-qa-finding-chip';
            chip.textContent = `${AI_QA_CATEGORY_LABELS[finding.category] || finding.category} · «${finding.quote}» (${finding.sourceModel})`;

            const markBadge = document.createElement('span');
            markBadge.className = 'ai-qa-finding-mark-badge';
            markBadge.hidden = true;
            chip.append(markBadge);

            const details = document.createElement('div');
            details.className = 'ai-qa-finding-details';
            details.hidden = true;
            const explanation = document.createElement('p');
            explanation.textContent = finding.explanation || '';
            details.append(explanation);
            if (finding.suggestion) {
                const suggestion = document.createElement('p');
                suggestion.className = 'ai-qa-finding-suggestion';
                suggestion.textContent = `Варіант: ${finding.suggestion}`;
                details.append(suggestion);
            }

            chip.addEventListener('click', () => {
                details.hidden = !details.hidden;
            });

            item.append(chip, details);
            panel.append(item);
            aiQaFlatFindings.push({ findingId, paragraphId: paragraphResult.paragraphId, finding, row });
        });
        const translationControl = row.querySelector('.translation-control');
        if (translationControl) {
            translationControl.insertAdjacentElement('afterend', panel);
        } else {
            row.append(panel);
        }
    });
}''',
        '''let aiQaFindingSequence = 0;

function findOrCreateAiQaPanel(row) {
    let panel = row.querySelector('.ai-qa-issues');
    if (panel) {
        return panel;
    }
    panel = document.createElement('div');
    panel.className = 'ai-qa-issues';
    const translationControl = row.querySelector('.translation-control');
    if (translationControl) {
        translationControl.insertAdjacentElement('afterend', panel);
    } else {
        row.append(panel);
    }
    return panel;
}

function refreshAiQaCounters() {
    aiQaCounters.replaceChildren();
    const counts = { critical: 0, stylistic: 0, typo: 0 };
    aiQaFlatFindings.forEach((entry) => {
        if (Object.hasOwn(counts, entry.finding.category)) {
            counts[entry.finding.category] += 1;
        }
    });
    ['critical', 'stylistic', 'typo'].forEach((category) => {
        const badge = document.createElement('button');
        badge.type = 'button';
        badge.className = `ai-qa-counter ai-qa-counter-${category}`;
        badge.textContent = `${AI_QA_CATEGORY_LABELS[category]}: ${counts[category]}`;
        badge.disabled = !counts[category];
        badge.addEventListener('click', () => startAiQaFilter(category));
        aiQaCounters.append(badge);
    });
}

function renderAiQaResults(result) {
    const errorMessages = Object.values(result.errors || {});
    aiQaStatus.textContent = errorMessages.length > 0 ? errorMessages.join(' ') : '';

    const paragraphResults = result.paragraphResults || [];
    paragraphResults.forEach((paragraphResult) => {
        const row = translationRows.querySelector(`.translation-row[data-paragraph-id="${CSS.escape(paragraphResult.paragraphId)}"]`);
        if (!row) {
            return;
        }
        const panel = findOrCreateAiQaPanel(row);
        paragraphResult.findings.forEach((finding) => {
            const isDuplicate = aiQaFlatFindings.some((entry) => (
                entry.paragraphId === paragraphResult.paragraphId
                && entry.finding.category === finding.category
                && entry.finding.quote === finding.quote
                && entry.finding.sourceModel === finding.sourceModel
            ));
            if (isDuplicate) {
                return;
            }
            const findingId = `finding-${aiQaFindingSequence += 1}`;
            finding.findingId = findingId;
            finding.paragraphId = paragraphResult.paragraphId;

            const item = document.createElement('div');
            item.className = `ai-qa-finding ai-qa-finding-${finding.category}`;
            item.dataset.findingId = findingId;

            const chip = document.createElement('button');
            chip.type = 'button';
            chip.className = 'ai-qa-finding-chip';
            chip.textContent = `${AI_QA_CATEGORY_LABELS[finding.category] || finding.category} · «${finding.quote}» (${finding.sourceModel})`;

            const markBadge = document.createElement('span');
            markBadge.className = 'ai-qa-finding-mark-badge';
            markBadge.hidden = true;
            chip.append(markBadge);

            const details = document.createElement('div');
            details.className = 'ai-qa-finding-details';
            details.hidden = true;
            const explanation = document.createElement('p');
            explanation.textContent = finding.explanation || '';
            details.append(explanation);
            if (finding.suggestion) {
                const suggestion = document.createElement('p');
                suggestion.className = 'ai-qa-finding-suggestion';
                suggestion.textContent = `Варіант: ${finding.suggestion}`;
                details.append(suggestion);
            }

            chip.addEventListener('click', () => {
                details.hidden = !details.hidden;
            });

            item.append(chip, details);
            panel.append(item);
            aiQaFlatFindings.push({ findingId, paragraphId: paragraphResult.paragraphId, finding, row });
        });
        if (panel.children.length === 0) {
            panel.remove();
        }
    });

    refreshAiQaCounters();
}''',
    )

    print("Patch 33 applied successfully.")


if __name__ == "__main__":
    main()
