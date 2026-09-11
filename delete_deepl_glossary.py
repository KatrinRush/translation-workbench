#!/usr/bin/env python3
"""
delete_deepl_glossary.py

Видаляє один конкретний глосарій з DeepL-акаунта за його ID
(через DELETE /v2/glossaries/{id}).

Використання:
    DEEPL_API_KEY="твій-ключ" python3 delete_deepl_glossary.py <glossary_id>
"""
import os
import sys
import urllib.error
import urllib.request

API_KEY = os.environ.get("DEEPL_API_KEY", "").strip()

if not API_KEY:
    sys.exit("Задай ключ через змінну середовища DEEPL_API_KEY.")
if len(sys.argv) != 2:
    sys.exit("Використання: python3 delete_deepl_glossary.py <glossary_id>")

glossary_id = sys.argv[1]
is_free = API_KEY.endswith(":fx")
base_url = "https://api-free.deepl.com/v2/glossaries" if is_free else "https://api.deepl.com/v2/glossaries"
url = f"{base_url}/{glossary_id}"

request = urllib.request.Request(
    url,
    headers={"Authorization": f"DeepL-Auth-Key {API_KEY}"},
    method="DELETE",
)

try:
    with urllib.request.urlopen(request, timeout=15) as response:
        status = response.status
except urllib.error.HTTPError as error:
    status = error.code
except urllib.error.URLError as error:
    sys.exit(f"Не вдалося з'єднатися з DeepL: {error}")

if status in (204, 404):
    print(f"Глосарій {glossary_id} видалено (або його вже не було).")
else:
    sys.exit(f"DeepL повернув неочікуваний статус {status}.")
