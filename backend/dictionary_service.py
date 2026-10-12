"""Dictionary lookups for the original column: a word or phrase in its sentence.

Order of a lookup: (1) the project glossary, longest match, answered without the model;
(2) the dictionary_cache; (3) one model call with the sentence, the whole paragraph and the chosen
translation of the paragraph. The model answers strict JSON, validated here; one retry when it is
not valid. Every call is recorded in translation_usage with kind 'dictionary'.

Privacy: the logs carry only lengths and token counts, never book text.
"""

from __future__ import annotations

import hashlib
import html
import json
import logging
import re
from typing import Any, Callable, Mapping

from .integrations.base import TranslationRequest
from .integrations.credentials import CredentialVault, CredentialVaultError
from .integrations.registry import ProviderRegistry
from .translations.glossary_check import _APOSTROPHES
from .translations.llm_prompt import select_glossary_entries
from .usage import UsageRecorder, capture_usage, find_price

LLM_PROVIDERS = ("claude", "openai", "gemini")
MODES = ("word", "phrase", "more")
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


# --- the model's answer ---------------------------------------------------------------------


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


def validate_answer(data: Any, fallback_term: str) -> dict[str, Any]:
    """The model's JSON -> the answer shape, or ValueError."""
    if not isinstance(data, dict):
        raise ValueError("not an object")
    term_type = data.get("termType")
    if term_type not in TERM_TYPES:
        raise ValueError("bad termType")
    translations = data.get("translations")
    if not isinstance(translations, list) or not translations:
        raise ValueError("translations")
    cleaned_translations = []
    for item in translations[:5]:
        if not isinstance(item, dict):
            raise ValueError("translation item")
        cleaned_translations.append({"text": _text(item.get("text"), 80, required=True), "register": _text(item.get("register"), 40)})
    examples = data.get("examples", [])
    if examples is None:
        examples = []
    if not isinstance(examples, list):
        raise ValueError("examples")
    cleaned_examples = []
    for item in examples[:2]:
        if not isinstance(item, dict):
            raise ValueError("example item")
        cleaned_examples.append({"en": _text(item.get("en"), 300, required=True), "uk": _text(item.get("uk"), 300, required=True)})
    return {
        "term": _text(data.get("term"), 120) or fallback_term,
        "lemma": _text(data.get("lemma"), 120),
        "pos": _text(data.get("pos"), 40),
        "termType": term_type,
        "expandedPhrase": _text(data.get("expandedPhrase"), 120),
        "meaningInContext": _text(data.get("meaningInContext"), 400, required=True),
        "translations": cleaned_translations,
        "registerNote": _text(data.get("registerNote"), 80),
        "inThisTranslation": _text(data.get("inThisTranslation"), 200),
        "examples": cleaned_examples,
    }


def parse_answer_json(text: str, fallback_term: str) -> dict[str, Any]:
    stripped = text.strip()
    stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", stripped)
    first, last = stripped.find("{"), stripped.rfind("}")
    if first < 0 or last <= first:
        raise ValueError("no JSON object")
    return validate_answer(json.loads(stripped[first:last + 1]), fallback_term)


SYSTEM_PROMPT = """Ти — англо-український словник для перекладача художньої книжки. Користувач вказує слово або фразу в реченні з книжки.
Відповідай ЛИШЕ одним JSON-об'єктом, без markdown і без пояснень. Усі пояснення — українською. Поля term, lemma, expandedPhrase, examples[].en — англійською.
Схема відповіді:
{"term": "слово чи фраза так, як вона стоїть у реченні",
 "lemma": "початкова форма слова чи фрази",
 "pos": "частина мови українською (іменник, дієслово, прикметник, прислівник, фразове дієслово, ідіома…)",
 "termType": "word | phrase | idiom | phrasal_verb",
 "expandedPhrase": "ширша усталена фраза, ідіома чи фразове дієслово, до якої входить слово в цьому реченні, інакше null",
 "meaningInContext": "значення саме в цьому реченні, коротко, українською",
 "translations": [{"text": "переклад", "register": "розмовне | груба лексика | застаріле | формальне | null"}],
 "registerNote": "розмовне / груба лексика / застаріле / формальне або null",
 "inThisTranslation": "яким словом чи фразою це передано в поточному перекладі абзацу, або null, якщо не знайдено",
 "examples": [{"en": "приклад", "uk": "переклад прикладу"}]}
Правила: translations — від 1 до 5 найточніших українських відповідників, першим — значення з цього речення; examples — до 2 коротких прикладів. Не вигадуй нічого, чого не знаєш: краще менше значень. Якщо слово входить в ідіому чи фразове дієслово, поясни саме її значення й заповни expandedPhrase."""


