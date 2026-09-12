"""
Patch 30: AI QA frontend (MVP), wired to the check_chapter_translation_quality
endpoint from patch 29.

Scope for this patch (deliberately reduced from the full spec discussed
earlier, to ship something testable now):
  - a button next to "Перевірити узгодження" that runs the combined LLM QA
    check using the project's configured qaConnectionIds (single model by
    default; a secondary button opts into running ALL configured QA models
    at once, per the "dual-run is opt-in, not default" decision)
  - three always-visible counters (critical / stylistic / typo)
  - one chip per finding under the paragraph (colored by category, tagged
    with which model found it), click to expand explanation + suggestion

NOT yet in this patch (planned as a follow-up): the click-through filter
mode with ✔️/✖️ marks and next/prev navigation from the original UX spec.

Depends on patch 25 (speech_register) and patch 29 (backend endpoint)
already being applied.

Run from the repo root (same folder as frontend/):
    python apply_patch30.py
"""
from pathlib import Path

API_JS_PATH = Path("frontend/api.js")
APP_JS_PATH = Path("frontend/app.js")
STYLES_CSS_PATH = Path("frontend/styles.css")


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
    # 1. api.js: new method, same shape as checkChapterGenderAgreement
    apply(
        API_JS_PATH,
        '''    checkChapterGenderAgreement(projectId, chapterId) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/chapters/${encodeURIComponent(chapterId)}/check-gender-agreement`, {
            method: 'POST',
            body: JSON.stringify({})
        });
    },''',
        '''    checkChapterGenderAgreement(projectId, chapterId) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/chapters/${encodeURIComponent(chapterId)}/check-gender-agreement`, {
            method: 'POST',
            body: JSON.stringify({})
        });
    },

    checkChapterTranslationQuality(projectId, chapterId, connectionIds) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/chapters/${encodeURIComponent(chapterId)}/qa-check`, {
            method: 'POST',
            body: JSON.stringify({ connectionIds })
        });
    },''',
    )

    # 2. app.js: new DOM elements next to the gender-agreement ones
    apply(
        APP_JS_PATH,
        '''const genderAgreementStatus = document.createElement('span');
genderAgreementStatus.className = 'paragraph-status';
genderAgreementStatus.id = 'gender-agreement-status';
checkGenderAgreementButton.insertAdjacentElement('afterend', genderAgreementStatus);''',
        '''const genderAgreementStatus = document.createElement('span');
genderAgreementStatus.className = 'paragraph-status';
genderAgreementStatus.id = 'gender-agreement-status';
checkGenderAgreementButton.insertAdjacentElement('afterend', genderAgreementStatus);

const checkAiQaButton = document.createElement('button');
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
checkAiQaDualButton.insertAdjacentElement('afterend', aiQaStatus);

const aiQaCounters = document.createElement('div');
aiQaCounters.className = 'ai-qa-counters';
aiQaCounters.id = 'ai-qa-counters';
aiQaStatus.insertAdjacentElement('afterend', aiQaCounters);''',
    )

    # 3. app.js: reset AI QA state whenever a different chapter is selected
    apply(
        APP_JS_PATH,
        '''    checkGenderAgreementButton.disabled = !chapter.chapterId;
    genderAgreementStatus.textContent = '';''',
        '''    checkGenderAgreementButton.disabled = !chapter.chapterId;
    genderAgreementStatus.textContent = '';
    checkAiQaButton.disabled = !chapter.chapterId;
    checkAiQaDualButton.disabled = !chapter.chapterId || (currentProject?.aiConfiguration?.qaConnectionIds || []).length < 2;
    aiQaStatus.textContent = '';
    aiQaCounters.replaceChildren();''',
    )

    # 4. app.js: the actual check/render functions, appended right after the
    #    existing gender-agreement ones (same file section, same style)
    apply(
        APP_JS_PATH,
        '''        const translationControl = row.querySelector('.translation-control');
        if (translationControl) {
            translationControl.insertAdjacentElement('afterend', panel);
        } else {
            row.append(panel);
        }
    });
}

function undoTranslation() {''',
        '''        const translationControl = row.querySelector('.translation-control');
        if (translationControl) {
            translationControl.insertAdjacentElement('afterend', panel);
        } else {
            row.append(panel);
        }
    });
}

const AI_QA_CATEGORY_LABELS = { critical: 'Критично', stylistic: 'Стилістично', typo: 'Одруківка' };

async function checkCurrentChapterAiQa(useAllModels) {
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
}

function clearAiQaIssues() {
    translationRows.querySelectorAll('.ai-qa-issues').forEach((panel) => panel.remove());
    aiQaCounters.replaceChildren();
}

function renderAiQaResults(result) {
    clearAiQaIssues();
    const counts = result.counts || { critical: 0, stylistic: 0, typo: 0 };
    const errorMessages = Object.values(result.errors || {});
    aiQaStatus.textContent = errorMessages.length > 0 ? errorMessages.join(' ') : '';

    ['critical', 'stylistic', 'typo'].forEach((category) => {
        const badge = document.createElement('span');
        badge.className = `ai-qa-counter ai-qa-counter-${category}`;
        badge.textContent = `${AI_QA_CATEGORY_LABELS[category]}: ${counts[category] || 0}`;
        aiQaCounters.append(badge);
    });

    const paragraphResults = result.paragraphResults || [];
    paragraphResults.forEach((paragraphResult) => {
        const row = translationRows.querySelector(`.translation-row[data-paragraph-id="${CSS.escape(paragraphResult.paragraphId)}"]`);
        if (!row) {
            return;
        }
        const panel = document.createElement('div');
        panel.className = 'ai-qa-issues';
        paragraphResult.findings.forEach((finding) => {
            const item = document.createElement('div');
            item.className = `ai-qa-finding ai-qa-finding-${finding.category}`;

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
        });
        const translationControl = row.querySelector('.translation-control');
        if (translationControl) {
            translationControl.insertAdjacentElement('afterend', panel);
        } else {
            row.append(panel);
        }
    });
}

function undoTranslation() {''',
    )

    # 5. styles.css: visual styling for the counters and finding chips
    apply(
        STYLES_CSS_PATH,
        '''.paragraph-status {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
}''',
        '''.paragraph-status {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
}

.ai-qa-status {
    color: var(--color-danger);
    font-size: 13px;
}

.ai-qa-counters {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 8px 0;
}

.ai-qa-counter {
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 600;
    border: 1px solid var(--color-border);
    background: var(--color-bg-inset);
    color: var(--color-text-secondary);
}

.ai-qa-counter-critical {
    background: var(--color-danger-bg-subtle);
    border-color: var(--color-danger-border-subtle);
    color: var(--color-danger);
}

.ai-qa-counter-stylistic {
    background: var(--color-warning-bg-subtle);
    border-color: var(--color-warning-border-subtle);
    color: var(--color-warning-text);
}

.ai-qa-issues {
    display: grid;
    gap: 6px;
    padding: 0 10px 8px;
}

.ai-qa-finding-chip {
    width: 100%;
    text-align: left;
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 13px;
    background: var(--color-bg-surface);
    border: 1px solid var(--color-border);
    color: var(--color-text-primary);
}

.ai-qa-finding-critical .ai-qa-finding-chip {
    border-color: var(--color-danger-border-subtle);
    background: var(--color-danger-bg-subtle);
}

.ai-qa-finding-stylistic .ai-qa-finding-chip {
    border-color: var(--color-warning-border-subtle);
    background: var(--color-warning-bg-subtle);
}

.ai-qa-finding-typo .ai-qa-finding-chip {
    border-color: var(--color-border-neutral);
    background: var(--color-bg-inset);
    color: var(--color-text-muted);
}

.ai-qa-finding-details {
    padding: 6px 10px;
    font-size: 13px;
    color: var(--color-text-secondary);
}

.ai-qa-finding-details p {
    margin: 4px 0;
}

.ai-qa-finding-suggestion {
    color: var(--color-text-primary);
    font-weight: 600;
}''',
    )

    print("Patch 30 applied successfully.")


if __name__ == "__main__":
    main()
