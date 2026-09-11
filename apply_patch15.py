#!/usr/bin/env python3
"""
apply_patch15.py — Патч 15: виправлення панелі пошукової навігації.

Що виправляє (за скаргами):
1. Панель "Повернутися"/"✕" більше не залипає на екрані назавжди — вона
   автоматично закривається, коли ти повертаєшся до списку проєктів або
   відкриваєш інший проєкт звичайним способом (не через результат
   пошуку). Раніше вона лишалась відкритою, бо очищалась тільки по кліку
   на "✕", а звичайна навігація її не чіпала.
2. Панель перенесена ВНИЗ екрана (туди, де чат з ШІ — сам чат на цей час
   ховається, щоб не накладались). Зліва — слово пошуку, посередині
   ‹ N з M › (стрілки сіріють і вимикаються на першому/останньому збігу),
   праворуч — "Повернутися" і "✕". Цикл ‹› тепер працює для будь-якого
   обсягу пошуку (розділ/проєкт/усі проєкти), а не тільки для розділу.
3. Перехід по кліку на результат пошуку тепер детермінований: замість
   крихкого трюку з setTimeout(0) для очікування довантаження чужого
   проєкту, код явно чекає структуру книги і сам викликає рендер —
   без залежності від порядку мікрозадач у браузері. Це мало б прибрати
   "нічого не відкривається" при переході в інший проєкт. Додатково
   перехід тепер явно відкриває вкладку "Переклад", щоб абзац одразу
   було видно, а не лишався за кадром на вкладці "Інформація про проєкт".

Файли: тільки frontend/index.html, frontend/styles.css, frontend/app.js.
Бекенд не чіпали.

Запусти з кореня репозиторію, ПІСЛЯ apply_patch12-14.py:
    python3 apply_patch15.py

Ідемпотентний: повторний запуск пропустить уже застосоване.

Після застосування — просто onови сторінку в браузері.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

EDITS_JSON = r"""
{"frontend/index.html": [["перебудова панелі: слово зліва, лічильник по центру, кнопки праворуч", "                <div id=\"search-nav-bar\" class=\"search-nav-bar\" hidden>\n                        <span id=\"search-nav-position\" class=\"search-nav-position\"></span>\n                        <div class=\"search-nav-controls\">\n                                <button id=\"search-nav-prev\" class=\"translation-action-icon\" type=\"button\" aria-label=\"Попередній збіг\" title=\"Попередній збіг\">‹</button>\n                                <button id=\"search-nav-next\" class=\"translation-action-icon\" type=\"button\" aria-label=\"Наступний збіг\" title=\"Наступний збіг\">›</button>\n                        </div>\n                        <button id=\"search-nav-return\" class=\"secondary-btn\" type=\"button\">← Повернутися</button>\n                        <button id=\"search-nav-exit\" class=\"translation-action-icon\" type=\"button\" aria-label=\"Вийти з пошуку\" title=\"Вийти з пошуку\">✕</button>\n                </div>", "                <div id=\"search-nav-bar\" class=\"search-nav-bar\" hidden>\n                        <span id=\"search-nav-query\" class=\"search-nav-query\"></span>\n                        <button id=\"search-nav-prev\" class=\"translation-action-icon\" type=\"button\" aria-label=\"Попередній збіг\" title=\"Попередній збіг\">‹</button>\n                        <span id=\"search-nav-position\" class=\"search-nav-position\"></span>\n                        <button id=\"search-nav-next\" class=\"translation-action-icon\" type=\"button\" aria-label=\"Наступний збіг\" title=\"Наступний збіг\">›</button>\n                        <button id=\"search-nav-return\" class=\"secondary-btn\" type=\"button\">← Повернутися</button>\n                        <button id=\"search-nav-exit\" class=\"translation-action-icon\" type=\"button\" aria-label=\"Вийти з пошуку\" title=\"Вийти з пошуку\">✕</button>\n                </div>"], ["бамп версії styles.css", "        <link rel=\"stylesheet\" href=\"/styles.css?v=7\">", "        <link rel=\"stylesheet\" href=\"/styles.css?v=8\">"], ["бамп версії app.js", "        <script src=\"/app.js?v=7\" defer></script>", "        <script src=\"/app.js?v=8\" defer></script>"]], "frontend/styles.css": [["перенести панель пошуку вниз екрана, приховати чат ШІ під час активного пошуку, padding знизу замість зверху", ".search-nav-bar {\n    position: fixed;\n    top: 48px;\n    left: 0;\n    right: 0;\n    z-index: 7;\n    display: flex;\n    align-items: center;\n    gap: 8px;\n    height: 44px;\n    padding: 0 10px;\n    background: var(--color-bg-sticky);\n    border-bottom: 1px solid var(--color-border);\n    backdrop-filter: blur(8px);\n}\n\n.search-nav-position {\n    font-size: 13px;\n    color: var(--color-text-muted);\n    white-space: nowrap;\n    flex-shrink: 0;\n}\n\n.search-nav-controls {\n    display: flex;\n    gap: 4px;\n    flex-shrink: 0;\n}\n\n.search-nav-bar .secondary-btn {\n    margin-left: auto;\n    flex-shrink: 0;\n}\n\n#project-workspace-view.workspace.search-nav-active {\n    padding-top: 110px;\n}", ".search-nav-bar {\n    position: fixed;\n    bottom: 0;\n    left: 0;\n    right: 0;\n    z-index: 16;\n    display: flex;\n    align-items: center;\n    gap: 8px;\n    height: 48px;\n    padding: 0 10px;\n    background: var(--color-bg-sticky);\n    border-top: 1px solid var(--color-border);\n    backdrop-filter: blur(8px);\n}\n\n.search-nav-query {\n    flex: 1 1 auto;\n    min-width: 0;\n    overflow: hidden;\n    text-overflow: ellipsis;\n    white-space: nowrap;\n    font-size: 14px;\n    font-weight: 600;\n}\n\n.search-nav-position {\n    font-size: 13px;\n    color: var(--color-text-muted);\n    white-space: nowrap;\n    flex-shrink: 0;\n}\n\n.search-nav-bar .secondary-btn {\n    flex-shrink: 0;\n}\n\n#project-workspace-view.workspace.search-nav-active {\n    padding-bottom: 140px;\n}\n\n#project-workspace-view.search-nav-active .project-chat-panel {\n    display: none;\n}"]], "frontend/app.js": [["посилання на елемент слова пошуку на нижній панелі", "const searchNavBar = document.querySelector('#search-nav-bar');\nconst searchNavPositionLabel = document.querySelector('#search-nav-position');", "const searchNavBar = document.querySelector('#search-nav-bar');\nconst searchNavQueryLabel = document.querySelector('#search-nav-query');\nconst searchNavPositionLabel = document.querySelector('#search-nav-position');"], ["детермінований перехід між проєктами (без гонки станів), явне відкриття вкладки Переклад, цикл ‹› для будь-якого обсягу пошуку", "    const isDifferentProject = !currentProject || currentProject.projectId !== result.projectId;\n    if (isDifferentProject) {\n        try {\n            const projectPromise = loadProjectDetail(result.projectId);\n            const structurePromise = WorkbenchApi.getProjectBookStructure(result.projectId);\n            const project = await projectPromise;\n            showProjectWorkspace(project, structurePromise);\n            await structurePromise;\n            await new Promise((resolve) => setTimeout(resolve, 0));\n        } catch (error) {\n            window.alert(error.message);\n            return;\n        }\n    }\n    const chapterIndex = loadedChapters.findIndex((chapter) => chapter.chapterId === result.chapterId);\n    if (chapterIndex === -1) {\n        return;\n    }\n    if (selectedChapterIndex !== chapterIndex) {\n        selectChapter(chapterIndex);\n    }\n    if (lastSearchScope === 'chapter') {\n        searchNavResults = lastSearchResults;\n        searchNavIndex = searchNavResults.indexOf(result);\n    } else {\n        searchNavResults = [];\n        searchNavIndex = -1;\n    }\n    showSearchNavBar();\n    closeSearchPanel();\n    highlightSearchResultParagraph(result);\n}", "    const isDifferentProject = !currentProject || currentProject.projectId !== result.projectId;\n    if (isDifferentProject) {\n        try {\n            const projectPromise = loadProjectDetail(result.projectId);\n            const structurePromise = WorkbenchApi.getProjectBookStructure(result.projectId);\n            const project = await projectPromise;\n            showProjectWorkspace(project, structurePromise);\n            const structure = await structurePromise;\n            renderFileDetails(structure);\n        } catch (error) {\n            window.alert(error.message);\n            return;\n        }\n    }\n    const chapterIndex = loadedChapters.findIndex((chapter) => chapter.chapterId === result.chapterId);\n    if (chapterIndex === -1) {\n        return;\n    }\n    if (selectedChapterIndex !== chapterIndex) {\n        selectChapter(chapterIndex);\n    }\n    showTranslationMode();\n    searchNavResults = lastSearchResults;\n    searchNavIndex = searchNavResults.indexOf(result);\n    showSearchNavBar();\n    closeSearchPanel();\n    highlightSearchResultParagraph(result);\n}"], ["показати слово пошуку на нижній панелі", "function showSearchNavBar() {\n    searchNavBar.hidden = false;\n    projectWorkspaceView.classList.add('search-nav-active');\n    updateSearchNavBar();\n}", "function showSearchNavBar() {\n    searchNavBar.hidden = false;\n    searchNavQueryLabel.textContent = lastSearchQuery;\n    projectWorkspaceView.classList.add('search-nav-active');\n    updateSearchNavBar();\n}"], ["той самий детермінований фікс для повернення на попередню позицію", "    if (target.projectId && (!currentProject || currentProject.projectId !== target.projectId)) {\n        try {\n            const projectPromise = loadProjectDetail(target.projectId);\n            const structurePromise = WorkbenchApi.getProjectBookStructure(target.projectId);\n            const project = await projectPromise;\n            showProjectWorkspace(project, structurePromise);\n            await structurePromise;\n            await new Promise((resolve) => setTimeout(resolve, 0));\n        } catch (error) {\n            window.alert(error.message);\n            return;\n        }\n    }", "    if (target.projectId && (!currentProject || currentProject.projectId !== target.projectId)) {\n        try {\n            const projectPromise = loadProjectDetail(target.projectId);\n            const structurePromise = WorkbenchApi.getProjectBookStructure(target.projectId);\n            const project = await projectPromise;\n            showProjectWorkspace(project, structurePromise);\n            const structure = await structurePromise;\n            renderFileDetails(structure);\n        } catch (error) {\n            window.alert(error.message);\n            return;\n        }\n    }"], ["очищення стану пошукової навігації при поверненні до списку проєктів", "function showMainScreen() {\n    projectWorkspaceView.hidden = true;\n    settingsView.hidden = true;\n    mainScreenView.hidden = false;\n    backToProjectsButton.hidden = true;\n    closeBriefDialog();\n    resetProjectChat();\n}", "function showMainScreen() {\n    exitSearchNavigation();\n    projectWorkspaceView.hidden = true;\n    settingsView.hidden = true;\n    mainScreenView.hidden = false;\n    backToProjectsButton.hidden = true;\n    closeBriefDialog();\n    resetProjectChat();\n}"], ["очищення стану пошукової навігації при звичайному відкритті проєкту зі списку", "    const openButton = event.target.closest('[data-action=\"open-project\"]');\n    if (openButton) {\n        try {\n            const projectId = openButton.dataset.projectId;\n            const projectPromise = loadProjectDetail(projectId);\n            const structurePromise = WorkbenchApi.getProjectBookStructure(projectId);\n            const project = await projectPromise;\n            showProjectWorkspace(project, structurePromise);\n        } catch (error) {\n            window.alert(error.message);\n        }\n    }", "    const openButton = event.target.closest('[data-action=\"open-project\"]');\n    if (openButton) {\n        try {\n            exitSearchNavigation();\n            const projectId = openButton.dataset.projectId;\n            const projectPromise = loadProjectDetail(projectId);\n            const structurePromise = WorkbenchApi.getProjectBookStructure(projectId);\n            const project = await projectPromise;\n            showProjectWorkspace(project, structurePromise);\n        } catch (error) {\n            window.alert(error.message);\n        }\n    }"]]}"""


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
                print("   Очікуваний фрагмент коду не знайдено — чи точно застосовані попередні патчі (12-14) перед цим?")
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
    print("Готово. Онови сторінку в браузері — бекенд не чіпали, рестарт не потрібен.")


if __name__ == "__main__":
    main()
