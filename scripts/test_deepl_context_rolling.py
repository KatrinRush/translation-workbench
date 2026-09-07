import json
import os
import urllib.request

API_KEY = os.environ["DEEPL_API_KEY"]
URL = "https://api-free.deepl.com/v2/translate"

TARGET = (
    "I've been waiting too long. My brother said he wanted you, "
    "so fair and pretty, but he's out playing Lord Muck in the country, "
    "and I'm tired of the second-best cuts."
)

BEFORE = (
    '"You\'re sixteen, Polly?"\n'
    '"Twenty!" I blink.'
)

AFTER = (
    '"I\'ll go to the butcher\'s, sir!" I squirm and push, '
    "but Mr. Bunson is far heavier and taller than I am."
)

TESTS = {
    "A — no context": None,
    "B — before": BEFORE,
    "C — after": AFTER,
    "D — before + after": BEFORE + "\n" + AFTER,
}

for name, context in TESTS.items():
    payload = {
        "text": [TARGET],
        "source_lang": "EN",
        "target_lang": "UK",
        "tag_handling": "xml",
        "tag_handling_version": "v2",
    }

    if context:
        payload["context"] = context

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        URL,
        data=data,
        headers={
            "Authorization": f"DeepL-Auth-Key {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    print("=" * 80)
    print(name)
    print("=" * 80)
    print("CONTEXT:")
    print(context if context else "(none)")
    print()

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            print("HTTP", response.status)
            print("TRANSLATION:")
            print(result["translations"][0]["text"])
    except urllib.error.HTTPError as e:
        print("HTTP ERROR:", e.code)
        print("DEEPL RESPONSE:")
        print(e.read().decode("utf-8", errors="replace"))
    except Exception as e:
        print("ERROR:", repr(e))

    print()
