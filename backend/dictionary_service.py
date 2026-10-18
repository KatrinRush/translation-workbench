"""Dictionary lookups for the original column: a word or phrase in its sentence.

The answer has two parts that never mix. The NEUTRAL part (meaning in this sentence, translation variants,
other meanings) is made from the original and the sentence only, never from a translation: the model keeps an
inventory of senses per lemma (dictionary_senses, not tied to a model or a paragraph) and, for a sentence, only
picks the sense from it (dictionary_picks); «жодне не підходить» appends a new sense to the inventory instead of
the nearest one. The TRANSLATION-AWARE part («Як перекладено тут», why, remarks) is a separate call that sees the
translation and is cached per paragraph and translation text (dictionary_renderings).

Order of a lookup: (1) the project glossary, longest match, answered without the model; (2) the cached sense
pick; (3) a model call: the full inventory for an unknown lemma, else the pick against the stored inventory.
The model answers strict JSON, validated here; one retry when it is not valid. Every call is recorded in
translation_usage with kind 'dictionary'.

Privacy: the logs carry only lengths and token counts, never book text.
"""

from __future__ import annotations

import hashlib
import unicodedata
import html
import json
import logging
import re
from typing import Any, Callable, Mapping

from .integrations.base import TranslationRequest
from .integrations.credentials import CredentialVault, CredentialVaultError
from .integrations.registry import ProviderRegistry
from .rendering_alignment import align_candidates, canonical_rendering as rendering_lemma, has_unknown_words, occurs
from .translations.glossary_check import _APOSTROPHES
from .translations.llm_prompt import is_character, select_glossary_entries
from .translations.narrator import NARRATOR_LABELS
from .usage import UsageRecorder, capture_usage, find_price

LLM_PROVIDERS = ("claude", "openai", "gemini")
MODES = ("word", "phrase", "more")
MAX_SENSES = 8
MAX_EXTENSIONS = 3
MAX_RESOLVE_PARAGRAPHS = 20
SCHEMA_VERSION = 1
MAX_PHRASE_CHARS = 80
MAX_PHRASE_WORDS = 8
MAX_MORE_REQUESTS = 3
MAX_OUTPUT_TOKENS = 1500
TERM_TYPES = ("word", "phrase", "idiom", "phrasal_verb")

# A word: letters with inner apostrophes (' ’ ‘ ʼ) and hyphens.
WORD_RE = re.compile(r"[^\W\d_]+(?:['’‘ʼ‐‑-][^\W\d_]+)*")
_TAG_RE = re.compile(r"<[^>]*>")

_ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "st", "prof", "jr", "sr", "vs", "etc", "i.e", "e.g", "mt", "capt", "col", "gen", "lt",
    "sgt", "rev", "hon", "fig", "approx", "ca", "cf", "viz", "inc", "ltd", "co", "mme", "mlle", "messrs",
}
_CLOSERS = set("\"'”’»)]}›")
_OPENERS = set("\"'“‘«([{‹")


class DictionaryError(RuntimeError):
    def __init__(self, message: str, http_status: int = 400, code: str = "dictionary_error"):
        super().__init__(message)
        self.http_status = http_status
        self.code = code


# --- text helpers ----------------------------------------------------------------------------


def plain_text(original: str) -> str:
    """The text of an original paragraph as the browser shows it (textContent): inline tags removed,
    entities decoded. The client's offsets count in this text."""
    return html.unescape(_TAG_RE.sub("", original or ""))


def normalize_term(text: str) -> str:
    return " ".join((text or "").translate(_APOSTROPHES).split()).lower()


def split_sentences(text: str) -> list[tuple[int, int]]:
    """Sentence spans (start, end) of a paragraph. A sentence ends after . ! ? … (plus closing quotes or
    brackets) and whitespace, unless the dot belongs to an abbreviation (Mr., Dr., St., etc., i.e.) or an
    initial, or the next word starts in lower case (a dialogue tag: «"Stop!" she cried.»). A closing
    quote after the stop stays in the sentence: «"Go." She left.» splits after the quote."""
    spans: list[tuple[int, int]] = []
    start = 0
    i = 0
    n = len(text)
    while i < n:
        if text[i] not in ".!?…":
            i += 1
            continue
        j = i
        while j + 1 < n and text[j + 1] in ".!?…":
            j += 1
        k = j + 1
        while k < n and text[k] in _CLOSERS:
            k += 1
        if k >= n or not text[k].isspace():
            i = j + 1
            continue
        m = k
        while m < n and text[m].isspace():
            m += 1
        q = m
        while q < n and text[q] in _OPENERS:
            q += 1
        following = text[q] if q < n else ""
        boundary = True
        if text[i] == "." and j == i:
            token = re.search(r"([A-Za-z][A-Za-z.]*)$", text[:i])
            if token:
                word = token.group(1)
                lowered = word.lower().rstrip(".")
                if lowered in _ABBREVIATIONS or (len(word) == 1 and word != "I"):
                    boundary = False
                elif lowered == "no" and following.isdigit():
                    boundary = False
        if following.islower():
            boundary = False
        if boundary and m < n:
            spans.append((start, k))
            start = m
        i = m if boundary else j + 1
    if start < n:
        spans.append((start, n))
    return spans or [(0, n)]


def sentence_around(text: str, start: int, end: int) -> tuple[int, int]:
    """The sentence that holds text[start:end]; the whole paragraph when it cannot be told."""
    try:
        for a, b in split_sentences(text):
            if a <= start and end <= b:
                return a, b
    except Exception:  # defensive: a splitter bug must not break a lookup
        pass
    return 0, len(text)


def glossary_matches(entries: list[Mapping[str, Any]], text: str) -> list[tuple[int, int, Mapping[str, Any]]]:
    """Spans of glossary terms in the paragraph, as glossary_check does it: whole words, typographic
    apostrophes and quotes straightened, case ignored, and a term inside an already matched longer
    one is not reported."""
    haystack = text.translate(_APOSTROPHES)
    found: list[tuple[int, int, Mapping[str, Any]]] = []
    ordered = sorted(select_glossary_entries(entries), key=lambda entry: len(str(entry.get("source") or "")), reverse=True)
    for entry in ordered:
        words = str(entry.get("source") or "").translate(_APOSTROPHES).split()
        if not words:
            continue
        pattern = r"(?<!\w)" + r"\s+".join(re.escape(word) for word in words) + r"(?!\w)"
        for match in re.finditer(pattern, haystack, re.IGNORECASE):
            a, b = match.span()
            if any(s <= a and b <= e for s, e, _ in found):
                continue
            found.append((a, b, entry))
    return found


# --- the model's answers ---------------------------------------------------------------------

REGISTERS = ("нейтральне", "розмовне", "застаріле", "книжне", "формальне", "груба лексика", "жаргон", "поетичне", "діалектне", "зневажливе")
NO_SENSE = "none"
_NO_REMARK = re.compile(r"^\W*(?:немає|нема|без|відсутн\w*|не потребує|переклад\w* (?:адекватн|коректн|правильн|точн|влучн|цілком)|все (?:добре|гаразд|вірно)|зауважень)", re.IGNORECASE)


_POS_UK = {
    "noun": "іменник", "verb": "дієслово", "adjective": "прикметник", "adverb": "прислівник", "pronoun": "займенник",
    "preposition": "прийменник", "conjunction": "сполучник", "interjection": "вигук", "numeral": "числівник", "particle": "частка",
    "determiner": "означник", "article": "артикль", "exclamation": "вигук", "participle": "дієприкметник", "phrase": "фраза",
    "idiom": "ідіома", "phrasal verb": "фразове дієслово", "proper noun": "власна назва", "abbreviation": "скорочення",
}


def ukrainian_pos(value: str | None) -> str | None:
    """The part of speech always in Ukrainian: the model sometimes answers «noun»."""
    if not value:
        return value
    key = " ".join(value.casefold().replace("_", " ").split())
    if key in _POS_UK:
        return _POS_UK[key]
    return _POS_UK.get(re.split(r"[\s,;/]+", key)[0], value)


