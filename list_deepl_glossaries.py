#!/usr/bin/env python3
"""
list_deepl_glossaries.py

Виводить усі глосарії, які зараз реально існують на твоєму DeepL-акаунті
(через GET /v2/glossaries), незалежно від того, чи знає про них Workbench.

Це допомагає з'ясувати, чи ліміт вичерпаний через "чужі"/забуті глосарії
(наприклад, створені напряму скриптами з backend/scripts/), чи справді
через ті, якими керує сам Workbench.

Використання:
    DEEPL_API_KEY="твій-ключ" python3 list_deepl_glossaries.py

Ключ також можна вставити прямо в змінну нижче замість читання з env,
якщо так зручніше.
"""
import json
import os
import sys
import urllib.request

API_KEY = os.environ.get("DEEPL_API_KEY", "").strip()

if not API_KEY:
    sys.exit("Задай ключ через змінну середовища DEEPL_API_KEY.")

is_free = API_KEY.endswith(":fx")
url = "https://api-free.deepl.com/v2/glossaries" if is_free else "https://api.deepl.com/v2/glossaries"

request = urllib.request.Request(
    url,
    headers={"Authorization": f"DeepL-Auth-Key {API_KEY}", "Accept": "application/json"},
    method="GET",
)

try:
    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
except urllib.error.HTTPError as error:
    sys.exit(f"DeepL повернув помилку {error.code}: {error.read().decode('utf-8', 'ignore')}")
except urllib.error.URLError as error:
    sys.exit(f"Не вдалося з'єднатися з DeepL: {error}")

glossaries = payload.get("glossaries", [])
if not glossaries:
    print("На акаунті немає жодного глосарію.")
else:
    print(f"Всього глосаріїв на акаунті: {len(glossaries)}\n")
    for item in glossaries:
        print(
            f"- id={item.get('glossary_id')}  "
            f"name={item.get('name')!r}  "
            f"{item.get('source_lang')}→{item.get('target_lang')}  "
            f"entries={item.get('entry_count')}  "
            f"ready={item.get('ready')}  "
            f"created={item.get('creation_time')}"
        )
