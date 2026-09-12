"""
Patch 31: AI QA filter mode — click a category counter to step through its
findings one at a time via a bottom nav bar (mirrors the existing
search-nav-bar pattern: prev/next cycling + position + exit), with
✔️/✖️ marks that are purely visual (never sent to the backend, never
change the text) and persist as a grey badge on the finding even outside
filter mode.

Depends on patch 30 already being applied.

Run from the repo root (same folder as frontend/):
    python apply_patch31.py
"""
from pathlib import Path

INDEX_HTML_PATH = Path("frontend/index.html")
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
    # 1. index.html: new nav bar, sibling of the existing search one
    apply(
        INDEX_HTML_PATH,
        '''                <div id="search-nav-bar" class="search-nav-bar" hidden>
                        <span id="search-nav-query" class="search-nav-query"></span>
                        <button id="search-nav-prev" class="translation-action-icon" type="button" aria-label="Попередній збіг" title="Попередній збіг">‹</button>
                        <span id="search-nav-position" class="search-nav-position"></span>
                        <button id="search-nav-next" class="translation-action-icon" type="button" aria-label="Наступний збіг" title="Наступний збіг">›</button>
                        <button id="search-nav-return" class="secondary-btn" type="button">← Повернутися</button>
                        <button id="search-nav-exit" class="translation-action-icon" type="button" aria-label="Вийти з пошуку" title="Вийти з пошуку">✕</button>
                </div>''',
        '''                <div id="search-nav-bar" class="search-nav-bar" hidden>
                        <span id="search-nav-query" class="search-nav-query"></span>
                        <button id="search-nav-prev" class="translation-action-icon" type="button" aria-label="Попередній збіг" title="Попередній збіг">‹</button>
                        <span id="search-nav-position" class="search-nav-position"></span>
                        <button id="search-nav-next" class="translation-action-icon" type="button" aria-label="Наступний збіг" title="Наступний збіг">›</button>
                        <button id="search-nav-return" class="secondary-btn" type="button">← Повернутися</button>
                        <button id="search-nav-exit" class="translation-action-icon" type="button" aria-label="Вийти з пошуку" title="Вийти з пошуку">✕</button>
                </div>

                <div id="ai-qa-nav-bar" class="search-nav-bar ai-qa-nav-bar" hidden>
                        <button id="ai-qa-nav-prev" class="translation-action-icon" type="button" aria-label="Попередня знахідка" title="Попередня знахідка">‹</button>
                        <span id="ai-qa-nav-position" class="search-nav-position"></span>
                        <div id="ai-qa-nav-content" class="ai-qa-nav-content"></div>
                        <button id="ai-qa-nav-next" class="translation-action-icon" type="button" aria-label="Наступна знахідка" title="Наступна знахідка">›</button>
                        <button id="ai-qa-nav-exit" class="translation-action-icon" type="button" aria-label="Вийти з режиму фільтра" title="Вийти з режиму фільтра">✕</button>
                </div>''',
    )

    # 2. app.js: DOM refs, next to the search-nav ones
    apply(
        APP_JS_PATH,
        '''const searchNavExitButton = document.querySelector('#search-nav-exit');''',
        '''const searchNavExitButton = document.querySelector('#search-nav-exit');
const aiQaNavBar = document.querySelector('#ai-qa-nav-bar');
const aiQaNavPositionLabel = document.querySelector('#ai-qa-nav-position');
const aiQaNavContent = document.querySelector('#ai-qa-nav-content');
const aiQaNavPrevButton = document.querySelector('#ai-qa-nav-prev');
const aiQaNavNextButton = document.querySelector('#ai-qa-nav-next');
const aiQaNavExitButton = document.querySelector('#ai-qa-nav-exit');''',
    )

    # 3. app.js: button wiring, next to the search-nav ones
    apply(
        APP_JS_PATH,
        '''searchNavExitButton.addEventListener('click', exitSearchNavigation);''',
        '''searchNavExitButton.addEventListener('click', exitSearchNavigation);
aiQaNavPrevButton.addEventListener('click', () => stepAiQaFilter(-1));
aiQaNavNextButton.addEventListener('click', () => stepAiQaFilter(1));
aiQaNavExitButton.addEventListener('click', exitAiQaFilter);''',
    )

    # 4. app.js: filter-mode state, next to the other AI QA module state
    apply(
        APP_JS_PATH,
        '''const AI_QA_CATEGORY_LABELS = { critical: 'Критично', stylistic: 'Стилістично', typo: 'Одруківка' };''',
        '''const AI_QA_CATEGORY_LABELS = { critical: 'Критично', stylistic: 'Стилістично', typo: 'Одруківка' };
let aiQaFlatFindings = [];
let aiQaFilterCategory = null;
let aiQaFilterIndex = 0;''',
    )

    # 5. app.js: rewrite renderAiQaResults to build the flat findings list,
    #    tag each finding item with a stable id, and make the counters
    #    clickable (disabled when their count is 0).
    apply(
        APP_JS_PATH,
        '''function renderAiQaResults(result) {
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
}''',
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
}

