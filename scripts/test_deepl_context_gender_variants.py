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

# Реальний текст безпосередньо перед TARGET
BEFORE_3 = (
    '"Mr. Bunson!"\n'
    '"You\'re sixteen, Polly?"\n'
    '"Twenty!" I blink.'
)

# Реальний текст із first-person narration
FIRST_PERSON = (
    '"I\'ll go to the butcher\'s, sir!" I squirm and push, '
    "but Mr. Bunson is far heavier and taller than I am.\n"
    '"That\'s why I thought you were so young, Polly."\n'
    '"I\'ve never met—" I stop.'
)

# Реальний текст ширшого уривка перед TARGET
BEFORE_LONG = (
    '"You always keep yourself clean and neat, Polly. '
    'Clean and neat and smelling fresh like flowers and buttermilk."\n'
    '"Thank you." I hoist up one of the heavy rolls of fabric '
    'and try to give a little curtsey. I think Mr. Bunson likes it '
    'when people treat him like he\'s very important, and since we\'d '
    'be out on the streets without his kindness, I suppose he\'s most '
    'important to the children and me.\n'
    '“Ooh!” A sharp little squeak jumps out of my lungs as the heavy '
    'roll crashes across my waist, Mr. Bunson on one side of it and '
    'me pinned to the wall on the other. “Mr. Bunson!”\n'
    '“You’re sixteen, Polly?”\n'
    '“Twenty!” I blink.'
)

AFTER = (
    '"I\'ll go to the butcher\'s, sir!" I squirm and push, '
    "but Mr. Bunson is far heavier and taller than I am.\n"
    '"That\'s why I thought you were so young, Polly."\n'
    'Most girls your age would already have had a husband by now—or '
    'at least a few good going overs."\n'
    '"I\'ve never met—" I stop. I don\'t know anyone to marry, '
    'and I know I don\'t want to do what Bunson seems intent on doing, '
    'his hand pawing at my dress. "Stop that!"\n'
    '"Shut up, or I\'ll put you out now. Tonight."'
)

TESTS = {
    "A — 3 before": BEFORE_3,
    "B — first-person context": FIRST_PERSON,
    "C — long before": BEFORE_LONG,
    "D — after": AFTER,
    "E — long before + after": BEFORE_LONG + "\n" + AFTER,
}

for name, context in TESTS.items():
    payload = {
        "text": [TARGET],
        "source_lang": "EN",
        "target_lang": "UK",
        "tag_handling": "xml",
        "tag_handling_version": "v2",
        "context": context,
    }

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
    print(context)
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
