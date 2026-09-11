#!/usr/bin/env python3
"""
apply_patch18.py — Патч 18: повернути кнопку "До проєктів" (регрес з патчу 12).

Що виправляє:
Патч 12 ховав УВЕСЬ .topbar всередині проєкту (щоб він не накладався на
нову панель дій зверху). Але кнопка "← До проєктів" (#back-to-projects)
фізично лежала саме в .topbar — тому вона теж зникала, і єдиним способом
вийти зі списку проєктів, поки ти в робочому просторі, лишався
"неможливий" клік по невидимій кнопці. Це і зловив e2e-тест
"Manual upload → cover changed" — він падав з таймаутом саме на кліку
по #back-to-projects.

Виправлення: та сама кнопка (той самий id, той самий обробник у app.js —
JS-код тут НЕ змінювався) перенесена в завжди видиму панель дій
(#quick-actions-bar), як перша кнопка зліва, іконкою "←". Ні app.js,
ні styles.css чіпати не довелось — .translation-action-icon вже описаний.

Файли: тільки frontend/index.html. Бекенд не чіпали.

Запусти з кореня репозиторію, ПІСЛЯ apply_patch12-17.py:
    python3 apply_patch18.py

Ідемпотентний: повторний запуск пропустить уже застосоване.

Після застосування — просто onови сторінку в браузері.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

EDITS_JSON = r"""
{"frontend/index.html": [["прибрати кнопку 'До проєктів' з topbar (він ховається всередині проєкту разом з нею)", "                <div class=\"topbar-actions\">\n                        <button id=\"back-to-projects\" class=\"secondary-btn\" type=\"button\" hidden>← До проєктів</button>\n                        <div class=\"version\">MVP v1.0</div>\n                </div>", "                <div class=\"topbar-actions\">\n                        <div class=\"version\">MVP v1.0</div>\n                </div>"], ["перенести ту саму кнопку 'До проєктів' (той самий id) у завжди видиму панель дій", "                <div id=\"quick-actions-bar\" class=\"quick-actions-bar\">\n                        <span id=\"quick-actions-project-title\" class=\"quick-actions-title\"></span>", "                <div id=\"quick-actions-bar\" class=\"quick-actions-bar\">\n                        <button id=\"back-to-projects\" class=\"translation-action-icon\" type=\"button\" hidden aria-label=\"До проєктів\" title=\"До проєктів\">←</button>\n                        <span id=\"quick-actions-project-title\" class=\"quick-actions-title\"></span>"]]}"""


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
                print("   Очікуваний фрагмент коду не знайдено — чи точно застосовані попередні патчі (12-17) перед цим?")
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
