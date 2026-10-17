"""Translation memory: how the translator has already translated a word or phrase in all her books.

A reference for her only. It reads the paragraphs she marked «Перевірено» or «Вичитано» (her decisions, not raw
engine output) and never calls a model. It is deliberately isolated: this module is imported by the HTTP layer
alone, and no code that builds a prompt (translation, QA, chat, engine instructions, dictionary) reads from it, so
nothing found here can reach an engine. A word she wants an engine to keep goes into the glossary by her own hand.

Search: the FTS5 index of paragraphs (`book_paragraphs_fts`) gives candidates by prefix; every candidate is then
checked here in Python: whole words, the forms of the word (English regular and common irregular forms; Ukrainian
through pymorphy3), a phrase as an exact match without regard to case.

Highlight: the word is marked in the original; a rendering is marked in the translation only when the dictionary
knows it (`dictionary_renderings`) and the stored translation hash still equals the hash of the paragraph's current
translation. Otherwise the whole paragraph is shown without a mark.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any, Iterable, Mapping

try:
    from .dictionary_service import DictionaryError, DictionaryService, MAX_PHRASE_CHARS, MAX_PHRASE_WORDS, WORD_RE, english_forms, normalize_term, plain_text, translation_hash
    from .translations.glossary_check import _APOSTROPHES
except ImportError:  # launched as `python server.py` from inside backend/
    from dictionary_service import DictionaryError, DictionaryService, MAX_PHRASE_CHARS, MAX_PHRASE_WORDS, WORD_RE, english_forms, normalize_term, plain_text, translation_hash
    from translations.glossary_check import _APOSTROPHES

PAGE_SIZE = 20
MAX_PAGE_SIZE = 50
MAX_MATCHES = 2000  # how many matches are counted at most; «140+» beyond
MAX_QUERY_CHARS = 120
_CYRILLIC = re.compile(r"[Ѐ-ӿ]")
_MARKER = re.compile("[^]*")
_TAG = re.compile(r"<[^>]*>")
_FORM_TOKEN = re.compile(r"^[^\W_]+$")

# --- English: regular forms (dictionary_service.english_forms) and the common irregular ones -----------------

_IRREGULAR_VERBS = """be:am is are was were been being|have:has had having|do:does did done doing|go:goes went gone going|say:says said|get:gets got gotten getting|make:makes made making|know:knows knew known|think:thinks thought|take:takes took taken taking|see:sees saw seen|come:comes came coming|give:gives gave given giving|find:finds found|tell:tells told|feel:feels felt|leave:leaves left leaving|put:puts putting|mean:means meant|keep:keeps kept|let:lets letting|begin:begins began begun beginning|seem:seems|help:helps|show:shows showed shown|hear:hears heard|run:runs ran running|hold:holds held|bring:brings brought|write:writes wrote written writing|sit:sits sat sitting|stand:stands stood|lose:loses lost losing|pay:pays paid|meet:meets met|set:sets setting|lead:leads led|read:reads|grow:grows grew grown|speak:speaks spoke spoken|spend:spends spent|win:wins won winning|send:sends sent|build:builds built|fall:falls fell fallen|draw:draws drew drawn|break:breaks broke broken|buy:buys bought|wear:wears wore worn|choose:chooses chose chosen|eat:eats ate eaten|drive:drives drove driven|rise:rises rose risen|throw:throws threw thrown|catch:catches caught|sell:sells sold|fight:fights fought|hide:hides hid hidden|hang:hangs hung|shake:shakes shook shaken|sing:sings sang sung|swim:swims swam swum|sleep:sleeps slept|teach:teaches taught|wake:wakes woke woken|forget:forgets forgot forgotten|forgive:forgives forgave forgiven|beat:beats beaten|bite:bites bit bitten|blow:blows blew blown|burn:burns burnt|cut:cuts cutting|dig:digs dug digging|fly:flies flew flown|freeze:freezes froze frozen|hit:hits hitting|hurt:hurts|kneel:kneels knelt|lay:lays laid|lie:lies lay lain lying|light:lights lit|ride:rides rode ridden|ring:rings rang rung|seek:seeks sought|shoot:shoots shot|shut:shuts shutting|slide:slides slid|spin:spins spun|spread:spreads|steal:steals stole stolen|stick:sticks stuck|strike:strikes struck|swear:swears swore sworn|swing:swings swung|tear:tears tore torn|undergo:undergoes underwent|wind:winds wound"""
_IRREGULAR_NOUNS = "man:men|woman:women|child:children|foot:feet|tooth:teeth|mouse:mice|goose:geese|person:people|life:lives|wife:wives|knife:knives|wolf:wolves|leaf:leaves|half:halves|thief:thieves|shelf:shelves|ox:oxen|louse:lice|self:selves"


def _parse_irregular(table: str) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for entry in table.split("|"):
        lemma, _, forms = entry.partition(":")
        result[lemma] = {lemma, *forms.split()}
    return result


_LEMMA_FORMS = {**_parse_irregular(_IRREGULAR_VERBS), **_parse_irregular(_IRREGULAR_NOUNS)}
_FORM_TO_LEMMAS: dict[str, set[str]] = {}
for _lemma, _forms in _LEMMA_FORMS.items():
    for _form in _forms:
        _FORM_TO_LEMMAS.setdefault(_form, set()).add(_lemma)


def _candidate_bases(word: str) -> set[str]:
    """Possible dictionary forms of a regular inflected English word (the plural, -ed, -ing)."""
    bases = {word}
    if word.endswith("ies") and len(word) > 4:
        bases.add(word[:-3] + "y")
    if word.endswith("es") and len(word) > 3:
        bases |= {word[:-2], word[:-1]}
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        bases.add(word[:-1])
    if word.endswith("ied") and len(word) > 4:
        bases.add(word[:-3] + "y")
    if word.endswith("ed") and len(word) > 4:
        bases |= {word[:-2], word[:-1]}
        if word[-3] == word[-4]:
            bases.add(word[:-3])
    if word.endswith("ing") and len(word) > 5:
        bases |= {word[:-3], word[:-3] + "e"}
        if word[-4] == word[-5]:
            bases.add(word[:-4])
    return bases


def english_word_forms(word: str, known: Iterable[str] = ()) -> set[str]:
    """The tapped or typed English word with its forms: regular forms of the word and of the base it may come from,
    the irregular forms when it is one, and the forms the dictionary has seen (`known`)."""
    word = normalize_term(word)
    forms = {word, *known}
    for base in _candidate_bases(word):
        forms |= english_forms(base)
    for lemma in _FORM_TO_LEMMAS.get(word, ()):
        forms |= _LEMMA_FORMS[lemma] | english_forms(lemma)
    return {form for form in forms if form}


# --- Ukrainian: pymorphy3 ------------------------------------------------------------------------------------

_CASE_ENDINGS = tuple(sorted(("а", "у", "ові", "еві", "ом", "ем", "і", "е", "є", "ю", "ою", "ею", "єю", "ам", "ами", "ах", "ів", "ей", "и", "я", "ям", "ями", "ях", "ї"), key=len, reverse=True))


@lru_cache(maxsize=1)
def _analyzer():
    try:
        import pymorphy3
    except ImportError:
        return None
    return pymorphy3.MorphAnalyzer(lang="uk")


def ukrainian_stem(word: str) -> str:
    for ending in _CASE_ENDINGS:
        if word.endswith(ending) and len(word) - len(ending) >= 3:
            return word[: -len(ending)]
    return word


@lru_cache(maxsize=4096)
def ukrainian_forms(word: str) -> tuple[frozenset[str], str | None]:
    """(forms, stem): every form of the most probable lemmas of the word; for a word the analyzer does not know
    (a name), also its stem, which then matches by prefix."""
    word = word.casefold().translate(_APOSTROPHES)
    analyzer = _analyzer()
    forms = {word}
    stem = None
    if analyzer is None:
        return frozenset(forms), ukrainian_stem(word)
    parses = analyzer.parse(word)
    lemmas: list[Any] = []
    for parse in parses:  # all readings: «кочерги» is read first as a plural-only word, and only then as a form of «кочерга»
        if len(lemmas) < 4 and parse.normal_form not in {item.normal_form for item in lemmas} and (not lemmas or parse.score >= 0.3):
            lemmas.append(parse)
    for parse in lemmas:
        forms.update(form.word.translate(_APOSTROPHES) for form in parse.lexeme)
    if not parses or not parses[0].is_known:
        stem = ukrainian_stem(word)
    return frozenset(forms), stem


@lru_cache(maxsize=4096)
def canonical_rendering(text: str) -> str:
    """A rendering as one comparable string: the lemma of a single word (кочергу → кочерга), else the lowercase phrase."""
    words = WORD_RE.findall((text or "").translate(_APOSTROPHES))
    if len(words) == 1:
        analyzer = _analyzer()
        word = words[0].casefold()
        return analyzer.parse(word)[0].normal_form if analyzer else word
    return " ".join(word.casefold() for word in words) or (text or "").strip().casefold()


# --- the query -----------------------------------------------------------------------------------------------


class Query:
    """What is searched: the language (by Cyrillic), the pattern that finds it in a plain text, the FTS prefilter."""

    def __init__(self, text: str, known_forms: Iterable[str] = ()):
        words = WORD_RE.findall((text or "").translate(_APOSTROPHES))
        if not words:
            raise DictionaryError("Введіть слово або фразу.", 400, "memory_invalid")
        if len(text) > MAX_QUERY_CHARS or len(words) > MAX_PHRASE_WORDS:
            raise DictionaryError("Введіть коротшу фразу (до 8 слів).", 400, "memory_invalid")
        self.text = " ".join(words)
        self.language = "uk" if _CYRILLIC.search(text) else "en"
        self.phrase = len(words) > 1
        self.field = "translation_text" if self.language == "uk" else "original_text"
        stems: list[str] = []
        if self.phrase:
            self.forms = {self.text.casefold()}
            options = [r"\s+".join(re.escape(word.casefold()) for word in words)]
            self.fts = '"' + " ".join(word.casefold() for word in words).replace('"', '""') + '"'
        else:
            word = words[0].casefold()
            if self.language == "uk":
                forms, stem = ukrainian_forms(word)
                self.forms = set(forms)
                if stem:
                    stems.append(stem)
            else:
                self.forms = english_word_forms(word, known_forms)
            options = [re.escape(form) for form in sorted(self.forms, key=len, reverse=True)]
            tokens = {form for form in self.forms if _FORM_TOKEN.match(form)} | set(stems)
            self.fts = " OR ".join(f"{token}*" for token in sorted(tokens)) if tokens else '"' + word + '"'
            if stems:
                options.append(re.escape(stems[0]) + r"[\w'’]*")
        self.pattern = re.compile(r"(?<![\w'’])(?:" + "|".join(options) + r")(?![\w'’])", re.IGNORECASE)
        self.lemmas: set[str] = {canonical_rendering(self.text)} if self.language == "uk" else set()

    def ranges(self, text: str) -> list[list[int]]:
        return [[match.start(), match.end()] for match in self.pattern.finditer(text.translate(_APOSTROPHES))]


def clean_original(original: str | None) -> str:
    return _MARKER.sub("", plain_text(original or ""))


def clean_translation(translation: str | None) -> str:
    return _TAG.sub("", _MARKER.sub("", translation or "")).strip()


def _ranges_of(text: str, needle: str) -> list[list[int]]:
    if not needle.strip():
        return []
    pattern = re.compile(r"(?<![\w'’])" + r"\s+".join(re.escape(part) for part in needle.translate(_APOSTROPHES).split()) + r"(?![\w'’])", re.IGNORECASE)
    return [[match.start(), match.end()] for match in pattern.finditer(text.translate(_APOSTROPHES))]


class TranslationMemory:
    def __init__(self, storage: Any):
        self._storage = storage

    # ------------------------------------------------------------------ the request

    @staticmethod
    def _tapped_term(plain: str, data: Mapping[str, Any]) -> str:
        """The word or phrase under the tap, found the way the dictionary finds it."""
        start, end, text = data.get("offsetStart"), data.get("offsetEnd"), data.get("text")
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (start, end)) or start < 0 or end <= start or not isinstance(text, str):
            raise DictionaryError("Некоректне місце в абзаці.", 400, "memory_invalid")
        first, last = DictionaryService._locate(plain, {"start": start, "end": end, "text": text})
        term = plain[first:last]
        if len(term) > MAX_PHRASE_CHARS or len(WORD_RE.findall(term)) > MAX_PHRASE_WORDS:
            raise DictionaryError("Виділіть коротшу фразу (до 8 слів).", 400, "dictionary_phrase_too_long")
        return term

    def search(self, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise DictionaryError("Некоректний запит.", 400, "memory_invalid")
        project_id, paragraph_id = data.get("projectId"), data.get("paragraphId")
        if not isinstance(project_id, str) or self._storage.get_project(project_id) is None:
            raise DictionaryError("Проєкт не знайдено.", 404, "not_found")
        offset, limit = data.get("offset", 0), data.get("limit", PAGE_SIZE)
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (offset, limit)) or offset < 0 or limit < 1:
            raise DictionaryError("Некоректний діапазон.", 400, "memory_invalid")
        limit = min(limit, MAX_PAGE_SIZE)
        exclude = None
        query_text = data.get("query")
        if isinstance(query_text, str) and query_text.strip():
            term, source = query_text.strip(), "query"
        else:
            if not isinstance(paragraph_id, str):
                raise DictionaryError("Вкажіть абзац або запит.", 400, "memory_invalid")
            context = self._storage.paragraph_lookup_context(paragraph_id)
            if context is None or context["projectId"] != project_id:
                raise DictionaryError("Абзац не знайдено.", 404, "not_found")
            term, source = self._tapped_term(plain_text(context["originalText"]), data), "tap"
            exclude = paragraph_id
        term_key = normalize_term(term)
        lemma_key = self._storage.lemma_for_surface(term_key) if not _CYRILLIC.search(term) else None
        known = self._storage.surfaces_of(lemma_key) if lemma_key else []
        query = Query(term, [*known, *( [lemma_key] if lemma_key else [])])
        return self._run(project_id, query, term, source, lemma_key, exclude, offset, limit)

    # ------------------------------------------------------------------ the search

    def _candidates(self, project_id: str, query: Query, exclude: str | None):
        project = self._storage.get_project(project_id)
        series_id = project.get("seriesId") if project else None
        with self._storage.connection() as connection:
            cursor = connection.execute(
                "SELECT bp.paragraph_id, bp.chapter_id, bp.paragraph_index, ch.chapter_index, ch.title AS chapter_title, ch.translation_title, "
                "doc.project_id, proj.title AS project_title, proj.series_id, bp.original_text, bp.translation_text, "
                "CASE WHEN proj.project_id = :current THEN 0 WHEN :series IS NOT NULL AND proj.series_id = :series THEN 1 ELSE 2 END AS rank "
                "FROM book_paragraphs_fts JOIN book_paragraphs bp ON bp.rowid = book_paragraphs_fts.rowid "
                "JOIN book_chapters ch ON ch.chapter_id = bp.chapter_id JOIN book_documents doc ON doc.book_id = ch.book_id "
                "JOIN book_projects proj ON proj.project_id = doc.project_id "
                f"WHERE book_paragraphs_fts MATCH :match AND bp.is_service = 0 AND (bp.reviewed = 1 OR bp.proofread = 1) "
                "AND TRIM(COALESCE(bp.translation_text, '')) != '' AND (:exclude IS NULL OR bp.paragraph_id != :exclude) "
                "ORDER BY rank, CASE WHEN rank = 1 THEN COALESCE(proj.book_number, 999999) ELSE 0 END, proj.title, "
                "ch.chapter_index, bp.paragraph_index",
                {"current": project_id, "series": series_id, "match": f"{query.field}:({query.fts})", "exclude": exclude},
            )
            for row in cursor:
                yield row

    def _renderings(self, paragraph_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
        found: dict[str, list[dict[str, Any]]] = {}
        with self._storage.connection() as connection:
            for index in range(0, len(paragraph_ids), 400):
                chunk = paragraph_ids[index:index + 400]
                rows = connection.execute(
                    f"SELECT paragraph_id, term_key, lemma_key, rendering, translation_hash FROM dictionary_renderings "
                    f"WHERE paragraph_id IN ({','.join('?' * len(chunk))})", chunk,
                ).fetchall()
                for row in rows:
                    found.setdefault(row["paragraph_id"], []).append(dict(row))
        return found

    def _run(self, project_id: str, query: Query, term: str, source: str, lemma_key: str | None, exclude: str | None,
             offset: int, limit: int) -> dict[str, Any]:
        matches: list[dict[str, Any]] = []
        for row in self._candidates(project_id, query, exclude):
            original, translation = clean_original(row["original_text"]), clean_translation(row["translation_text"])
            text = translation if query.language == "uk" else original
            ranges = query.ranges(text)
            if not ranges:
                continue
            matches.append({"row": row, "original": original, "translation": translation, "ranges": ranges})
            if len(matches) >= MAX_MATCHES:
                break
        rendering_rows = self._renderings([match["row"]["paragraph_id"] for match in matches])
        english_keys = {normalize_term(form) for form in query.forms} if query.language == "en" else set()
        wanted_lemmas = {lemma_key, normalize_term(term)} - {None} if query.language == "en" else set()
        groups: dict[str, int] = {}
        unresolved = 0
        items: list[dict[str, Any]] = []
        for position, match in enumerate(matches):
            row = match["row"]
            digest = translation_hash(match["translation"])
            known = None
            for stored in rendering_rows.get(row["paragraph_id"], []):
                if stored["translation_hash"].split(":")[0] != digest or not stored["rendering"]:
                    continue
                if query.language == "en" and (stored["lemma_key"] in wanted_lemmas or stored["term_key"] in english_keys):
                    known = {"rendering": stored["rendering"], "termKey": stored["term_key"]}
                    break
                if query.language == "uk" and canonical_rendering(stored["rendering"]) in query.lemmas:
                    known = {"rendering": stored["rendering"], "termKey": stored["term_key"]}
                    break
            if query.language == "en":
                if known:
                    label = canonical_rendering(known["rendering"])
                    groups[label] = groups.get(label, 0) + 1
                else:
                    unresolved += 1
            if not offset <= position < offset + limit:
                continue
            if query.language == "en":
                original_ranges = match["ranges"]
                translation_ranges = _ranges_of(match["translation"], known["rendering"]) if known else []
            else:
                translation_ranges = match["ranges"]
                original_ranges = _ranges_of(match["original"], known["termKey"]) if known else []
            items.append({
                "paragraphId": row["paragraph_id"], "chapterId": row["chapter_id"], "chapterIndex": row["chapter_index"],
                "chapterTitle": row["translation_title"] or row["chapter_title"], "projectId": row["project_id"],
                "projectTitle": row["project_title"], "scope": ("current", "series", "other")[row["rank"]],
                "original": match["original"], "translation": match["translation"],
                "originalRanges": original_ranges, "translationRanges": translation_ranges,
                "rendering": known["rendering"] if known else None,
            })
        summary = None
        if query.language == "en" and groups:
            summary = {"groups": [{"text": text, "count": count} for text, count in sorted(groups.items(), key=lambda item: (-item[1], item[0]))],
                       "unresolved": unresolved}
        return {
            "term": term, "source": source, "language": query.language, "phrase": query.phrase,
            "sourceTerm": (lemma_key or query.text.casefold()) if query.language == "en" else None,
            "total": len(matches), "capped": len(matches) >= MAX_MATCHES, "offset": offset,
            "hasMore": offset + limit < len(matches), "items": items, "summary": summary,
        }


__all__ = ["TranslationMemory", "Query", "english_word_forms", "ukrainian_forms", "canonical_rendering"]
