"""Patch 46 — QA AI as a submode tab inside "Переклад".

Run from the repo root: python apply_patch46.py

Requires patches 44 and 45 already applied.

What this does:
1. frontend/index.html
   - new "QA AI" button alongside Інформація/Правила/Структуровані
     правила/Глосарій in #project-submode-navigation
   - new empty `#translation-qa-content` panel (a translation-submode-content
     div, same pattern as the others) — filled dynamically by app.js, same
     as `#translation-information-content`
2. frontend/app.js
   - new `translationQaContent` element reference
   - `showTranslationSubmode` gains the 'QA AI' case
   - the existing AI-QA control cluster (model checkboxes, "AI QA"
     button, status line, "Скинути AI QA", counters, and patch 45's
     "Прогнати вибрані") now gets appended into `#translation-qa-content`
     instead of being chained after the gender-agreement button inside
     the chapter view. Nothing about their behavior changes — this is a
     structural move only. `checkGenderAgreementButton` / `genderAgreementStatus`
     (the separate, non-AI check) stay exactly where they were, in the
     chapter view's action row.

Per-paragraph AI QA finding panels (the little highlighted-issue chips
under each translation row) are unaffected — those attach to
`translation-rows` regardless of where the control panel lives.

The QA AI tab still only makes sense once a chapter is selected in the
chapter browser below it, same as Правила/Глосарій already only make
sense once a project is loaded — the chapter browser itself is not
submode-gated, so it stays visible under whichever submode tab is active.

Mode 1's actual batch-stepping UI (Next / Repeat this batch / Cancel,
with resumable progress) is a separate follow-up patch — this one only
gives it a proper home.
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


def patch_html() -> None:
    path = REPO_ROOT / "frontend" / "index.html"

    replace_once(
        path,
        '''                <nav id="project-submode-navigation" class="project-submode-navigation" aria-label="Розділи режиму" hidden>
                        <button class="project-submode-navigation-button" type="button">Інформація</button>
                        <button class="project-submode-navigation-button" type="button">Правила</button>
                        <button class="project-submode-navigation-button" type="button">Структуровані правила</button>
                        <button class="project-submode-navigation-button" type="button">Глосарій</button>
                </nav>''',
        '''                <nav id="project-submode-navigation" class="project-submode-navigation" aria-label="Розділи режиму" hidden>
                        <button class="project-submode-navigation-button" type="button">Інформація</button>
                        <button class="project-submode-navigation-button" type="button">Правила</button>
                        <button class="project-submode-navigation-button" type="button">Структуровані правила</button>
                        <button class="project-submode-navigation-button" type="button">Глосарій</button>
                        <button class="project-submode-navigation-button" type="button">QA AI</button>
                </nav>''',
    )

    replace_once(
        path,
        '''                                </section>
                        </div>
                        <div id="workspace-content">''',
        '''                                </section>
                                <div id="translation-qa-content" class="translation-qa translation-submode-content"></div>
                        </div>
                        <div id="workspace-content">''',
    )

    print(f"index.html patched: {path}")


def patch_app() -> None:
    path = REPO_ROOT / "frontend" / "app.js"

    # New element reference, declared alongside the other submode content consts
    replace_once(
        path,
        '''const translationGlossaryContent = document.querySelector('#translation-glossary-content');''',
        '''const translationGlossaryContent = document.querySelector('#translation-glossary-content');
const translationQaContent = document.querySelector('#translation-qa-content');''',
    )

    # showTranslationSubmode: add the 'QA AI' case
    replace_once(
        path,
        '''function showTranslationSubmode(submode) {
    translationInformationContent.hidden = submode !== 'Інформація';
    translationRulesContent.hidden = submode !== 'Правила';
    translationStructuredRulesContent.hidden = submode !== 'Структуровані правила';
    translationGlossaryContent.hidden = submode !== 'Глосарій';
    translationGlossaryEditor.hidden = submode !== 'Глосарій';
}''',
        '''function showTranslationSubmode(submode) {
    translationInformationContent.hidden = submode !== 'Інформація';
    translationRulesContent.hidden = submode !== 'Правила';
    translationStructuredRulesContent.hidden = submode !== 'Структуровані правила';
    translationGlossaryContent.hidden = submode !== 'Глосарій';
    translationGlossaryEditor.hidden = submode !== 'Глосарій';
    translationQaContent.hidden = submode !== 'QA AI';
}''',
    )

    # Relocate the AI-QA control cluster's anchor point: it used to chain off
    # genderAgreementStatus (inside the chapter view's action row); now it
    # roots into the new QA AI submode panel instead. Everything after this
    # first element in the cluster still chains via insertAdjacentElement
    # onto its own previous sibling, so only this one anchor needs to change.
    replace_once(
        path,
        '''const aiQaConnections = document.createElement('div');
aiQaConnections.className = 'ai-qa-connections';
aiQaConnections.id = 'ai-qa-connections';
genderAgreementStatus.insertAdjacentElement('afterend', aiQaConnections);''',
        '''const aiQaConnections = document.createElement('div');
aiQaConnections.className = 'ai-qa-connections';
aiQaConnections.id = 'ai-qa-connections';
translationQaContent.append(aiQaConnections);''',
    )

    print(f"app.js patched: {path}")


if __name__ == "__main__":
    patch_html()
    patch_app()
    print("Patch 46 applied.")
