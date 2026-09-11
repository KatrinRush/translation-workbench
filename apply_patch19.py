#!/usr/bin/env python3
"""
apply_patch19.py — Патч 19: 502 при перекладі абзацу через контекст для DeepL.

Причина (знайдено в логах /api/logs, [DEEPL DEBUG] context=...):
backend/translations/context.py розбиває сусідній абзац на речення по
крапках/знаках оклику, зовсім не знаючи про вбудовані rich-text теги
(<i>, <b>, <s>). Якщо один такий тег огортає ОДРАЗУ КІЛЬКА речень
(наприклад, курсивом виділено 3-5 речень поспіль, як у "She's a human.
... She's all mine." одним <i>...</i>), розбивка на речення ріже
всередині цього тега. Кожен окремий "уламок"-речення лишається з
непарним тегом:
    "<i>She's a human."       — відкрито, не закрито
    "She's all mine</i>."     — закрито, не відкрито
Коли білдер контексту бере "останні 3 речення перед абзацом" і в цю
трійку потрапляє такий уламок — DeepL отримує невалідний XML (з
tag_handling='xml') і повертає помилку, яку сервер не розпарсив як
JSON → "Workbench повернув відповідь без JSON (HTTP 502)".

Виправлення: прибирати HTML-теги з тексту абзацу ПЕРЕД розбиттям на
речення для контексту. Сам контекст для DeepL — це підказка про сенс
навколишнього тексту, форматування йому не потрібне; переклад
абзацу, що зараз редагується, ця зміна ніяк не чіпає.

Файли: тільки backend/translations/context.py.

Запусти з кореня репозиторію:
    python3 apply_patch19.py

Ідемпотентний: повторний запуск пропустить уже застосоване.

ПОТРІБЕН РЕСТАРТ БЕКЕНДУ (backend/translations/context.py змінився).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

EDITS_JSON = r"""
{"backend/translations/context.py": [["додати функцію очищення HTML-тегів перед розбиттям на речення", "_CLOSING_PUNCTUATION = \"\\\"')]}\"\n_ABBREVIATIONS = {\"mr\", \"mrs\", \"ms\", \"dr\", \"prof\", \"sr\", \"jr\", \"st\", \"etc\", \"e.g\", \"i.e\"}", "_CLOSING_PUNCTUATION = \"\\\"')]}\"\n_ABBREVIATIONS = {\"mr\", \"mrs\", \"ms\", \"dr\", \"prof\", \"sr\", \"jr\", \"st\", \"etc\", \"e.g\", \"i.e\"}\n_TAG_RE = re.compile(r\"<[^>]+>\")\n\n\ndef _strip_tags(text: str) -> str:\n    \"\"\"Remove inline rich-text tags (<i>, </b>, <s>...) before sentence splitting.\n\n    DeepL context is plain guidance text, not rendered output — it doesn't\n    need formatting. Splitting on tag-containing text is what produced\n    orphaned opening/closing tags when a single <i>...</i> run spanned\n    several sentences (the sentence boundary lands *inside* the tag pair).\n    \"\"\"\n    return _TAG_RE.sub(\"\", text)"], ["прибирати теги з original_text перед розбиттям на речення (сама причина 502 на DeepL)", "            if element.get(\"isService\", False):\n                continue\n            paragraph_sentences = _sentences(original_text)", "            if element.get(\"isService\", False):\n                continue\n            paragraph_sentences = _sentences(_strip_tags(original_text))"]]}"""


def patch_file(rel_path, edits):
    path = ROOT / rel_path
    if not path.exists():
        print(f"❌ Не знайдено файл: {rel_path} (запускаєш скрипт не з кореня репозиторію? або файл лежить в іншому місці, ніж backend/translations/context.py?)")
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
                print("   Очікуваний фрагмент коду не знайдено — файл, схоже, відрізняється від очікуваного. Нічого не змінено.")
            else:
                print(f"   Фрагмент зустрічається {count} разів (очікувався 1) — неоднозначно. Нічого не змінено.")
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
    print("ПОТРІБЕН РЕСТАРТ БЕКЕНДУ — файл context.py використовується тільки при перекладі через DeepL, без рестарту старий код лишиться в пам’яті.")


if __name__ == "__main__":
    main()
