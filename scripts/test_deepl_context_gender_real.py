import json
import os
import urllib.request
import urllib.error

API_KEY = os.environ["DEEPL_API_KEY"]
URL = "https://api-free.deepl.com/v2/translate"

TARGET = (
    "I've been waiting too long. My brother said he wanted you, "
    "so fair and pretty, but he's out playing Lord Muck in the country, "
    "and I'm tired of the second-best cuts."
)

# Тут вставляємо ТІЛЬКИ реальний English-контекст із роману.
# Жодних пояснень типу "The narrator is male."
CONTEXTS = {
    "A — no context": None,

    "B — immediate before": (
        '"Mr. Bunson!"\n'
        '"You\'re sixteen, Polly?"\n'
        '"Twenty!" I blink.'
    ),

    "C — first-person narration": (
        '"Thank you." I hoist up one of the heavy rolls of fabric '
        'and try to give a little curtsey.\n'
        'I think Mr. Bunson likes it when people treat him like he\'s '
        'very important.'
    ),

    "D — first-person after": (
        '"I\'ve never met—" I stop. '
        'I don\'t know anyone to marry, and I know I don\'t want to do '
        'what Bunson seems intent on doing, his hand pawing at my dress.'
    ),
}

for name, context in CONTEXTS.items():
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
        print(e.read().decode("utf-8", errors="replace"))

    except Exception as e:
        print("ERROR:", repr(e))

    print()
