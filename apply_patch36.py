"""
Patch 36: visual tweak to the AI QA filter nav bar per Катя's feedback —
text block on the left (wraps to 2-3 lines instead of single-line
ellipsis truncation), ✔️/✖️ made smaller and grouped together on the
right side of the text, right before the › button.

Depends on patch 35 already being applied.

Run from the repo root (same folder as frontend/):
    python apply_patch36.py
"""
from pathlib import Path

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
    # 1. app.js: split the content into a wrapping text block + a compact
    #    action-button group, instead of one flat flex-wrap row
    apply(
        APP_JS_PATH,
        '''    aiQaNavContent.replaceChildren();
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

    const accept = document.createElement('button');
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
        '''    aiQaNavContent.replaceChildren();

    const text = document.createElement('div');
    text.className = 'ai-qa-nav-text';
    const quote = document.createElement('span');
    quote.className = 'ai-qa-nav-quote';
    quote.textContent = `«${entry.finding.quote}»`;
    const explanation = document.createElement('span');
    explanation.className = 'ai-qa-nav-explanation';
    explanation.textContent = entry.finding.explanation || '';
    text.append(quote, explanation);
    if (entry.finding.suggestion) {
        const suggestion = document.createElement('span');
        suggestion.className = 'ai-qa-nav-suggestion';
        suggestion.textContent = `→ ${entry.finding.suggestion}`;
        text.append(suggestion);
    }
    aiQaNavContent.append(text);

    const actions = document.createElement('div');
    actions.className = 'ai-qa-nav-actions';
    const accept = document.createElement('button');
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
    actions.append(accept, dismiss);
    aiQaNavContent.append(actions);
}''',
    )

    # 2. styles.css: text wraps (up to 3 lines, ellipsis only past that),
    #    actions become a small, tight group instead of inline-wrapped buttons
    apply(
        STYLES_CSS_PATH,
        '''.ai-qa-nav-content {
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
}''',
        '''.ai-qa-nav-content {
    flex: 1 1 auto;
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 4px 0;
}

.ai-qa-nav-text {
    flex: 1 1 auto;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
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
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    white-space: normal;
}

.ai-qa-nav-actions {
    flex: 0 0 auto;
    display: flex;
    gap: 2px;
}

.ai-qa-nav-actions .icon-btn {
    min-width: 28px;
    padding: 2px 6px;
    font-size: 15px;
}''',
    )

    print("Patch 36 applied successfully.")


if __name__ == "__main__":
    main()
