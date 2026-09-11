#!/usr/bin/env python3
"""
apply_patch13.py — Патч 13: панель результатів пошуку (UI до /api/search з патчу 12).

Що робить:
1. frontend/api.js    — WorkbenchApi.search(query, {scope, chapterId, projectId,
                         limit, offset}) — тонка обгортка над GET /api/search.
2. frontend/index.html — модальний діалог #search-dialog: інпут, перемикач
                         Розділ/Проєкт/Усі проєкти, список результатів.
                         Бамп ?v= для styles.css/api.js/app.js, щоб браузер
                         підхопив нові версії файлів.
3. frontend/styles.css — стилі діалогу, перемикача scope, картки результату,
                         підсвітка знайденого слова (<mark>) і коротка
                         флеш-анімація на абзаці після переходу.
4. frontend/app.js     — вся логіка: відкриття/закриття діалогу (Esc теж
                         закриває), дебаунс 300мс на ввід, вимкнення
                         недоступних scope (Розділ — якщо розділ не обраний,
                         Проєкт — якщо проєкт не відкрито), рендер результатів,
                         і навігація по кліку: перемикає проєкт (якщо треба),
                         розділ, скролить і на 2с підсвічує потрібний абзац.

Запусти з кореня репозиторію (там, де лежать backend/ і frontend/), ПІСЛЯ
apply_patch12.py — цей патч редагує ті самі файли, що й дванадцятий:
    python3 apply_patch13.py

Скрипт ідемпотентний: якщо частину патчу вже застосовано — пропустить
готове. Якщо очікуваний фрагмент коду не знайдено (наприклад, patch12 ще
не застосовано, або файл відрізняється) — зупиниться з поясненням і
НІЧОГО не запише.

Після застосування — просто onови сторінку в браузері (бекенд не чіпали,
рестарт не потрібен).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

EDITS_JSON = r"""
{"frontend/api.js": [["метод search() у WorkbenchApi", "    getProjectBookStructure(projectId) {\n        return this.request(`/api/projects/${encodeURIComponent(projectId)}/book/structure`);\n    },", "    getProjectBookStructure(projectId) {\n        return this.request(`/api/projects/${encodeURIComponent(projectId)}/book/structure`);\n    },\n\n    search(query, { scope = 'all', chapterId, projectId, limit, offset } = {}) {\n        const params = new URLSearchParams({ q: query, scope });\n        if (chapterId) params.set('chapterId', chapterId);\n        if (projectId) params.set('projectId', projectId);\n        if (limit) params.set('limit', String(limit));\n        if (offset) params.set('offset', String(offset));\n        return this.request(`/api/search?${params.toString()}`);\n    },"]], "frontend/index.html": [["розмітка діалогу пошуку", "        <script src=\"/api.js?v=4\" defer></script>\n        <script src=\"/app.js?v=5\" defer></script>\n</body>\n</html>", "        <div id=\"search-dialog\" class=\"new-project-dialog\" hidden>\n                <div class=\"new-project-dialog-content search-dialog-content\" role=\"dialog\" aria-modal=\"true\" aria-labelledby=\"search-dialog-title\">\n                        <div class=\"dialog-header\">\n                                <div>\n                                        <p class=\"project-label\">Пошук</p>\n                                        <h2 id=\"search-dialog-title\">Пошук по перекладу</h2>\n                                </div>\n                                <button id=\"close-search-dialog\" class=\"icon-btn\" type=\"button\" aria-label=\"Закрити пошук\">×</button>\n                        </div>\n                        <input id=\"search-input\" type=\"search\" class=\"search-input\" placeholder=\"Слово або фраза українською чи англійською…\">\n                        <div id=\"search-scope-toggle\" class=\"search-scope-toggle\" role=\"radiogroup\" aria-label=\"Область пошуку\">\n                                <button type=\"button\" class=\"search-scope-button active\" data-scope=\"chapter\">Розділ</button>\n                                <button type=\"button\" class=\"search-scope-button\" data-scope=\"project\">Проєкт</button>\n                                <button type=\"button\" class=\"search-scope-button\" data-scope=\"all\">Усі проєкти</button>\n                        </div>\n                        <div id=\"search-results\" class=\"search-results\">\n                                <p class=\"muted\">Введіть текст для пошуку.</p>\n                        </div>\n                </div>\n        </div>\n\n        <script src=\"/api.js?v=5\" defer></script>\n        <script src=\"/app.js?v=6\" defer></script>\n</body>\n</html>"], ["бамп версії styles.css у head", "        <link rel=\"stylesheet\" href=\"/styles.css?v=5\">", "        <link rel=\"stylesheet\" href=\"/styles.css?v=6\">"]], "frontend/styles.css": [["стилі діалогу пошуку (інпут, перемикач scope, результати, підсвітка)", ".icon-btn:hover {\n    color: var(--color-text-primary);\n}", ".icon-btn:hover {\n    color: var(--color-text-primary);\n}\n\n.search-dialog-content {\n    display: flex;\n    flex-direction: column;\n    gap: 14px;\n    max-height: min(85vh, 720px);\n}\n\n.search-input {\n    width: 100%;\n    padding: 10px 12px;\n    border-radius: 8px;\n    border: 1px solid var(--color-border-strong);\n    background: var(--color-bg-elevated);\n    color: var(--color-text-primary);\n    font-size: 15px;\n}\n\n.search-scope-toggle {\n    display: flex;\n    gap: 6px;\n}\n\n.search-scope-button {\n    flex: 1 1 0;\n    background: var(--color-bg-elevated);\n    color: var(--color-text-secondary);\n    border: 1px solid var(--color-border);\n    padding: 8px 10px;\n    font-size: 13px;\n    border-radius: 8px;\n}\n\n.search-scope-button.active {\n    background: var(--color-success);\n    color: var(--color-text-on-accent);\n    border-color: var(--color-success);\n}\n\n.search-scope-button:disabled {\n    opacity: 0.5;\n    cursor: not-allowed;\n}\n\n.search-results {\n    overflow-y: auto;\n    display: grid;\n    gap: 8px;\n    padding-right: 2px;\n}\n\n.search-result-item {\n    display: block;\n    width: 100%;\n    text-align: left;\n    padding: 10px 12px;\n    background: var(--color-bg-surface);\n    border: 1px solid var(--color-border);\n    border-radius: 8px;\n    color: var(--color-text-primary);\n}\n\n.search-result-item:hover {\n    background: var(--color-bg-hover);\n}\n\n.search-result-meta {\n    margin-bottom: 4px;\n    font-size: 12px;\n    color: var(--color-text-muted);\n}\n\n.search-result-snippet mark {\n    background: rgba(255, 193, 7, 0.45);\n    color: inherit;\n    border-radius: 2px;\n    padding: 0 2px;\n}\n\n@keyframes search-result-flash {\n    from { background: var(--color-bg-highlight); }\n    to { background: transparent; }\n}\n\n.search-result-highlight {\n    animation: search-result-flash 2s ease-out;\n}"]], "frontend/app.js": [["посилання на елементи діалогу пошуку", "const quickActionsProjectTitle = document.querySelector('#quick-actions-project-title');\nconst openSearchButton = document.querySelector('#open-search');", "const quickActionsProjectTitle = document.querySelector('#quick-actions-project-title');\nconst openSearchButton = document.querySelector('#open-search');\nconst searchDialog = document.querySelector('#search-dialog');\nconst closeSearchDialogButton = document.querySelector('#close-search-dialog');\nconst searchInput = document.querySelector('#search-input');\nconst searchScopeToggle = document.querySelector('#search-scope-toggle');\nconst searchResultsContainer = document.querySelector('#search-results');"], ["стан для пошуку", "let currentProject = null;", "let currentProject = null;\nlet currentSearchScope = 'chapter';\nlet searchDebounceTimer = null;\nlet searchRequestToken = 0;"], ["заміна заглушки кнопки пошуку на повну логіку панелі (відкриття, scope, дебаунс, рендер результатів, навігація)", "undoTranslationButton.addEventListener('click', undoTranslation);\nredoTranslationButton.addEventListener('click', redoTranslation);\n// TODO: замінити на реальне відкриття панелі пошуку (наступний патч)\nopenSearchButton.addEventListener('click', () => {\n    console.log('Пошук: панель ще не підключена.');\n});", "undoTranslationButton.addEventListener('click', undoTranslation);\nredoTranslationButton.addEventListener('click', redoTranslation);\nopenSearchButton.addEventListener('click', openSearchPanel);\ncloseSearchDialogButton.addEventListener('click', closeSearchPanel);\nsearchInput.addEventListener('input', () => {\n    clearTimeout(searchDebounceTimer);\n    searchDebounceTimer = setTimeout(() => { void runSearch(); }, 300);\n});\nsearchScopeToggle.addEventListener('click', (event) => {\n    const button = event.target.closest('.search-scope-button');\n    if (button && !button.disabled) {\n        setSearchScope(button.dataset.scope);\n    }\n});\ndocument.addEventListener('keydown', (event) => {\n    if (event.key === 'Escape' && !searchDialog.hidden) {\n        closeSearchPanel();\n    }\n});\n\nfunction openSearchPanel() {\n    searchDialog.hidden = false;\n    updateSearchScopeAvailability();\n    searchInput.value = '';\n    renderSearchPlaceholder('Введіть текст для пошуку.');\n    searchInput.focus();\n}\n\nfunction closeSearchPanel() {\n    searchDialog.hidden = true;\n    clearTimeout(searchDebounceTimer);\n}\n\nfunction renderSearchPlaceholder(text) {\n    const placeholder = document.createElement('p');\n    placeholder.className = 'muted';\n    placeholder.textContent = text;\n    searchResultsContainer.replaceChildren(placeholder);\n}\n\nfunction updateSearchScopeAvailability() {\n    const chapterButton = searchScopeToggle.querySelector('[data-scope=\"chapter\"]');\n    const projectButton = searchScopeToggle.querySelector('[data-scope=\"project\"]');\n    if (chapterButton) {\n        chapterButton.disabled = selectedChapterIndex === null;\n    }\n    if (projectButton) {\n        projectButton.disabled = !currentProject;\n    }\n    if (\n        (currentSearchScope === 'chapter' && selectedChapterIndex === null)\n        || (currentSearchScope === 'project' && !currentProject)\n    ) {\n        setSearchScope('all');\n    } else {\n        setSearchScope(currentSearchScope, { rerun: false });\n    }\n}\n\nfunction setSearchScope(scope, { rerun = true } = {}) {\n    currentSearchScope = scope;\n    searchScopeToggle.querySelectorAll('.search-scope-button').forEach((button) => {\n        button.classList.toggle('active', button.dataset.scope === scope);\n    });\n    if (rerun && searchInput.value.trim()) {\n        void runSearch();\n    }\n}\n\nasync function runSearch() {\n    const query = searchInput.value.trim();\n    if (!query) {\n        renderSearchPlaceholder('Введіть текст для пошуку.');\n        return;\n    }\n    const requestToken = ++searchRequestToken;\n    renderSearchPlaceholder('Шукаю…');\n    try {\n        const params = { scope: currentSearchScope };\n        if (currentSearchScope === 'chapter' && selectedChapterIndex !== null) {\n            params.chapterId = loadedChapters[selectedChapterIndex]?.chapterId;\n        }\n        if (currentSearchScope === 'project' && currentProject) {\n            params.projectId = currentProject.projectId;\n        }\n        const result = await WorkbenchApi.search(query, params);\n        if (requestToken !== searchRequestToken) {\n            return;\n        }\n        renderSearchResults(result);\n    } catch (error) {\n        if (requestToken !== searchRequestToken) {\n            return;\n        }\n        renderSearchPlaceholder(error.message);\n    }\n}\n\nfunction highlightSnippet(snippet) {\n    const escaped = escapeRichText(String(snippet ?? ''));\n    return escaped.replaceAll('⟦', '<mark>').replaceAll('⟧', '</mark>');\n}\n\nfunction renderSearchResults(result) {\n    const results = result?.results || [];\n    if (results.length === 0) {\n        renderSearchPlaceholder('Нічого не знайдено.');\n        return;\n    }\n    searchResultsContainer.replaceChildren();\n    results.forEach((item) => {\n        const button = document.createElement('button');\n        button.type = 'button';\n        button.className = 'search-result-item';\n\n        const meta = document.createElement('div');\n        meta.className = 'search-result-meta';\n        meta.textContent = `${item.projectTitle} · ${item.chapterTitle} · ${item.positionPercent}%`;\n\n        const snippet = document.createElement('div');\n        snippet.className = 'search-result-snippet';\n        snippet.innerHTML = highlightSnippet(item.snippet);\n\n        button.append(meta, snippet);\n        button.addEventListener('click', () => { void navigateToSearchResult(item); });\n        searchResultsContainer.append(button);\n    });\n}\n\nasync function navigateToSearchResult(result) {\n    const isDifferentProject = !currentProject || currentProject.projectId !== result.projectId;\n    if (isDifferentProject) {\n        try {\n            const projectPromise = loadProjectDetail(result.projectId);\n            const structurePromise = WorkbenchApi.getProjectBookStructure(result.projectId);\n            const project = await projectPromise;\n            showProjectWorkspace(project, structurePromise);\n            await structurePromise;\n            await new Promise((resolve) => setTimeout(resolve, 0));\n        } catch (error) {\n            window.alert(error.message);\n            return;\n        }\n    }\n    const chapterIndex = loadedChapters.findIndex((chapter) => chapter.chapterId === result.chapterId);\n    if (chapterIndex === -1) {\n        return;\n    }\n    if (selectedChapterIndex !== chapterIndex) {\n        selectChapter(chapterIndex);\n    }\n    closeSearchPanel();\n    highlightSearchResultParagraph(result.paragraphId);\n}\n\nfunction highlightSearchResultParagraph(paragraphId) {\n    const row = translationRows.querySelector(`.translation-row[data-paragraph-id=\"${CSS.escape(paragraphId)}\"]`);\n    if (!row) {\n        return;\n    }\n    row.scrollIntoView({ behavior: 'smooth', block: 'center' });\n    row.classList.add('search-result-highlight');\n    setTimeout(() => row.classList.remove('search-result-highlight'), 2000);\n}"]]}"""


def patch_file(rel_path, edits):
    path = ROOT / rel_path
    if not path.exists():
        print(f"❌ Не знайдено файл: {rel_path} (запускаєш скрипт не з кореня репозиторію?)")
        sys.exit(1)

    text = path.read_text(encoding="utf-8")
    original_text = text
    for description, old, new in edits:
        if new in text:
            print(f"↷ {rel_path}: «{description}» вже застосовано — пропускаю")
            continue
        count = text.count(old)
        if count != 1:
            print(f"❌ {rel_path}: не можу застосувати «{description}»")
            if count == 0:
                print("   Очікуваний фрагмент коду не знайдено — чи точно застосовано apply_patch12.py перед цим?")
                print("   Нічого не змінено.")
            else:
                print(f"   Фрагмент зустрічається {count} разів (очікувався 1) — неоднозначно.")
                print("   Нічого не змінено.")
            sys.exit(1)
        text = text.replace(old, new, 1)
        print(f"✓ {rel_path}: {description}")

    if text != original_text:
        path.write_text(text, encoding="utf-8")


def main():
    all_edits = json.loads(EDITS_JSON)
    for rel_path, edits in all_edits.items():
        patch_file(rel_path, edits)

    print()
    print("Готово.")
    print("Онови сторінку в браузері — бекенд не чіпали, рестарт не потрібен.")


if __name__ == "__main__":
    main()
