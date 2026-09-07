from __future__ import annotations

import json
import os
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_KEY = os.environ.get("DEEPL_API_KEY")

if not API_KEY:
    print("ERROR: DEEPL_API_KEY is not set.")
    sys.exit(1)

TEXT = '<p>This is a <b>very <i>important</i> and</b> urgent message.</p>'

URL = (
    "https://api-free.deepl.com/v2/translate"
    if API_KEY.endswith(":fx")
    else "https://api.deepl.com/v2/translate"
)


def run_test(name: str, extra_fields: dict[str, str]) -> None:
    fields = {
        "text": TEXT,
        "source_lang": "EN",
        "target_lang": "UK",
        "preserve_formatting": "1",
        **extra_fields,
    }

    body = urlencode(fields).encode("utf-8")

    request = Request(
        URL,
        headers={
            "Authorization": f"DeepL-Auth-Key {API_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data=body,
        method="POST",
    )

    print()
    print("=" * 80)
    print(name)
    print("=" * 80)
    print("REQUEST:")
    print(json.dumps(fields, ensure_ascii=False, indent=2))

    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read()
            print()
            print(f"HTTP {response.status}")
            print("RESPONSE:")
            print(raw.decode("utf-8"))
    except Exception as exc:
        print()
        print("ERROR:")
        print(repr(exc))


run_test("A — no tag handling", {})

run_test(
    "B — XML tag handling",
    {"tag_handling": "xml"},
)

run_test(
    "C — XML tag handling + v2",
    {
        "tag_handling": "xml",
        "tag_handling_version": "v2",
    },
)
