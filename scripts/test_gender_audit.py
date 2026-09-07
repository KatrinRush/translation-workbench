import json
import os

ORIGINAL = (
    "I've been waiting too long. My brother said he wanted you, "
    "so fair and pretty, but he's out playing Lord Muck in the country, "
    "and I'm tired of the second-best cuts."
)

TRANSLATION = (
    "Я занадто довго чекала. Мій брат казав, що хоче тебе, "
    "таку світлошкіру й гарненьку, але він поїхав у село гратися "
    "в лорда Мака, а я втомилася від другосортних шматків."
)

RULE = "The narrator is male. First-person narration must use masculine grammatical forms."

PROMPT = f"""
You are a translation QA auditor.

Check the Ukrainian translation against the English original.

IMPORTANT RULE:
{RULE}

ORIGINAL:
{ORIGINAL}

TRANSLATION:
{TRANSLATION}

Find only actual errors caused by violation of the narrator-gender rule.

Return JSON in exactly this format:
{{
  "has_gender_error": true,
  "errors": [
    {{
      "source": "...",
      "current": "...",
      "expected": "...",
      "reason": "..."
    }}
  ]
}}

If there are no gender errors, return:
{{
  "has_gender_error": false,
  "errors": []
}}
"""

print("=" * 80)
print("GENDER AUDIT TEST")
print("=" * 80)
print()
print(PROMPT)
