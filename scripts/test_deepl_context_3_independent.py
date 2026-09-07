import json
import os
import urllib.request

API_KEY = os.environ["DEEPL_API_KEY"]
URL = "https://api-free.deepl.com/v2/translate"


TESTS = [
    {
        "name": "TEST 1",
        "before": (
            '"Mr. Bunson!"\n'
            '"You\'re sixteen, Polly?"\n'
            '"Twenty!" I blink.'
        ),
        "target": (
            "I've been waiting too long. My brother said he wanted you, "
            "so fair and pretty, but he's out playing Lord Muck in the country, "
            "and I'm tired of the second-best cuts."
        ),
        "after": (
            '"I\'ll go to the butcher\'s, sir!" I squirm and push, '
            "but Mr. Bunson is far heavier and taller than I am.\n"
            '"That\'s why I thought you were so young, Polly."\n'
            'Most girls your age would already have had a husband by now—or at least a few good going overs."'
        ),
    },

    {
        "name": "TEST 2",
        "before": (
            '"You always keep yourself clean and neat, Polly. '
            'Clean and neat and smelling fresh like flowers and buttermilk."\n'
            '"Thank you." I hoist up one of the heavy rolls of fabric and try to give a little curtsey.\n'
            "I think Mr. Bunson likes it when people treat him like he's very important, "
            "and since we'd be out on the streets without his kindness, "
            "I suppose he's most important to the children and me."
        ),
        "target": (
            "Ooh! A sharp little squeak jumps out of my lungs as the heavy roll crashes "
            "across my waist, Mr. Bunson on one side of it and me pinned to the wall on the other."
        ),
        "after": (
            '"Mr. Bunson!"\n'
            '"You\'re sixteen, Polly?"\n'
            '"Twenty!" I blink.'
        ),
    },

    {
        "name": "TEST 3",
        "before": (
            '"I\'ll go to the butcher\'s, sir!" I squirm and push, '
            "but Mr. Bunson is far heavier and taller than I am.\n"
            '"That\'s why I thought you were so young, Polly."\n'
            'Most girls your age would already have had a husband by now—or at least a few good going overs."'
        ),
        "target": (
            '"I\'ve never met—" I stop. I don\'t know anyone to marry, '
            "and I know I don't want to do what Bunson seems intent on doing, "
            'his hand pawing at my dress. "Stop that!"'
        ),
        "after": (
            '"Shut up, or I\'ll put you out now. Tonight."\n'
            '"You always keep yourself clean and neat, Polly. '
            'Clean and neat and smelling fresh like flowers and buttermilk."\n'
            '"Thank you." I hoist up one of the heavy rolls of fabric and try to give a little curtsey.'
        ),
    },
]


def translate(target, context):
    payload = {
        "text": [target],
        "source_lang": "EN",
        "target_lang": "UK",
        "context": context,
    }

    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"DeepL-Auth-Key {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["translations"][0]["text"]


for test in TESTS:
    context = test["before"] + "\n" + test["after"]

    print("=" * 80)
    print(test["name"])
    print("=" * 80)
    print("BEFORE:")
    print(test["before"])
    print()
    print("TARGET:")
    print(test["target"])
    print()
    print("AFTER:")
    print(test["after"])
    print()
    print("TRANSLATION:")

    try:
        print(translate(test["target"], context))
    except Exception as e:
        print("ERROR:", repr(e))

    print()
