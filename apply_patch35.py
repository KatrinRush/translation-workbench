"""
Patch 35: frontend wiring for the persistence added in patch 34.

  - Opening/selecting a chapter now fetches its already-pending AI QA
    findings (GET qa-findings) and renders them, so switching chapters and
    back no longer loses everything.
  - Since the backend now always returns the complete current pending set
    (not just "what this call found"), renderAiQaResults goes back to a
    full replace instead of patch 33's client-side merge/dedup — the
    server is the single source of truth now, so client-side dedup would
    just be redundant work.
  - ✔️/✖️ now actually calls DELETE /api/qa-findings/{findingId} and, on
    success, removes the finding from the page entirely (per Катя's
    decision: once resolved it's not kept around at all, not even
    greyed-out) instead of leaving a permanent grey badge.

Depends on patches 25-34 already being applied.

Run from the repo root (same folder as frontend/):
    python apply_patch35.py
"""
from pathlib import Path

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
    # 1. api.js: two new methods for the patch 34 endpoints
    apply(
        API_JS_PATH,
        '''    checkChapterTranslationQuality(projectId, chapterId, connectionIds) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/chapters/${encodeURIComponent(chapterId)}/qa-check`, {
            method: 'POST',
            body: JSON.stringify({ connectionIds })
        });
    },''',
        '''    checkChapterTranslationQuality(projectId, chapterId, connectionIds) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/chapters/${encodeURIComponent(chapterId)}/qa-check`, {
            method: 'POST',
            body: JSON.stringify({ connectionIds })
        });
    },

    listChapterQaFindings(projectId, chapterId) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/chapters/${encodeURIComponent(chapterId)}/qa-findings`);
    },

    resolveQaFinding(findingId) {
        return this.request(`/api/qa-findings/${encodeURIComponent(findingId)}`, { method: 'DELETE' });
    },''',
    )

    # 2. app.js: clean up the duplicate replaceChildren() left over from
    #    patch 33, and fetch existing findings when a chapter is selected
    apply(
        APP_JS_PATH,
        '''    checkAiQaButton.disabled = !chapter.chapterId || aiQaConnections.querySelectorAll('input').length === 0;
    aiQaStatus.textContent = '';
    exitAiQaFilter();
    aiQaCounters.replaceChildren();
    aiQaFlatFindings = [];
    aiQaCounters.replaceChildren();''',
        '''    checkAiQaButton.disabled = !chapter.chapterId || aiQaConnections.querySelectorAll('input').length === 0;
    aiQaStatus.textContent = '';
    exitAiQaFilter();
    aiQaCounters.replaceChildren();
    aiQaFlatFindings = [];
    if (chapter.chapterId && currentProject?.projectId) {
        void loadChapterAiQaFindings(chapter.chapterId);
    }''',
    )

    # 3. app.js: new loader, calling the same renderer used after a run
    apply(
        APP_JS_PATH,
        '''function clearAiQaIssues() {''',
        '''async function loadChapterAiQaFindings(chapterId) {
    try {
        const result = await WorkbenchApi.listChapterQaFindings(currentProject.projectId, chapterId);
        renderAiQaResults(result);
    } catch (error) {
        aiQaStatus.textContent = `Не вдалося завантажити AI QA: ${error.message}`;
    }
}

function clearAiQaIssues() {''',
    )

    # 4. app.js: renderAiQaResults becomes a full replace (server is now
    #    the single source of truth, no client-side dedup needed) and uses
    #    the real, stable findingId from the backend instead of a local
    #    sequence number. Drop the never-shown mark badge too.
    apply(
        APP_JS_PATH,
        '''let aiQaFindingSequence = 0;

function findOrCreateAiQaPanel(row) {''',
        '''function findOrCreateAiQaPanel(row) {''',
    )
    apply(
        APP_JS_PATH,
        '''function renderAiQaResults(result) {
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
        '''function renderAiQaResults(result) {
    // The backend always returns the complete current pending set, so this
    // is a full replace, not a merge.
    exitAiQaFilter();
    translationRows.querySelectorAll('.ai-qa-issues').forEach((panel) => panel.remove());
    aiQaFlatFindings = [];

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
            const findingId = finding.findingId;
            finding.paragraphId = paragraphResult.paragraphId;

            const item = document.createElement('div');
            item.className = `ai-qa-finding ai-qa-finding-${finding.category}`;
            item.dataset.findingId = findingId;

            const chip = document.createElement('button');
            chip.type = 'button';
            chip.className = 'ai-qa-finding-chip';
            chip.textContent = `${AI_QA_CATEGORY_LABELS[finding.category] || finding.category} · «${finding.quote}» (${finding.sourceModel})`;

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

    # 5. app.js: the nav bar no longer needs the "already marked" branch —
    #    a marked finding is deleted immediately, so it can never be shown
    #    again mid-filter. Always render the two action buttons.
    apply(
        APP_JS_PATH,
        '''    if (entry.finding.mark) {
        const markLabel = document.createElement('span');
        markLabel.className = 'ai-qa-nav-mark';
        markLabel.textContent = entry.finding.mark === 'accepted' ? '✔️' : '✖️';
        aiQaNavContent.append(markLabel);
    } else {
        const accept = document.createElement('button');
        accept.type = 'button';
        accept.className = 'icon-btn';
        accept.setAttribute('aria-label', 'Погодитись зі знахідкою');
        accept.textContent = '✔️';
        accept.addEventListener('click', () => markAiQaFinding(entry, 'accepted'));
        const dismiss = document.createElement('button');
        dismiss.type = 'button';
        dismiss.className = 'icon-btn';
        dismiss.setAttribute('aria-label', 'Відхилити знахідку');
        dismiss.textContent = '✖️';
        dismiss.addEventListener('click', () => markAiQaFinding(entry, 'dismissed'));
        aiQaNavContent.append(accept, dismiss);
    }
}''',
        '''    const accept = document.createElement('button');
    accept.type = 'button';
    accept.className = 'icon-btn';
    accept.setAttribute('aria-label', 'Погодитись зі знахідкою');
    accept.textContent = '✔️';
    accept.addEventListener('click', () => void markAiQaFinding(entry));
    const dismiss = document.createElement('button');
    dismiss.type = 'button';
    dismiss.className = 'icon-btn';
    dismiss.setAttribute('aria-label', 'Відхилити знахідку');
    dismiss.textContent = '✖️';
    dismiss.addEventListener('click', () => void markAiQaFinding(entry));
    aiQaNavContent.append(accept, dismiss);
}''',
    )

    # 6. app.js: marking now deletes the finding server-side and removes it
    #    from the page outright — no more permanent grey badge.
    apply(
        APP_JS_PATH,
        '''function markAiQaFinding(entry, mark) {
    entry.finding.mark = mark;
    const itemEl = translationRows.querySelector(`.ai-qa-finding[data-finding-id="${CSS.escape(entry.findingId)}"]`);
    if (itemEl) {
        itemEl.classList.add('ai-qa-finding-marked');
        itemEl.dataset.mark = mark;
        const badge = itemEl.querySelector('.ai-qa-finding-mark-badge');
        if (badge) {
            badge.hidden = false;
            badge.textContent = mark === 'accepted' ? '✔️' : '✖️';
        }
    }
    showAiQaFilterItem();
}''',
        '''async function markAiQaFinding(entry) {
    try {
        await WorkbenchApi.resolveQaFinding(entry.findingId);
    } catch (error) {
        aiQaStatus.textContent = `Не вдалося зберегти позначку: ${error.message}`;
        return;
    }
    aiQaFlatFindings = aiQaFlatFindings.filter((item) => item.findingId !== entry.findingId);
    const itemEl = translationRows.querySelector(`.ai-qa-finding[data-finding-id="${CSS.escape(entry.findingId)}"]`);
    if (itemEl) {
        const panel = itemEl.closest('.ai-qa-issues');
        itemEl.remove();
        if (panel && panel.children.length === 0) {
            panel.remove();
        }
    }
    refreshAiQaCounters();
    showAiQaFilterItem();
}''',
    )

    print("Patch 35 applied successfully.")


if __name__ == "__main__":
    main()
