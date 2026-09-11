#!/usr/bin/env python3
"""
apply_patch16.py — Патч 16: порядок ‹›-переходів по книзі + розділ/% на панелі.

Що виправляє:
1. backend/storage.py — результати пошуку сортувались за релевантністю
   FTS (bm25), тому кнопки ‹› стрибали не по порядку читання (могли йти
   "з кінця книги до початку" всупереч номерам розділів). Тепер
   сортування за фактичною позицією в книзі: проєкт → розділ → абзац.
   ПОТРІБЕН РЕСТАРТ БЕКЕНДУ.
2. frontend/app.js + styles.css — на нижній панелі пошуку поруч із
   лічильником "N з M" тепер показується назва розділу і % позиції в
   ньому (те саме, що й у списку результатів), з обрізанням "…", якщо
   не вміщується.

Файли: backend/storage.py, frontend/index.html, frontend/styles.css,
frontend/app.js.

Запусти з кореня репозиторію, ПІСЛЯ apply_patch12-15.py:
    python3 apply_patch16.py

Ідемпотентний: повторний запуск пропустить уже застосоване.

Після застосування: backend/storage.py змінився — перезапусти процес
Workbench, щоб новий порядок сортування підхопився. Фронтенд — просто
onови сторінку.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

EDITS_JSON = r"""
{"backend/storage.py": [["сортувати результати пошуку за позицією в книзі (проєкт → розділ → абзац), а не за релевантністю FTS — щоб ‹ › рухались по порядку читання", "                \"ORDER BY rank LIMIT ? OFFSET ?\",", "                \"ORDER BY proj.title, ch.chapter_index, bp.paragraph_index LIMIT ? OFFSET ?\","]], "frontend/index.html": [["бамп версії styles.css", "        <link rel=\"stylesheet\" href=\"/styles.css?v=8\">", "        <link rel=\"stylesheet\" href=\"/styles.css?v=9\">"], ["бамп версії app.js", "        <script src=\"/app.js?v=8\" defer></script>", "        <script src=\"/app.js?v=9\" defer></script>"]], "frontend/styles.css": [["query/position labels: query бере обмежену ширину, лічильник+розділ+% розтягується з обрізанням", ".search-nav-query {\n    flex: 1 1 auto;\n    min-width: 0;\n    overflow: hidden;\n    text-overflow: ellipsis;\n    white-space: nowrap;\n    font-size: 14px;\n    font-weight: 600;\n}\n\n.search-nav-position {\n    font-size: 13px;\n    color: var(--color-text-muted);\n    white-space: nowrap;\n    flex-shrink: 0;\n}", ".search-nav-query {\n    flex: 0 1 auto;\n    max-width: 30%;\n    min-width: 0;\n    overflow: hidden;\n    text-overflow: ellipsis;\n    white-space: nowrap;\n    font-size: 14px;\n    font-weight: 600;\n}\n\n.search-nav-position {\n    flex: 1 1 auto;\n    min-width: 0;\n    overflow: hidden;\n    text-overflow: ellipsis;\n    white-space: nowrap;\n    font-size: 13px;\n    color: var(--color-text-muted);\n}"]], "frontend/app.js": [["показати назву розділу і % на панелі поруч з лічильником", "function updateSearchNavBar() {\n    const hasCycling = searchNavResults.length > 0;\n    searchNavPrevButton.hidden = !hasCycling;\n    searchNavNextButton.hidden = !hasCycling;\n    searchNavPositionLabel.textContent = hasCycling ? `${searchNavIndex + 1} з ${searchNavResults.length}` : '';\n    searchNavPrevButton.disabled = !hasCycling || searchNavIndex <= 0;\n    searchNavNextButton.disabled = !hasCycling || searchNavIndex >= searchNavResults.length - 1;\n}", "function updateSearchNavBar() {\n    const hasCycling = searchNavResults.length > 0;\n    searchNavPrevButton.hidden = !hasCycling;\n    searchNavNextButton.hidden = !hasCycling;\n    if (hasCycling) {\n        const current = searchNavResults[searchNavIndex];\n        const chapterInfo = current ? ` · ${current.chapterTitle} · ${current.positionPercent}%` : '';\n        searchNavPositionLabel.textContent = `${searchNavIndex + 1} з ${searchNavResults.length}${chapterInfo}`;\n    } else {\n        searchNavPositionLabel.textContent = '';\n    }\n    searchNavPrevButton.disabled = !hasCycling || searchNavIndex <= 0;\n    searchNavNextButton.disabled = !hasCycling || searchNavIndex >= searchNavResults.length - 1;\n}"]]}"""


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
                print("   Очікуваний фрагмент коду не знайдено — чи точно застосовані попередні патчі (12-15) перед цим?")
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
    print("Бекенд: перезапусти процес (змінився storage.py).")
    print("Фронтенд: просто онови сторінку.")


if __name__ == "__main__":
    main()
