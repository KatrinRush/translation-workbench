"""
Patch 39: distinguish a Gemini content-filter block from a genuinely
malformed response in GeminiProvider.analyze().

When Gemini's safety filter blocks a request/response, the JSON it
returns has no candidates[0].content.parts[0].text — either no
candidates at all (promptFeedback.blockReason set) or a candidate whose
finishReason is SAFETY/PROHIBITED_CONTENT/RECITATION/etc. instead of
STOP. The old code let that fall straight into the KeyError/IndexError
catch-all and mislabeled it "Gemini повернув некоректну відповідь." —
technically true but hides the actual, actionable reason (Катя's AI QA
run on an explicit-content chapter hit exactly this).

Now checks promptFeedback.blockReason and each candidate's finishReason
before touching the text path, and raises a specific message naming the
block reason when that's what happened. The genuine-malformed-shape case
(unexpected JSON despite a normal finish reason) keeps the original
generic message.

Run from the repo root (same folder as backend/):
    python apply_patch39.py
"""
from pathlib import Path

GEMINI_PROVIDER_PATH = Path("backend/integrations/providers/gemini.py")


def apply(path: Path, old: str, new: str, count: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    occurrences = text.count(old)
    if occurrences != count:
        raise SystemExit(
            f"Expected {count} occurrence(s) of snippet in {path}, found {occurrences}.\n"
            f"--- snippet ---\n{old}\n---------------"
        )
    path.write_text(text.replace(old, new, count), encoding="utf-8")


def main() -> None:
    apply(
        GEMINI_PROVIDER_PATH,
        '''        try:
            payload = json.loads(response_body.decode("utf-8"))
            text = payload["candidates"][0]["content"]["parts"][0]["text"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError) as error:
            raise ValueError("Gemini повернув некоректну відповідь.") from error
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Gemini повернув порожній результат аналізу.")
        return text.strip()''',
        '''        try:
            payload = json.loads(response_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("Gemini повернув некоректну відповідь.") from error

        block_reason = None
        if isinstance(payload, dict):
            block_reason = (payload.get("promptFeedback") or {}).get("blockReason")
        if block_reason:
            raise ValueError(f"Gemini заблокував запит через фільтр контенту ({block_reason}).")

        candidates = payload.get("candidates") if isinstance(payload, dict) else None
        if not candidates:
            raise ValueError("Gemini не повернув жодної відповіді — ймовірно, заблоковано фільтром контенту.")

        finish_reason = candidates[0].get("finishReason") if isinstance(candidates[0], dict) else None
        if finish_reason not in (None, "STOP", "MAX_TOKENS"):
            raise ValueError(f"Gemini заблокував або обірвав відповідь ({finish_reason}), ймовірно через фільтр контенту.")

        try:
            text = candidates[0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as error:
            raise ValueError("Gemini повернув некоректну відповідь.") from error
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Gemini повернув порожній результат аналізу.")
        return text.strip()''',
    )

    print("Patch 39 applied successfully.")


if __name__ == "__main__":
    main()