# «Чому так» that only restates the dictionary or the grammar instead of giving a ground: the meaning matches the dictionary, the
# form matches the original, case and number. Such a text counts as no reason.
_EMPTY_REASON = re.compile(
    r"відповіда\w*\s+(?:\w+\s+){0,2}значенн\w*|за\s+словником|словникови\w*\s+значенн|"
    r"форм\w*\s+(?:\w+\s+)?(?:збіг\w*|співпад\w*|відповіда\w*)|(?:збіг\w*|співпад\w*)\s+з\s+оригінал\w*|відповідає\s+оригінал\w*|"
    r"називн\w*\s+відмін\w*|\bвідмін(?:ок|к\w+)\b|\bоднин\w*|\bмножин\w*|\bчисл[оі]\b|"
    r"дослівн\w*|буквальн\w*|прямий\s+переклад|звичайн\w*\s+переклад|стандартн\w*\s+(?:переклад|відповідник)",
    re.IGNORECASE,
)


def _text(value: Any, limit: int, required: bool = False) -> str | None:
    if value is None:
        if required:
            raise ValueError("missing text")
        return None
    if not isinstance(value, str):
        raise ValueError("not a string")
    value = " ".join(value.split())
    if not value:
        if required:
            raise ValueError("empty text")
        return None
    return value[:limit]


def normalize_variant(text: str) -> str:
    """A translation variant for comparing: case, stress marks and punctuation do not matter."""
    decomposed = unicodedata.normalize("NFD", (text or "").translate(_APOSTROPHES))
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return " ".join(re.sub(r"[^\w\s'-]", " ", stripped.casefold()).split())


def _translations(items: Any, limit: int = 6) -> list[dict[str, Any]]:
    if not isinstance(items, list) or not items:
        raise ValueError("translations")
    cleaned: list[dict[str, Any]] = []
    unknown: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items[:limit]:
        if not isinstance(item, dict):
            raise ValueError("translation item")
        text = _text(item.get("text"), 80, required=True)
        key = normalize_variant(text)
        if key in seen:
            continue
        seen.add(key)
        entry = {"text": text, "register": _text(item.get("register"), 40) or "нейтральне"}
        # a word pymorphy3 does not know (made up by the model: «баранння») is not shown
        (unknown if has_unknown_words(text) else cleaned).append(entry)
    # when nothing in a sense could be checked it stays, marked, rather than being left without any variant
    return cleaned or [{**entry, "unverified": True} for entry in unknown]


def _examples(items: Any) -> list[dict[str, str]]:
    if items is None:
        return []
    if not isinstance(items, list):
        raise ValueError("examples")
    cleaned: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in items[:4]:
        if not isinstance(item, dict):
            raise ValueError("example item")
        example = {"en": _text(item.get("en"), 300, required=True), "uk": _text(item.get("uk"), 300, required=True)}
        key = normalize_variant(example["en"])
        if key not in seen:
            seen.add(key)
            cleaned.append(example)
    return cleaned[:2]


def validate_sense(data: Any) -> dict[str, Any]:
    """One sense of the inventory: {gloss, pos, translations, examples} (the id is given by the code)."""
    if not isinstance(data, dict):
        raise ValueError("sense is not an object")
    return {
        "gloss": _text(data.get("gloss"), 400, required=True),
        "pos": ukrainian_pos(_text(data.get("pos"), 40)),
        "translations": _translations(data.get("translations")),
        "examples": _examples(data.get("examples")),
    }


def _term_fields(data: Mapping[str, Any], fallback_term: str) -> dict[str, Any]:
    term_type = data.get("termType")
    if term_type not in TERM_TYPES:
        raise ValueError("bad termType")
    return {
        "term": _text(data.get("term"), 120) or fallback_term,
        "lemma": _text(data.get("lemma"), 120),
        "pos": ukrainian_pos(_text(data.get("pos"), 40)),
        "termType": term_type,
        "expandedPhrase": _text(data.get("expandedPhrase"), 120),
    }


def _variant_keys(sense: Mapping[str, Any]) -> set[str]:
    return {rendering_lemma(item["text"]) for item in sense["translations"]}


def merge_into(existing: dict[str, Any], sense: Mapping[str, Any]) -> None:
    """The same meaning told twice: the later one adds its variants and examples to the earlier."""
    known = {normalize_variant(item["text"]) for item in existing["translations"]}
    existing["translations"] += [dict(item) for item in sense["translations"] if normalize_variant(item["text"]) not in known]
    have = {normalize_variant(item["en"]) for item in existing.get("examples") or []}
    existing["examples"] = [*(existing.get("examples") or []), *(item for item in sense.get("examples") or [] if normalize_variant(item["en"]) not in have)][:2]