function startAiQaFilter(category) {
    const list = aiQaFlatFindings.filter((entry) => entry.finding.category === category);
    if (list.length === 0) {
        return;
    }
    aiQaFilterCategory = category;
    aiQaFilterIndex = 0;
    projectWorkspaceView.classList.add('ai-qa-nav-active');
    aiQaNavBar.hidden = false;
    showAiQaFilterItem();
}

function currentAiQaFilterList() {
    return aiQaFlatFindings.filter((entry) => entry.finding.category === aiQaFilterCategory);
}

function stepAiQaFilter(direction) {
    const list = currentAiQaFilterList();
    const nextIndex = aiQaFilterIndex + direction;
    if (nextIndex < 0 || nextIndex >= list.length) {
        return;
    }
    aiQaFilterIndex = nextIndex;
    showAiQaFilterItem();
}

function showAiQaFilterItem() {
    const list = currentAiQaFilterList();
    document.querySelectorAll('.ai-qa-finding-current').forEach((el) => el.classList.remove('ai-qa-finding-current'));
    if (list.length === 0) {
        exitAiQaFilter();
        return;
    }
    if (aiQaFilterIndex >= list.length) {
        aiQaFilterIndex = list.length - 1;
    }
    const entry = list[aiQaFilterIndex];
    const itemEl = translationRows.querySelector(`.ai-qa-finding[data-finding-id="${CSS.escape(entry.findingId)}"]`);
    if (itemEl) {
        itemEl.classList.add('ai-qa-finding-current');
    }
    entry.row.scrollIntoView({ behavior: 'smooth', block: 'center' });

    aiQaNavPositionLabel.textContent = `${aiQaFilterIndex + 1} з ${list.length}`;
    aiQaNavPrevButton.disabled = aiQaFilterIndex <= 0;
    aiQaNavNextButton.disabled = aiQaFilterIndex >= list.length - 1;

    aiQaNavContent.replaceChildren();
    const quote = document.createElement('span');
    quote.className = 'ai-qa-nav-quote';
    quote.textContent = `«${entry.finding.quote}»`;
    const explanation = document.createElement('span');
    explanation.className = 'ai-qa-nav-explanation';
    explanation.textContent = entry.finding.explanation || '';
    aiQaNavContent.append(quote, explanation);
    if (entry.finding.suggestion) {
        const suggestion = document.createElement('span');
        suggestion.className = 'ai-qa-nav-suggestion';
        suggestion.textContent = `→ ${entry.finding.suggestion}`;
        aiQaNavContent.append(suggestion);
    }

    if (entry.finding.mark) {
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
}

function markAiQaFinding(entry, mark) {
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
}

function exitAiQaFilter() {
    aiQaFilterCategory = null;
    aiQaFilterIndex = 0;
    aiQaNavBar.hidden = true;
    projectWorkspaceView.classList.remove('ai-qa-nav-active');
    document.querySelectorAll('.ai-qa-finding-current').forEach((el) => el.classList.remove('ai-qa-finding-current'));
}''',
    )

    # 6. app.js: also exit filter mode when clearing/re-running the check
    apply(
        APP_JS_PATH,
        '''function clearAiQaIssues() {
    translationRows.querySelectorAll('.ai-qa-issues').forEach((panel) => panel.remove());
    aiQaCounters.replaceChildren();
}''',
        '''function clearAiQaIssues() {
    exitAiQaFilter();
    translationRows.querySelectorAll('.ai-qa-issues').forEach((panel) => panel.remove());
    aiQaCounters.replaceChildren();
    aiQaFlatFindings = [];
}''',
    )

    # 7. styles.css: nav bar layout + persistent mark badge + "current" highlight
    apply(
        STYLES_CSS_PATH,
        '''#project-workspace-view.workspace.search-nav-active {
    padding-bottom: 140px;
}''',
        '''#project-workspace-view.workspace.search-nav-active {
    padding-bottom: 140px;
}

#project-workspace-view.workspace.ai-qa-nav-active {
    padding-bottom: 140px;
}

.ai-qa-nav-bar {
    height: auto;
    min-height: 48px;
    padding: 8px 10px;
}

.ai-qa-nav-content {
    flex: 1 1 auto;
    min-width: 0;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 4px 10px;
}

.ai-qa-nav-quote {
    font-weight: 600;
    font-size: 13px;
}

.ai-qa-nav-explanation,
.ai-qa-nav-suggestion {
    font-size: 13px;
    color: var(--color-text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 260px;
}

.ai-qa-nav-mark {
    font-size: 16px;
}

.ai-qa-finding-current .ai-qa-finding-chip {
    outline: 2px solid var(--color-border-accent);
    outline-offset: 1px;
}

.ai-qa-finding-mark-badge {
    margin-left: 6px;
}

.ai-qa-finding-marked .ai-qa-finding-chip {
    background: var(--color-bg-inset);
    border-color: var(--color-border-neutral);
    color: var(--color-text-muted);
}''',
    )

    print("Patch 31 applied successfully.")


if __name__ == "__main__":
    main()
