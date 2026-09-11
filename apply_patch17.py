#!/usr/bin/env python3
"""
apply_patch17.py — Патч 17: панель дійсно ховається + видно номер розділу.

Що виправляє:
1. frontend/styles.css — .search-nav-bar встановлював display:flex без
   жодного правила для атрибута [hidden]. Коли одночасно є HTML-атрибут
   hidden і авторський CSS-клас без урахування [hidden], браузер віддає
   перевагу авторському CSS над стандартним "[hidden] { display: none }" —
   тому JS (searchNavBar.hidden = true) технічно спрацьовував, але
   візуально нічого не ховав. Панель лишалась видимою назавжди після
   першого показу. Додано .search-nav-bar[hidden] { display: none; } —
   той самий патерн, який уже використовується для інших діалогів у
   файлі (.new-project-dialog[hidden] тощо).
2. frontend/app.js — і в списку результатів, і на нижній панелі поруч
   із назвою розділу тепер показується його номер (той самий, що у
   стрічці "Розділи": 01, 02...). % — це позиція ВСЕРЕДИНІ розділу
   (другий рівень сортування), не наскрізна по книзі, тому сам собою
   він не показує загальний порядок — а номер розділу показує.

Файли: frontend/index.html (бамп версій), frontend/styles.css,
frontend/app.js. Бекенд не чіпали.

Запусти з кореня репозиторію, ПІСЛЯ apply_patch12-16.py:
    python3 apply_patch17.py

Ідемпотентний: повторний запуск пропустить уже застосоване.

Після застосування — просто onови сторінку в браузері.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

EDITS_JSON = r"""
{"frontend/index.html": [["бамп версії styles.css", "        <link rel=\"stylesheet\" href=\"/styles.css?v=9\">", "        <link rel=\"stylesheet\" href=\"/styles.css?v=10\">"], ["бамп версії app.js", "        <script src=\"/app.js?v=9\" defer></script>", "        <script src=\"/app.js?v=10\" defer></script>"]], "frontend/styles.css": [["справжній фікс: явне правило [hidden] для .search-nav-bar (без нього JS-приховування не діяло)", ".search-nav-bar {\n    position: fixed;\n    bottom: 0;\n    left: 0;\n    right: 0;\n    z-index: 16;\n    display: flex;\n    align-items: center;\n    gap: 8px;\n    height: 48px;\n    padding: 0 10px;\n    background: var(--color-bg-sticky);\n    border-top: 1px solid var(--color-border);\n    backdrop-filter: blur(8px);\n}", ".search-nav-bar {\n    position: fixed;\n    bottom: 0;\n    left: 0;\n    right: 0;\n    z-index: 16;\n    display: flex;\n    align-items: center;\n    gap: 8px;\n    height: 48px;\n    padding: 0 10px;\n    background: var(--color-bg-sticky);\n    border-top: 1px solid var(--color-border);\n    backdrop-filter: blur(8px);\n}\n\n.search-nav-bar[hidden] {\n    display: none;\n}"]], "frontend/app.js": [["показати номер розділу (як у стрічці Розділи) у списку результатів пошуку", "        meta.textContent = `${item.projectTitle} · ${item.chapterTitle} · ${item.positionPercent}%`;", "        meta.textContent = `${item.projectTitle} · ${String(item.chapterIndex + 1).padStart(2, '0')} · ${item.chapterTitle} · ${item.positionPercent}%`;"], ["показати номер розділу на нижній панелі пошуку", "        const chapterInfo = current ? ` · ${current.chapterTitle} · ${current.positionPercent}%` : '';", "        const chapterInfo = current ? ` · ${String(current.chapterIndex + 1).padStart(2, '0')} · ${current.chapterTitle} · ${current.positionPercent}%` : '';"]]}"""


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
                print("   Очікуваний фрагмент коду не знайдено — чи точно застосовані попередні патчі (12-16) перед цим?")
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