def same_sense(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    """The same gloss, or a shared translation variant in the same part of speech: one meaning, not two."""
    if normalize_variant(left["gloss"]) == normalize_variant(right["gloss"]):
        return True
    return (left.get("pos") or "") == (right.get("pos") or "") and bool(_variant_keys(left) & _variant_keys(right))


def _sense_list(items: Any) -> list[dict[str, Any]]:
    """The senses of an answer with ids s1, s2, … by position; a repeated meaning (the same gloss or a shared
    translation variant) is merged into the first."""
    if not isinstance(items, list) or not items:
        raise ValueError("senses")
    senses: list[dict[str, Any]] = []
    for item in items[:MAX_SENSES]:
        sense = validate_sense(item)
        twin = next((existing for existing in senses if same_sense(existing, sense)), None)
        if twin is not None:
            merge_into(twin, sense)
            continue
        senses.append({"id": f"s{len(senses) + 1}", **sense})
    return senses


def _remap_sense_id(raw: list[Any], merged: list[dict[str, Any]], index: int) -> str:
    """The id in the merged list of the sense the model numbered `index` in its own list."""
    try:
        chosen = validate_sense(raw[index])
    except ValueError:
        return merged[0]["id"]
    return next((sense["id"] for sense in merged if same_sense(sense, chosen)), merged[0]["id"])


def validate_full(data: Any, fallback_term: str) -> dict[str, Any]:
    """The answer for an unknown lemma: the term fields, the whole inventory and the chosen sense."""
    if not isinstance(data, dict):
        raise ValueError("not an object")
    fields = _term_fields(data, fallback_term)
    raw_senses = data.get("senses")
    senses = _sense_list(raw_senses)
    wanted = data.get("senseId")
    ids = [f"s{i + 1}" for i in range(len(raw_senses))]
    if wanted not in ids:
        raise ValueError("senseId")
    wanted = _remap_sense_id(raw_senses, senses, int(wanted[1:]) - 1)
    return {**fields, "senses": senses, "senseId": wanted}


def validate_pick(data: Any, fallback_term: str, inventory_ids: list[str]) -> dict[str, Any]:
    """The answer against a known inventory: an existing senseId, or "none" with the new sense described."""
    if not isinstance(data, dict):
        raise ValueError("not an object")
    fields = _term_fields(data, fallback_term)
    sense_id = data.get("senseId")
    if sense_id == NO_SENSE:
        return {**fields, "senseId": None, "newSense": validate_sense(data.get("newSense"))}
    if sense_id not in inventory_ids:
        raise ValueError("senseId")
    return {**fields, "senseId": sense_id, "newSense": None}


def validate_extension(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        raise ValueError("not an object")
    raw = data.get("senses")
    if not isinstance(raw, list):
        raise ValueError("senses")
    return [validate_sense(item) for item in raw[:3]]


def validate_rendering(data: Any) -> dict[str, Any]:
    """The translation-aware answer. Empty remarks and boilerplate («зауважень немає») count as no remark."""
    if not isinstance(data, dict):
        raise ValueError("not an object")
    rendering = _text(data.get("rendering"), 200)
    reason = _text(data.get("reason"), 300)
    if reason and (_NO_REMARK.match(reason) or _EMPTY_REASON.search(reason)):
        reason = None
    raw_issues = data.get("issues") or []
    if not isinstance(raw_issues, list):
        raise ValueError("issues")
    issues = []
    for item in raw_issues[:3]:
        text = _text(item, 300) if isinstance(item, str) else None
        if text and not _NO_REMARK.match(text) and not _EMPTY_REASON.search(text):
            issues.append(text)
    return {"rendering": rendering, "reason": reason, "issues": issues}


def parse_json_object(text: str) -> Any:
    stripped = text.strip()
    stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", stripped)
    first, last = stripped.find("{"), stripped.rfind("}")
    if first < 0 or last <= first:
        raise ValueError("no JSON object")
    return json.loads(stripped[first:last + 1])


_SENSE_SCHEMA = (
    '{"gloss": "значення коротко, українською, лише за оригіналом", "pos": "частина мови українською", '
    '"translations": [{"text": "український відповідник", "register": "нейтральне | розмовне | застаріле | книжне | груба лексика | жаргон | поетичне | діалектне | зневажливе"}], '
    '"examples": [{"en": "приклад", "uk": "переклад прикладу"}]}'
)

_COMMON_RULES = (
    "Ти англо-український словник для перекладача художньої книжки. Ти НЕ бачиш перекладу книжки і не повинен його вгадувати: "
    "значення визначай лише за оригіналом і контекстом речення. Відповідай ЛИШЕ одним JSON-об'єктом, без markdown і без пояснень. "
    "Усі пояснення — українською; поля term, lemma, expandedPhrase, examples[].en — англійською. "
    "Кожен варіант перекладу має позначку регістру (нейтральне, якщо особливого регістру немає). "
    "Варіанти перекладу одного значення — синоніми саме цього значення; той самий український відповідник не повторюй у різних значеннях. "
    "Не вигадуй нічого, чого не знаєш: краще менше значень. "
    "Одне значення — один запис: синоніми й відмінкові форми того самого значення (автомобіль, машина) — це варіанти ОДНОГО значення, а не різні значення. "
    "Варіанти пиши в початковій формі (називний відмінок однини для іменників) і лише ті, якими це англійське слово справді перекладають; "
    "не додавай слів, що лише звучать схоже або є відповідниками іншого англійського слова (омонім, інша лексема), і рідкісних чи помилкових відповідників. "
    "Додавай розмовні, регіональні й застарілі відповідники, якщо вони справді вживаються, з відповідною позначкою регістру. "
    "Кожен приклад у examples — різний; не повторюй той самий приклад. "
    "Кожен український відповідник — реальне слово сучасної української мови, яке ти точно знаєш; ніколи не вигадуй слів і не утворюй їх самотужки "
    "(«баранння», «невинятко» — вигадані). Перелічуй найприродніші й найуживаніші відповідники першими, зокрема пестливі та зменшувальні форми, "
    "якщо вони звичайні для цього слова (ягня — ягнятко). Частину мови (pos) завжди пиши українською: іменник, дієслово, прикметник, прислівник тощо, "
    "ніколи англійською (noun, verb)."
)

SYSTEM_FULL = _COMMON_RULES + """
Дай повний перелік значень слова чи фрази (від 1 до 6, за частотою; різні частини мови — окремі значення), потім познач те, що стоїть у реченні.
Схема відповіді:
{"term": "слово чи фраза так, як вона стоїть у реченні", "lemma": "початкова форма слова чи фрази", "pos": "частина мови в цьому реченні",
 "termType": "word | phrase | idiom | phrasal_verb",
 "expandedPhrase": "ширша усталена фраза, ідіома чи фразове дієслово, до якої входить слово в цьому реченні, інакше null",
 "senses": [""" + _SENSE_SCHEMA + """, ...],
 "senseId": "s1 — номер значення зі списку senses (s1, s2, … за порядком), яке стоїть у цьому реченні"}
У книжці слово може мати особливе значення (раса, титул, істота, вигадана назва): якщо за контекстом це так, додай його до senses і вибери його."""

SYSTEM_PICK = _COMMON_RULES + """
Тобі дано перелік значень слова чи фрази. Обери те, що стоїть у реченні. Якщо жодне з наведених не підходить — це може бути особливе значення \
цієї книжки чи серії (раса, титул, істота, вигадана назва) або рідкісне значення: тоді senseId = "none" і опиши нове значення в newSense. \
Не добирай найближче значення, якщо воно не підходить.
Схема відповіді:
{"term": "слово чи фраза так, як вона стоїть у реченні", "lemma": "початкова форма", "pos": "частина мови в цьому реченні",
 "termType": "word | phrase | idiom | phrasal_verb",
 "expandedPhrase": "ширша усталена фраза, ідіома чи фразове дієслово, до якої входить слово в цьому реченні, інакше null",
 "senseId": "id зі списку або none",
 "newSense": null або """ + _SENSE_SCHEMA + "}"

SYSTEM_EXTEND = _COMMON_RULES + """
Дай ще до 3 РІДКІСНИХ значень слова чи фрази, яких немає в уже відомих (застарілі, технічні, жаргонні, переносні). Якщо їх нема — порожній список.
Схема відповіді: {"senses": [""" + _SENSE_SCHEMA + ", ...]}"

SYSTEM_RENDERING = """Ти допомагаєш перекладачеві художньої книжки перевірити, як слово чи фразу з оригіналу передано в перекладі абзацу.
Відповідай ЛИШЕ одним JSON-об'єктом, без markdown. Усі пояснення — українською.
Схема: {"rendering": "слово чи фраза перекладу, якою передано термін, або null, якщо не знайдено",
 "reason": "коротко (одне речення), чому так переклали, АБО null",
 "issues": ["конкретна проблема", ...]}
Правила:
- Спершу знайди в перекладі абзацу слово чи фразу, якими передано термін. Якщо в перекладі є форма (будь-який відмінок чи число) одного зі "значень за словником", відомих відповідників або "кандидата від програми" — поверни саме цю форму з перекладу. null — лише якщо жодного відповідника в тексті справді немає.
- rendering — рівно так, як стоїть у тексті перекладу (з його відмінковим закінченням), без додаткових слів.
- reason — лише справжня підстава вибору слова. НІКОЛИ не пиши у reason: що переклад «відповідає значенню за словником», що форма «збіглася з оригіналом», \
згадки про відмінок, число (однина, множина, називний відмінок), «дослівно», «буквально», «стандартний переклад», і не переказуй сам переклад. \
Погані відповіді (замість них — reason: null): «Перекладено як молода вівця, що відповідає першому значенню за словником; форма збіглася з оригіналом \
(однина, називний відмінок)»; «Відповідає основному значенню слова»; «Слово в однині, як в оригіналі». \
Добрі підстави: «Зменшувальна форма передає little (little lamb).»; «Мовлення персонажа розмовне, тому просте слово.»; «Так у глосарії проєкту.»
- reason пиши лише з реальних підстав, які видно з наданого: хто говорить (оповідач чи персонаж і його мовлення), регістр, запис у глосарії, правило проєкту. Якщо очевидної причини немає — reason: null. Не вигадуй причин.
- issues заповнюй лише за конкретної проблеми: помилка значення, суперечність глосарію, регістр не відповідає мовцеві. Якщо зауважень немає — обов'язково порожній список []; це правильна відповідь. Не давай порад заради порад."""

SYSTEM_RESOLVE = """Для кожного пронумерованого абзацу визнач, яким словом чи фразою в українському перекладі передано вказаний англійський термін.
Відповідай ЛИШЕ одним JSON-об'єктом: {"items": [{"n": 1, "rendering": "слово перекладу або null, якщо не знайдено"}, ...]}. Нічого не вигадуй: якщо не впевнений — null.
rendering — рівно так, як слово стоїть у тексті перекладу. Якщо в абзаці є форма одного з відомих відповідників (їх наведено) — поверни її."""


def _sense_line(sense: Mapping[str, Any]) -> str:
    variants = "; ".join(f"{item['text']} ({item['register']})" for item in sense["translations"])
    return f"{sense['id']}: {sense['gloss']}" + (f" [{sense['pos']}]" if sense.get("pos") else "") + f" — варіанти: {variants}"


def _marked(sentence: str, start: int, end: int, sentence_start: int) -> str:
    return sentence[:start - sentence_start] + "⟦" + sentence[start - sentence_start:end - sentence_start] + "⟧" + sentence[end - sentence_start:]


def build_user_message(term: str, effective_mode: str, sentence: str, paragraph: str, start: int, end: int, sentence_start: int,
                       inventory: Mapping[str, Any] | None = None) -> str:
    """The question for the neutral part. It carries the original only: no translation of the paragraph."""
    lines = [
        f"Термін: {term}",
        f"Що це: {'фраза' if effective_mode == 'phrase' else 'слово'}",
        f"Речення (термін позначено ⟦ ⟧): {_marked(sentence, start, end, sentence_start)}",
    ]
    if sentence.strip() != paragraph.strip():
        lines.append(f"Увесь абзац (контекст): {paragraph}")
    if inventory is not None:
        lines.append("Відомі значення:")
        lines.extend(_sense_line(sense) for sense in inventory["senses"])
    return "\n".join(lines)


def build_extension_message(term: str, inventory: Mapping[str, Any]) -> str:
    return f"Слово чи фраза: {term}\nУже відомі значення (не повторюй):\n" + "\n".join(_sense_line(sense) for sense in inventory["senses"])


# --- translation-aware helpers ---------------------------------------------------------------------


def translation_hash(text: str | None) -> str:
    return hashlib.sha256(f"{SCHEMA_VERSION}\n{(text or '').strip()}".encode("utf-8")).hexdigest()[:32]


def english_forms(word: str) -> set[str]:
    """The word and its regular forms (-s, -es, -ed, -ing, 's, -ies/-ied, a doubled final consonant)."""
    base = word.lower()
    forms = {base, base + "s", base + "es", base + "'s", base + "’s", base + "ed", base + "d", base + "ing"}
    if base.endswith("e"):
        forms.add(base[:-1] + "ing")
    if base.endswith("y") and len(base) > 2:
        forms |= {base[:-1] + "ies", base[:-1] + "ied"}
    if len(base) > 2 and base[-1] not in "aeiouwxy" and base[-2] in "aeiou" and base[-3] not in "aeiou":
        forms |= {base + base[-1] + "ed", base + base[-1] + "ing"}
    return forms


def original_pattern(lemma_key: str, surfaces: list[str]) -> re.Pattern[str]:
    """Where a lemma stands in an original text: the lemma and its regular forms (a single word), the phrase itself
    for a phrase, and every form seen in a lookup."""
    options: set[str] = {re.escape(form) for form in english_forms(lemma_key)} if " " not in lemma_key else {re.escape(lemma_key)}
    options |= {re.escape(surface) for surface in surfaces}
    ordered = sorted(options, key=len, reverse=True)
    return re.compile(r"(?<![\w'’])(?:" + "|".join(r"\s+".join(part.split(r"\ ")) for part in ordered) + r")(?![\w])", re.IGNORECASE)


def variant_pattern(text: str) -> re.Pattern[str] | None:
    """A Ukrainian variant in any case form: the stem of every word (cases change the ending), words in order."""
    words = [word for word in re.findall(r"[\w'’]+", normalize_variant(text)) if word]
    if not words:
        return None
    stems = []
    for word in words:
        cut = 2 if len(word) >= 6 else (1 if len(word) >= 4 else 0)
        stems.append(re.escape(word[:len(word) - cut]) + r"[\w'’]*")
    return re.compile(r"(?<![\w'’])" + r"[\W]+".join(stems), re.IGNORECASE)


def canonical_rendering(rendering: str, variants: list[str]) -> str:
    """A rendering as one of the known variants when it is a case form of it, so «кочергу» and «кочерга» are one line."""
    for variant in variants:
        pattern = variant_pattern(variant)
        if pattern and pattern.fullmatch(normalize_variant(rendering)):
            return variant
    return normalize_variant(rendering) or rendering


class DictionaryService:
    def __init__(
        self,
        storage: Any,
        vault: CredentialVault,
        registry: ProviderRegistry,
        list_models: Callable[[str], Mapping[str, Any]],
        glossary_entries: Callable[[dict[str, Any]], list[dict[str, Any]]],
    ):
        self._storage = storage
        self._vault = vault
        self._registry = registry
        self._list_models = list_models
        self._glossary_entries = glossary_entries

    # ------------------------------------------------------------------ request

    @staticmethod
    def _parse_request(data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise DictionaryError("Некоректний запит.", 400, "dictionary_invalid")
        project_id, paragraph_id, text = data.get("projectId"), data.get("paragraphId"), data.get("text")
        start, end, mode = data.get("offsetStart"), data.get("offsetEnd"), data.get("mode", "word")
        if not isinstance(project_id, str) or not isinstance(paragraph_id, str) or not isinstance(text, str):
            raise DictionaryError("Вкажіть проєкт, абзац і текст.", 400, "dictionary_invalid")
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (start, end)) or start < 0 or end <= start:
            raise DictionaryError("Некоректне місце в абзаці.", 400, "dictionary_invalid")
        if mode not in MODES:
            raise DictionaryError("Режим має бути word, phrase або more.", 400, "dictionary_invalid")
        return {"projectId": project_id, "paragraphId": paragraph_id, "text": text, "start": start, "end": end, "mode": mode}

    @staticmethod
    def _locate(plain: str, request: dict[str, Any]) -> tuple[int, int]:
        """The selection in the paragraph's plain text, trimmed to its words. The client's text must agree
        with the offsets; if the paragraph changed meanwhile the text is looked up near them."""
        start, end = request["start"], min(request["end"], len(plain))
        wanted = normalize_term(request["text"])
        if start >= len(plain) or normalize_term(plain[start:end]) != wanted:
            candidates = [m.start() for m in re.finditer(re.escape(request["text"].strip()), plain)] if request["text"].strip() else []
            if not candidates:
                raise DictionaryError("Абзац змінився, торкніться слова ще раз.", 409, "dictionary_stale")
            start = min(candidates, key=lambda position: abs(position - request["start"]))
            end = start + len(request["text"].strip())
        words = list(WORD_RE.finditer(plain, start, end))
        if not words:
            raise DictionaryError("Тут нема слова для пошуку.", 400, "dictionary_no_word")
        return words[0].start(), words[-1].end()

    # ------------------------------------------------------------------ model

    def _ready_connections(self) -> list[dict[str, Any]]:
        return [
            item for item in self._storage.list_integration_connections()
            if item["providerId"] in LLM_PROVIDERS and item["enabled"] and item["testStatus"] == "connected"
        ]

    def _resolve_model(self, project: dict[str, Any], inventory: bool = False) -> tuple[dict[str, Any], str]:
        """The connection and model of a dictionary request. The inventory of a word (made once per word and kept) may have its own,
        stronger model (`inventoryModel`); «Як перекладено тут» and the rest use `model`, else the cheapest one."""
        configuration = (project.get("aiConfiguration") or {}).get("dictionary") or {}
        ready = self._ready_connections()
        wanted = configuration.get("connectionId")
        if wanted:
            connection = next((item for item in ready if item["connectionId"] == wanted), None)
            if connection is None:
                raise DictionaryError(
                    "Підключення моделі словника недоступне або не перевірене. Обери інше в ⚙ або перевір його в Connections.",
                    409, "dictionary_connection_unavailable",
                )
        else:
            connection = next((item for item in ready if item["providerId"] == "claude"), None) or (ready[0] if ready else None)
            if connection is None:
                raise DictionaryError("Немає підключення до Claude, GPT чи Gemini. Додай його в Connections.", 409, "dictionary_no_connection")
        model = (configuration.get("inventoryModel") if inventory else None) or configuration.get("model")
        if not (isinstance(model, str) and model.strip()):
            model = self._cheapest_model(connection)
        return connection, model.strip()

    def _cheapest_model(self, connection: dict[str, Any]) -> str:
        """The cheapest priced model of the connection's own list (input + output price); without any
        price the provider's default model, else the first one in the list."""
        try:
            models = list(self._list_models(connection["connectionId"]).get("models") or [])
        except Exception:
            models = []
        prices = self._storage.list_model_prices()
        priced = []
        for item in models:
            price = find_price(item["id"], prices)
            if price and price.get("inputPerMTok") is not None and price.get("outputPerMTok") is not None:
                priced.append((price["inputPerMTok"] + price["outputPerMTok"], item["id"]))
        if priced:
            return min(priced)[1]
        provider = self._registry.get(connection["providerId"])
        default = getattr(provider, "DEFAULT_TRANSLATION_MODEL", None)
        if isinstance(default, str) and default:
            return default
        if models:
            return models[0]["id"]
        raise DictionaryError("Не вдалося отримати список моделей. Обери модель словника в ⚙.", 502, "dictionary_models_unavailable")

    def _credentials(self, connection: dict[str, Any]):
        provider = self._registry.get(connection["providerId"])
        if provider is None or not hasattr(provider, "complete"):
            raise DictionaryError("Цей провайдер не підтримує словник. Обери Claude, GPT чи Gemini.", 400, "dictionary_provider_unsupported")
        if not self._vault.available:
            raise DictionaryError("Сховище ключів недоступне.", 503, "credential_storage_unavailable")
        record = self._storage.get_integration_connection_record(connection["connectionId"])
        try:
            return provider, self._vault.decrypt(record["credentialsCiphertext"])
        except (CredentialVaultError, TypeError) as error:
            raise DictionaryError("Збережені ключі недоступні.", 503, "credentials_locked") from error

    # ------------------------------------------------------------------ one model call

    def _ask(self, provider, credentials, model: str, system: str, user: str, parse: Callable[[Any], Any]) -> Any:
        reminder = ""
        for attempt in (1, 2):
            try:
                text, _served = provider.complete(
                    credentials,
                    TranslationRequest(text=user + reminder, target_language="UK", instructions=system, model=model),
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                )
            except ValueError as error:
                raise DictionaryError(f"Помилка моделі: {error}", 502, "dictionary_model_error") from error
            try:
                return parse(parse_json_object(text))
            except (ValueError, TypeError, KeyError, json.JSONDecodeError):
                logging.warning("Dictionary answer was not valid JSON (attempt %s, %s characters)", attempt, len(text))
                reminder = "\n\nПопередня відповідь не була валідним JSON за схемою. Поверни лише один JSON-об'єкт за схемою, без жодного іншого тексту."
        raise DictionaryError("Модель повернула відповідь у неправильному форматі. Спробуй ще раз.", 502, "dictionary_invalid_response")

    def _caller(self, connection: dict[str, Any], model: str, project_id: str, chapter_id: str | None):
        """ask(system, user, parse): credentials are read on the first call only (a cached answer needs none); every
        call is recorded as kind 'dictionary'. `ask.rows` collects the usage rows for the log."""
        state: dict[str, Any] = {}
        recorder = UsageRecorder(self._storage, project_id, chapter_id, connection["providerId"], "dictionary")

        def ask(system: str, user: str, parse: Callable[[Any], Any]) -> Any:
            if "provider" not in state:
                state["provider"], state["credentials"] = self._credentials(connection)
            with capture_usage(recorder):
                return self._ask(state["provider"], state["credentials"], model, system, user, parse)

        ask.recorder = recorder  # type: ignore[attr-defined]
        return ask

    # ------------------------------------------------------------------ the neutral part

    @staticmethod
    def _append_sense(inventory: dict[str, Any], sense: Mapping[str, Any], special: bool = False) -> str:
        """Adds a sense to the inventory (or returns the id of the one with the same gloss)."""
        key = normalize_variant(sense["gloss"])
        for existing in inventory["senses"]:
            if normalize_variant(existing["gloss"]) == key or (not special and not existing.get("special") and same_sense(existing, sense)):
                if normalize_variant(existing["gloss"]) != key:
                    merge_into(existing, sense)
                return existing["id"]
        number = 1 + max((int(item["id"][1:]) for item in inventory["senses"] if item["id"][1:].isdigit()), default=0)
        new_id = f"s{number}"
        inventory["senses"].append({"id": new_id, **dict(sense), **({"special": True} if special else {})})
        return new_id

    def _identify(self, ask, model: str, term: str, term_key: str, sentence_hash: str, prompt_mode: str, sentence: str, plain: str,
                  start: int, end: int, a: int) -> tuple[str, dict[str, Any], dict[str, Any], bool]:
        """(lemma key, inventory, analysis with senseId, whether the model was asked). The model sees the original only."""
        storage = self._storage
        lemma_key = storage.lemma_for_surface(term_key)
        inventory = storage.get_dictionary_senses(lemma_key) if lemma_key else None
        if inventory is not None:
            pick = storage.get_dictionary_pick(term_key, sentence_hash)
            ids = [sense["id"] for sense in inventory["senses"]]
            if pick and pick["inventoryVersion"] == inventory["version"] and pick.get("senseId") in ids:
                return lemma_key, inventory, pick, False
            return (lemma_key, *self._pick(ask, model, inventory, lemma_key, term, term_key, sentence_hash, prompt_mode, sentence, plain, start, end, a), True)

        full = ask(SYSTEM_FULL, build_user_message(term, prompt_mode, sentence, plain, start, end, a),
                   lambda data: validate_full(data, term))
        lemma_key = normalize_term(full["lemma"] or term) or term_key
        existing = storage.get_dictionary_senses(lemma_key)
        storage.set_surface(term_key, lemma_key)
        if existing is not None:  # another form of a known lemma: the stored inventory stays, only the sense is picked
            return (lemma_key, *self._pick(ask, model, existing, lemma_key, term, term_key, sentence_hash, prompt_mode, sentence, plain, start, end, a), True)
        inventory = {"senses": full["senses"], "extended": 0}
        version = storage.put_dictionary_senses(lemma_key, inventory, model)
        inventory["version"] = version
        analysis = {key: full[key] for key in ("term", "lemma", "pos", "termType", "expandedPhrase", "senseId")}
        storage.put_dictionary_pick(term_key, sentence_hash, version, analysis)
        return lemma_key, inventory, analysis, True

    def _pick(self, ask, model: str, inventory: dict[str, Any], lemma_key: str, term: str, term_key: str, sentence_hash: str,
              prompt_mode: str, sentence: str, plain: str, start: int, end: int, a: int) -> tuple[dict[str, Any], dict[str, Any]]:
        ids = [sense["id"] for sense in inventory["senses"]]
        answer = ask(SYSTEM_PICK, build_user_message(term, prompt_mode, sentence, plain, start, end, a, inventory),
                     lambda data: validate_pick(data, term, ids))
        if answer["senseId"] is None:  # none fits: the book's own meaning is added to the inventory, not the nearest one
            answer["senseId"] = self._append_sense(inventory, answer["newSense"], special=True)
            self._storage.put_dictionary_senses(lemma_key, inventory, model)
        analysis = {key: answer[key] for key in ("term", "lemma", "pos", "termType", "expandedPhrase", "senseId")}
        self._storage.put_dictionary_pick(term_key, sentence_hash, inventory["version"], analysis)
        return inventory, analysis

    def _extend(self, ask, model: str, lemma_key: str, term: str, inventory: dict[str, Any]) -> None:
        """«Ще значення»: rare senses are appended to the inventory for good (at most 3 times per lemma)."""
        if inventory.get("extended", 0) >= MAX_EXTENSIONS:
            raise DictionaryError("Більше значень немає: для одного слова можна попросити ще лише 3 рази.", 429, "dictionary_more_limit")
        extra = ask(SYSTEM_EXTEND, build_extension_message(term, inventory), validate_extension)
        for sense in extra:
            self._append_sense(inventory, sense)
        inventory["extended"] = inventory.get("extended", 0) + 1
        self._storage.put_dictionary_senses(lemma_key, inventory, model)

    @staticmethod
    def _compose(inventory: Mapping[str, Any], analysis: Mapping[str, Any], term: str, lemma_key: str) -> dict[str, Any]:
        """The neutral answer from the inventory: the chosen sense, its variants, the other senses. A translation
        variant is shown once in the whole answer."""
        senses = inventory["senses"]
        chosen = next(sense for sense in senses if sense["id"] == analysis["senseId"])
        shown: set[str] = set()
        translations = []
        for item in chosen["translations"]:
            key = normalize_variant(item["text"])
            if key not in shown:
                shown.add(key)
                translations.append(dict(item))
        chosen_gloss = normalize_variant(chosen["gloss"])
        others = []
        for sense in senses:
            if sense["id"] == chosen["id"] or normalize_variant(sense["gloss"]) == chosen_gloss:
                continue
            fresh = []
            for item in sense["translations"]:
                key = normalize_variant(item["text"])
                if key not in shown:
                    shown.add(key)
                    fresh.append(dict(item))
            if not fresh and not sense.get("special"):
                continue  # all its variants were shown above: the same meaning told twice
            others.append({"id": sense["id"], "gloss": sense["gloss"], "pos": ukrainian_pos(sense.get("pos")), "translations": fresh,
                           "special": bool(sense.get("special"))})
        return {
            "term": analysis.get("term") or term,
            "lemma": analysis.get("lemma") or lemma_key,
            "lemmaKey": lemma_key,
            "pos": ukrainian_pos(analysis.get("pos") or chosen.get("pos")),
            "termType": analysis["termType"],
            "expandedPhrase": analysis.get("expandedPhrase"),
            "senseId": chosen["id"],
            "meaningInContext": chosen["gloss"],
            "translations": translations,
            "otherSenses": others,
            "special": bool(chosen.get("special")),
            "examples": list(chosen.get("examples") or []),
            "inventoryVersion": inventory["version"],
        }

    # ------------------------------------------------------------------ lookup

    def _prepare(self, request: dict[str, Any]) -> dict[str, Any]:
        context = self._storage.paragraph_lookup_context(request["paragraphId"])
        project = self._storage.get_project(request["projectId"])
        if context is None or project is None or context["projectId"] != request["projectId"]:
            raise DictionaryError("Абзац не знайдено.", 404, "not_found")
        plain = plain_text(context["originalText"])
        start, end = self._locate(plain, request)
        term = plain[start:end]
        words = WORD_RE.findall(term)
        if len(term) > MAX_PHRASE_CHARS or len(words) > MAX_PHRASE_WORDS:
            raise DictionaryError("Виділіть коротшу фразу (до 8 слів).", 400, "dictionary_phrase_too_long")
        a, b = sentence_around(plain, start, end)
        return {"context": context, "project": project, "plain": plain, "start": start, "end": end, "term": term, "words": words,
                "a": a, "b": b, "sentence": plain[a:b]}

    def lookup(self, data: Any) -> dict[str, Any]:
        request = self._parse_request(data)
        prepared = self._prepare(request)
        context, project, plain = prepared["context"], prepared["project"], prepared["plain"]
        start, end, term, words, a, b, sentence = (prepared[key] for key in ("start", "end", "term", "words", "a", "b", "sentence"))
        mode = "more" if request["mode"] == "more" else ("word" if len(words) == 1 else "phrase")

        matches = glossary_matches(self._glossary_entries(project), plain)
        overlapping = [m for m in matches if m[0] < end and start < m[1]]
        glossary = [
            {"source": str(entry.get("source") or ""), "target": str(entry.get("target") or ""), "note": entry.get("note")}
            for _s, _e, entry in overlapping
        ]
        selection = {"start": start, "end": end, "term": term}
        # The sentence and where the term stands in it are worked out here on every lookup: they are not
        # cached and not logged (the client shows them as «У реченні: …»).
        base = {"mode": mode, "term": term, "selection": selection, "glossary": glossary, "expanded": None, "priceWarning": None,
                "sentence": sentence, "termStart": start - a, "termEnd": end - a}
        covering = [m for m in overlapping if m[0] <= start and end <= m[1]]
        if covering and mode != "more":
            self._log(request, term, sentence, "glossary", None, 0, 0)
            return {**base, "source": "glossary", "result": None, "model": None, "cached": False, "moreRemaining": MAX_EXTENSIONS}

        if mode != "more" and isinstance(data, dict) and data.get("allowModel") is False:
            # «without the model»: the glossary was the only thing that could answer; the client asks the model by a button
            self._log(request, term, sentence, "pending", None, 0, 0)
            return {**base, "source": "pending", "result": None, "model": None, "cached": False, "moreRemaining": MAX_EXTENSIONS}

        connection, model = self._resolve_model(project, inventory=True)
        term_key = normalize_term(term)
        sentence_hash = hashlib.sha256(normalize_term(sentence).encode("utf-8")).hexdigest()[:32]
        price = find_price(model, self._storage.list_model_prices())
        priced = bool(price) and price.get("inputPerMTok") is not None and price.get("outputPerMTok") is not None
        warning = None if priced else f"Для моделі {model} не задано ціну: вартість запитів словника не буде пораховано. Задай її в ⚙."

        ask = self._caller(connection, model, request["projectId"], context["chapterId"])
        prompt_mode = "word" if len(words) == 1 else "phrase"
        lemma_key, inventory, analysis, asked = self._identify(ask, model, term, term_key, sentence_hash, prompt_mode, sentence, plain, start, end, a)
        if mode == "more":
            self._extend(ask, model, lemma_key, term, inventory)
            asked = True
        answer = self._compose(inventory, analysis, term, lemma_key)
        source = "model" if asked else "cache"
        input_tokens = sum(row.get("inputTokens", 0) for row in ask.recorder.rows)
        output_tokens = sum(row.get("outputTokens", 0) for row in ask.recorder.rows)
        self._log(request, term, sentence, source, model if asked else model, input_tokens, output_tokens)
        answer["knownRenderings"] = self._extra_renderings(request["projectId"], lemma_key, inventory)
        return {**base, "mode": mode, "source": source, "result": answer, "model": model, "cached": not asked, "priceWarning": warning,
                "expanded": self._expanded(plain, a, b, start, end, answer),
                "moreRemaining": MAX_EXTENSIONS - inventory.get("extended", 0)}

    def refresh_senses(self, data: Any) -> dict[str, Any]:
        """«Оновити значення»: the lemma's inventory is made again from this sentence (original only); the sentence
        picks made with the old one stop counting. The answer is the new lookup."""
        request = self._parse_request({**(data if isinstance(data, dict) else {}), "mode": "word"})
        prepared = self._prepare(request)
        context, project, plain = prepared["context"], prepared["project"], prepared["plain"]
        start, end, term, words, a, sentence = (prepared[key] for key in ("start", "end", "term", "words", "a", "sentence"))
        connection, model = self._resolve_model(project, inventory=True)
        term_key = normalize_term(term)
        sentence_hash = hashlib.sha256(normalize_term(sentence).encode("utf-8")).hexdigest()[:32]
        prompt_mode = "word" if len(words) == 1 else "phrase"
        ask = self._caller(connection, model, request["projectId"], context["chapterId"])
        full = ask(SYSTEM_FULL, build_user_message(term, prompt_mode, sentence, plain, start, end, a), lambda data: validate_full(data, term))
        lemma_key = self._storage.lemma_for_surface(term_key) or normalize_term(full["lemma"] or term) or term_key
        self._storage.set_surface(term_key, lemma_key)
        inventory = {"senses": full["senses"], "extended": 0}
        inventory["version"] = self._storage.put_dictionary_senses(lemma_key, inventory, model, bump_version=True)
        analysis = {key: full[key] for key in ("term", "lemma", "pos", "termType", "expandedPhrase", "senseId")}
        self._storage.put_dictionary_pick(term_key, sentence_hash, inventory["version"], analysis)
        self._log(request, term, sentence, "model", model, sum(r.get("inputTokens", 0) for r in ask.recorder.rows),
                  sum(r.get("outputTokens", 0) for r in ask.recorder.rows))
        return self.lookup({**data, "mode": "word"})

    @staticmethod
    def _expanded(plain: str, a: int, b: int, start: int, end: int, answer: Mapping[str, Any]) -> dict[str, Any] | None:
        """Where the wider phrase the model named stands in the sentence, if it covers the selection."""
        phrase = answer.get("expandedPhrase")
        if not phrase or len(WORD_RE.findall(phrase)) > MAX_PHRASE_WORDS:
            return None
        words = phrase.translate(_APOSTROPHES).split()
        if not words:
            return None
        pattern = r"\s+".join(re.escape(word) for word in words)
        for match in re.finditer(pattern, plain[a:b].translate(_APOSTROPHES), re.IGNORECASE):
            s, e = a + match.start(), a + match.end()
            if s <= start and end <= e and (s, e) != (start, end):
                return {"start": s, "end": e, "text": plain[s:e]}
        return None

    # ------------------------------------------------------------------ the translation-aware part

    def _rendering_context(self, project: dict[str, Any], paragraph_id: str, plain: str) -> list[str]:
        """What may explain a translation: who speaks, the characters' speech, the glossary and the project rules."""
        lines: list[str] = []
        narrator = self._storage.paragraph_narrator_change(paragraph_id) or project.get("narratorGender")
        if narrator in NARRATOR_LABELS:
            lines.append(f"Оповідач абзацу: {NARRATOR_LABELS[narrator]}")
        entries = select_glossary_entries(self._glossary_entries(project))
        characters = [entry for entry in entries if is_character(entry)][:12]
        if characters:
            lines.append("Персонажі: " + "; ".join(
                f"{entry.get('source')} → {entry.get('target')}" + (f" (мовлення: {entry.get('speechRegister')})" if entry.get("speechRegister") else "")
                for entry in characters))
        hits = [entry for _s, _e, entry in glossary_matches(entries, plain)]
        if hits:
            lines.append("Глосарій у цьому абзаці: " + "; ".join(
                f"{entry.get('source')} → {entry.get('target')}" + (f" ({entry.get('note')})" if entry.get("note") else "") for entry in hits))
        rules = (project.get("translationRules") or "").strip()
        if rules:
            lines.append("Правила проєкту: " + " ".join(rules.split())[:1500])
        return lines

    def _extra_renderings(self, project_id: str, lemma_key: str, inventory: Mapping[str, Any]) -> list[str]:
        """Renderings used in this project that the inventory does not list: they enrich the variants."""
        listed = {rendering_lemma(item["text"]) for sense in inventory["senses"] for item in sense["translations"]}
        return [item["text"] for item in self._storage.list_known_renderings([project_id], lemma_key) if item["key"] not in listed]

    def candidate_renderings(self, project_ids: list[str], lemma_key: str, first_sense: str | None = None) -> list[str]:
        """Every Ukrainian rendering a paragraph can be checked against, without a model: the variants of all senses of the
        lemma's inventory (the chosen sense first) and the renderings known for the lemma in the projects."""
        inventory = self._storage.get_dictionary_senses(lemma_key)
        senses = sorted((inventory or {}).get("senses", []), key=lambda sense: sense["id"] != first_sense)
        texts = [item["text"] for sense in senses for item in sense["translations"]]
        texts += [item["text"] for item in self._storage.list_known_renderings(project_ids, lemma_key)]
        return list(dict.fromkeys(texts))

    def remember_rendering(self, project_id: str, lemma_key: str, rendering: str | None, translation: str, source: str) -> None:
        """A rendering seen in a translation (by a model or confirmed) becomes a known rendering of the lemma in the
        project, even when the inventory does not list it. Only when it really stands in the translation."""
        if rendering and rendering.strip() and occurs(translation, rendering):
            self._storage.add_known_rendering(project_id, lemma_key, rendering_lemma(rendering), rendering.strip().casefold(), source)

    def rendering(self, data: Any) -> dict[str, Any]:
        """«Як перекладено тут» and the optional reason and remarks. The only call that sees the translation; the
        neutral part never uses its answer. Cached per paragraph and translation text."""
        request = self._parse_request({**(data if isinstance(data, dict) else {}), "mode": "word"})
        lemma, sense_id = (data or {}).get("lemma"), (data or {}).get("senseId")
        if not isinstance(lemma, str) or not isinstance(sense_id, str):
            raise DictionaryError("Вкажіть лему і значення.", 400, "dictionary_invalid")
        prepared = self._prepare(request)
        context, project, plain = prepared["context"], prepared["project"], prepared["plain"]
        start, end, term, a, sentence = (prepared[key] for key in ("start", "end", "term", "a", "sentence"))
        lemma_key = normalize_term(lemma)
        inventory = self._storage.get_dictionary_senses(lemma_key)
        sense = next((item for item in (inventory or {}).get("senses", []) if item["id"] == sense_id), None)
        if sense is None:
            raise DictionaryError("Значення слова змінилося, торкніться слова ще раз.", 409, "dictionary_stale")
        translation = _TAG_RE.sub("", re.sub("[^]*", "", context["translationText"] or "")).strip()
        empty = {"rendering": None, "reason": None, "issues": [], "hasTranslation": bool(translation), "source": "none", "model": None}
        if not translation:
            return empty
        term_key = normalize_term(term)
        digest = f"{translation_hash(translation)}:{sense_id}"
        cached = self._storage.get_dictionary_rendering(request["projectId"], request["paragraphId"], term_key)
        if cached and cached["translationHash"] == digest and cached["source"] == "lookup" and cached["rendering"]:
            return {**empty, "rendering": cached["rendering"], "reason": cached["reason"], "issues": cached["issues"], "source": "cache",
                    "model": cached["model"]}  # a «not found» is never replayed: it is asked again
        project_ids = [request["projectId"]]
        found = align_candidates(translation, self.candidate_renderings(project_ids, lemma_key, sense_id))
        connection, model = self._resolve_model(project)
        known = [item["text"] for item in self._storage.list_known_renderings(project_ids, lemma_key)]
        lines = [
            f"Термін: {term}",
            f"Речення (термін позначено ⟦ ⟧): {_marked(sentence, start, end, a)}",
            f"Абзац оригіналу: {plain}",
            f"Переклад абзацу: {translation}",
            f"Значення за словником: {sense['gloss']}; відомі відповідники: " + "; ".join(item["text"] for item in sense["translations"]),
            *(f"Інше значення: {other['gloss']}; відповідники: " + "; ".join(item["text"] for item in other["translations"])
              for other in (inventory or {}).get("senses", []) if other["id"] != sense_id),
            *([f"Відомі в цьому проєкті відповідники: {'; '.join(known)}"] if known else []),
            *([f"Кандидат від програми (знайдено в перекладі): {found['text']}"] if found else []),
            *self._rendering_context(project, request["paragraphId"], plain),
        ]
        ask = self._caller(connection, model, request["projectId"], context["chapterId"])
        answer = ask(SYSTEM_RENDERING, "\n".join(lines), validate_rendering)
        # The model's word must stand in the translation; the program's single candidate fills in when it found nothing.
        if answer["rendering"] and not occurs(translation, answer["rendering"]):
            answer = {**answer, "rendering": None}
        if answer["rendering"] is None and found:
            answer = {**answer, "rendering": found["text"]}
        self._storage.put_dictionary_rendering(request["projectId"], request["paragraphId"], term_key, lemma_key, sense_id, digest,
                                               answer["rendering"], answer["reason"], answer["issues"], model, "lookup")
        self.remember_rendering(request["projectId"], lemma_key, answer["rendering"], translation, "model")
        self._log(request, term, sentence, "rendering", model, sum(r.get("inputTokens", 0) for r in ask.recorder.rows),
                  sum(r.get("outputTokens", 0) for r in ask.recorder.rows))
        return {**empty, **answer, "source": "model", "model": model}

    # ------------------------------------------------------------------ the same word in other chapters

    def _scan(self, project_id: str, lemma_key: str) -> dict[str, Any]:
        """Where the lemma stands in the book's originals and how each place was rendered, without any model: a rendering
        already stored (a lookup or an earlier «Визначити»), else a known variant of the lemma found in the translation."""
        inventory = self._storage.get_dictionary_senses(lemma_key)
        if inventory is None:
            raise DictionaryError("Спершу відкрийте слово у словнику.", 409, "dictionary_stale")
        variants = self.candidate_renderings([project_id], lemma_key)
        patterns = [(text, variant_pattern(text)) for text in variants]
        stored = {row["paragraphId"]: row for row in self._storage.list_dictionary_renderings(project_id, lemma_key)}
        pattern = original_pattern(lemma_key, self._storage.surfaces_of(lemma_key))
        groups: dict[str, dict[str, Any]] = {}
        unresolved: dict[str, Any] = {"paragraphs": 0, "chapters": {}, "ids": []}
        total = 0

        def add(bucket: dict[str, Any], paragraph: Mapping[str, Any]) -> None:
            chapter = bucket["chapters"].setdefault(paragraph["chapterIndex"], {"chapterIndex": paragraph["chapterIndex"], "title": paragraph["chapterTitle"], "count": 0})
            chapter["count"] += 1

        for paragraph in self._storage.list_project_paragraph_texts(project_id):
            original = plain_text(paragraph["originalText"])
            if not pattern.search(original):
                continue
            total += 1
            translation = _TAG_RE.sub("", re.sub("[^]*", "", paragraph["translationText"] or ""))
            rendering = None
            row = stored.get(paragraph["paragraphId"])
            if not translation.strip():
                unresolved["paragraphs"] += 1  # no translation yet: nothing to look at
                add(unresolved, paragraph)
                continue
            if row and row["rendering"] and row["translationHash"].split(":")[0] == translation_hash(translation.strip()):
                rendering = canonical_rendering(row["rendering"], variants)
            elif row and row["rendering"] is None and row["translationHash"].split(":")[0] == translation_hash(translation.strip()):
                unresolved["paragraphs"] += 1  # the model was asked already and found nothing: not asked again
                add(unresolved, paragraph)
                continue
            elif translation.strip():
                found = next((text for text, pat in patterns if pat and pat.search(translation)), None)
                rendering = found
            if rendering is None:
                unresolved["paragraphs"] += 1
                unresolved["ids"].append(paragraph["paragraphId"])
                add(unresolved, paragraph)
                continue
            bucket = groups.setdefault(rendering, {"text": rendering, "paragraphs": 0, "chapters": {}})
            bucket["paragraphs"] += 1
            add(bucket, paragraph)

        def finish(bucket: Mapping[str, Any]) -> dict[str, Any]:
            return {key: (sorted(value.values(), key=lambda item: item["chapterIndex"]) if key == "chapters" else value)
                    for key, value in bucket.items() if key != "ids"}

        return {
            "lemma": lemma_key,
            "total": total,
            "renderings": sorted((finish(group) for group in groups.values()), key=lambda group: (-group["paragraphs"], group["text"])),
            "unresolved": finish(unresolved),
            "resolvable": min(len(unresolved["ids"]), MAX_RESOLVE_PARAGRAPHS),
            "_ids": unresolved["ids"],
        }

    def occurrences(self, data: Any) -> dict[str, Any]:
        project_id, lemma = (data or {}).get("projectId") if isinstance(data, dict) else None, (data or {}).get("lemma") if isinstance(data, dict) else None
        if not isinstance(project_id, str) or not isinstance(lemma, str) or self._storage.get_project(project_id) is None:
            raise DictionaryError("Вкажіть проєкт і слово.", 400, "dictionary_invalid")
        report = self._scan(project_id, normalize_term(lemma))
        report.pop("_ids")
        return report

    def resolve_occurrences(self, data: Any) -> dict[str, Any]:
        """«Визначити решту моделлю»: one request for at most 20 paragraphs where no rendering is known yet."""
        project_id, lemma = (data or {}).get("projectId") if isinstance(data, dict) else None, (data or {}).get("lemma") if isinstance(data, dict) else None
        project = self._storage.get_project(project_id) if isinstance(project_id, str) else None
        if project is None or not isinstance(lemma, str):
            raise DictionaryError("Вкажіть проєкт і слово.", 400, "dictionary_invalid")
        lemma_key = normalize_term(lemma)
        report = self._scan(project_id, lemma_key)
        wanted = report["_ids"][:MAX_RESOLVE_PARAGRAPHS]
        if wanted:
            connection, model = self._resolve_model(project)
            texts = {item["paragraphId"]: item for item in self._storage.list_project_paragraph_texts(project_id)}
            pattern = original_pattern(lemma_key, self._storage.surfaces_of(lemma_key))
            lines = [f"Англійський термін: {lemma_key}"]
            numbered: dict[int, str] = {}
            for number, paragraph_id in enumerate(wanted, 1):
                item = texts[paragraph_id]
                original = plain_text(item["originalText"])
                a, b = sentence_around(original, *(lambda m: (m.start(), m.end()))(pattern.search(original)))
                translation = _TAG_RE.sub("", re.sub("[^]*", "", item["translationText"] or "")).strip()
                if not translation:
                    continue
                numbered[number] = paragraph_id
                lines.append(f"{number}. Оригінал: {original[a:b][:400]}\n   Переклад абзацу: {translation[:700]}")
            if numbered:
                ask = self._caller(connection, model, project_id, None)

                def parse(raw: Any) -> dict[int, str | None]:
                    items = raw.get("items") if isinstance(raw, dict) else None
                    if not isinstance(items, list):
                        raise ValueError("items")
                    return {int(item["n"]): _text(item.get("rendering"), 200) for item in items if isinstance(item, dict) and isinstance(item.get("n"), int)}

                answers = ask(SYSTEM_RESOLVE, "\n".join(lines), parse)
                for number, paragraph_id in numbered.items():
                    rendering = answers.get(number)
                    translation = texts[paragraph_id]["translationText"] or ""
                    cleaned = _TAG_RE.sub("", re.sub("[^]*", "", translation)).strip()
                    if rendering and not occurs(cleaned, rendering):
                        rendering = None
                    self.remember_rendering(project_id, lemma_key, rendering, cleaned, "model")
                    self._storage.put_dictionary_rendering(
                        project_id, paragraph_id, normalize_term(lemma_key), lemma_key, None, f"{translation_hash(cleaned)}:",
                        rendering, None, [], model, "resolve")
                logging.info("Dictionary resolve: project=%s paragraphs=%d inputTokens=%d outputTokens=%d", project_id, len(numbered),
                             sum(r.get("inputTokens", 0) for r in ask.recorder.rows), sum(r.get("outputTokens", 0) for r in ask.recorder.rows))
        report = self._scan(project_id, lemma_key)
        report.pop("_ids")
        return report

    @staticmethod
    def _log(request: dict[str, Any], term: str, sentence: str, source: str, model: str | None, input_tokens: int, output_tokens: int) -> None:
        logging.info(
            "Dictionary lookup: project=%s mode=%s source=%s termChars=%d sentenceChars=%d model=%s inputTokens=%d outputTokens=%d",
            request["projectId"], request["mode"], source, len(term), len(sentence), model or "-", input_tokens, output_tokens,
        )


__all__ = ["DictionaryError", "DictionaryService", "split_sentences", "plain_text", "glossary_matches", "validate_full", "validate_pick",
           "validate_rendering", "normalize_variant"]