def build_user_message(term: str, effective_mode: str, sentence: str, paragraph: str, translation: str | None,
                       start: int, end: int, sentence_start: int, exclude: list[str]) -> str:
    marked = sentence[:start - sentence_start] + "⟦" + sentence[start - sentence_start:end - sentence_start] + "⟧" + sentence[end - sentence_start:]
    lines = [
        f"Термін: {term}",
        f"Що це: {'фраза' if effective_mode == 'phrase' else 'слово'}",
        f"Речення (термін позначено ⟦ ⟧): {marked}",
    ]
    if sentence.strip() != paragraph.strip():
        lines.append(f"Увесь абзац (контекст): {paragraph}")
    lines.append(f"Поточний переклад абзацу: {translation.strip() if translation and translation.strip() else '(ще нема)'}")
    if exclude:
        lines.append("Дай ІНШІ значення, яких ще не було. Уже показано (не повторюй): " + "; ".join(exclude))
    return "\n".join(lines)


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

    def _resolve_model(self, project: dict[str, Any]) -> tuple[dict[str, Any], str]:
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
        model = configuration.get("model")
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

    def _ask(self, provider, credentials, model: str, user: str, fallback_term: str) -> dict[str, Any]:
        reminder = ""
        for attempt in (1, 2):
            try:
                text, _served = provider.complete(
                    credentials,
                    TranslationRequest(text=user + reminder, target_language="UK", instructions=SYSTEM_PROMPT, model=model),
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                )
            except ValueError as error:
                raise DictionaryError(f"Помилка моделі: {error}", 502, "dictionary_model_error") from error
            try:
                return parse_answer_json(text, fallback_term)
            except (ValueError, json.JSONDecodeError):
                logging.warning("Dictionary answer was not valid JSON (attempt %s, %s characters)", attempt, len(text))
                reminder = "\n\nПопередня відповідь не була валідним JSON за схемою. Поверни лише один JSON-об'єкт за схемою, без жодного іншого тексту."
        raise DictionaryError("Модель повернула відповідь у неправильному форматі. Спробуй ще раз.", 502, "dictionary_invalid_response")

    # ------------------------------------------------------------------ lookup

    def lookup(self, data: Any) -> dict[str, Any]:
        request = self._parse_request(data)
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
        mode = "more" if request["mode"] == "more" else ("word" if len(words) == 1 else "phrase")
        a, b = sentence_around(plain, start, end)
        sentence = plain[a:b]

        matches = glossary_matches(self._glossary_entries(project), plain)
        overlapping = [m for m in matches if m[0] < end and start < m[1]]
        glossary = [
            {"source": str(entry.get("source") or ""), "target": str(entry.get("target") or ""), "note": entry.get("note")}
            for _s, _e, entry in overlapping
        ]
        selection = {"start": start, "end": end, "term": term}
        base = {"mode": mode, "term": term, "selection": selection, "glossary": glossary, "expanded": None, "priceWarning": None}
        covering = [m for m in overlapping if m[0] <= start and end <= m[1]]
        if covering and mode != "more":
            self._log(request, term, sentence, "glossary", None, 0, 0)
            return {**base, "source": "glossary", "result": None, "model": None, "cached": False, "moreRemaining": MAX_MORE_REQUESTS}

        connection, model = self._resolve_model(project)
        term_key = normalize_term(term)
        sentence_hash = hashlib.sha256(normalize_term(sentence).encode("utf-8")).hexdigest()[:32]
        cached_rows = self._storage.list_dictionary_cache(term_key, sentence_hash, model)
        more_rows = [row for row in cached_rows if row[0].startswith("more")]
        price = find_price(model, self._storage.list_model_prices())
        priced = bool(price) and price.get("inputPerMTok") is not None and price.get("outputPerMTok") is not None
        warning = None if priced else f"Для моделі {model} не задано ціну: вартість запитів словника не буде пораховано. Задай її в ⚙."

        if mode != "more":
            cached = next((row[1] for row in cached_rows if row[0] == mode), None)
            if cached is not None:
                self._log(request, term, sentence, "cache", model, 0, 0)
                return {**base, "source": "cache", "result": cached, "model": model, "cached": True, "priceWarning": warning,
                        "expanded": self._expanded(plain, a, b, start, end, cached),
                        "moreRemaining": MAX_MORE_REQUESTS - len(more_rows)}
            cache_mode = mode
            exclude: list[str] = []
        else:
            if len(more_rows) >= MAX_MORE_REQUESTS:
                raise DictionaryError("Більше значень немає: для одного слова можна попросити ще лише 3 рази.", 429, "dictionary_more_limit")
            cache_mode = f"more{len(more_rows) + 1}"
            exclude = [item["text"] for _mode, response in cached_rows for item in response.get("translations", [])]

        provider, credentials = self._credentials(connection)
        prompt_mode = "word" if len(words) == 1 else "phrase"
        user = build_user_message(term, prompt_mode, sentence, plain, context["translationText"], start, end, a, exclude)
        recorder = UsageRecorder(self._storage, request["projectId"], context["chapterId"], connection["providerId"], "dictionary")
        with capture_usage(recorder):
            answer = self._ask(provider, credentials, model, user, term)
        self._storage.put_dictionary_cache(term_key, sentence_hash, model, cache_mode, answer)
        input_tokens = sum(row.get("inputTokens", 0) for row in recorder.rows)
        output_tokens = sum(row.get("outputTokens", 0) for row in recorder.rows)
        self._log(request, term, sentence, "model", model, input_tokens, output_tokens)
        used_more = len(more_rows) + (1 if cache_mode.startswith("more") else 0)
        return {**base, "mode": mode, "source": "model", "result": answer, "model": model, "cached": False, "priceWarning": warning,
                "expanded": self._expanded(plain, a, b, start, end, answer), "moreRemaining": MAX_MORE_REQUESTS - used_more}

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

    @staticmethod
    def _log(request: dict[str, Any], term: str, sentence: str, source: str, model: str | None, input_tokens: int, output_tokens: int) -> None:
        logging.info(
            "Dictionary lookup: project=%s mode=%s source=%s termChars=%d sentenceChars=%d model=%s inputTokens=%d outputTokens=%d",
            request["projectId"], request["mode"], source, len(term), len(sentence), model or "-", input_tokens, output_tokens,
        )


__all__ = ["DictionaryError", "DictionaryService", "split_sentences", "plain_text", "glossary_matches", "validate_answer"]
