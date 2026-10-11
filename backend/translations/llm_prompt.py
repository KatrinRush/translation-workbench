"""Prompt construction for LLM (Claude) chapter translation.

Split into a system prompt and a per-batch user message on purpose: the system
prompt carries everything that is the same for every batch of a project
(format contract, dialogue convention, glossary, characters, rules) and is
sent with cache_control, so it must be byte-identical between batches — keep
it free of anything batch-specific and keep every list in a stable order.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from .narrator import NARRATOR_LABELS

_CHARACTER_GENDER_LABELS = {
    "masc": "чоловічий рід",
    "femn": "жіночий рід",
    "plur": "множина",
}

_FORMAT_RULES = """\
Ти — досвідчений літературний перекладач художньої прози з англійської на українську.

ФОРМАТ (суворо):
- Вхідний текст для перекладу — XML-елемент <chunk>, що містить абзаци <p id="…">.
- Поверни ЛИШЕ один елемент <chunk> з тими самими <p id="…"> у тому самому порядку: кожен id рівно один раз, без нових, пропущених, об'єднаних чи розділених абзаців.
- Значення атрибутів id копіюй без змін. Порожній абзац лишай порожнім.
- Теги форматування <b>, <i>, <s> всередині абзацу збережи навколо відповідних перекладених слів.
- Не додавай жодного тексту поза <chunk>: без пояснень, коментарів, markdown-огорожі.
- Блоки контексту в повідомленні (попередні абзаци оригіналу й перекладу) НЕ перекладай і НЕ повертай — вони лише для узгодженості імен, тону й сюжету.

ДІАЛОГИ (українська традиція):
- Пряму мову оформлюй через тире (—), без лапок, у межах того самого <p> (абзаци не розділяй).
- Слова автора відокремлюй тире з комами за українськими правилами.
- Приклад: "Go," he said. "Now." → — Іди, — сказав він. — Негайно.
- Приклад: She asked, "Why?" → Вона спитала: — Чому?
- Лапки «» лишай тільки для цитат, назв і думок, які в оригіналі не є репліками діалогу.

СТИЛЬ:
- Перекладай природною літературною українською, зберігаючи зміст, тон, конотацію й конкретику дієслів оригіналу; ідіоми передавай функціональними українськими відповідниками.
- Рід і особу оповідача в наративних реченнях узгоджуй зі статтю оповідача, вказаною для кожного абзацу (це не стосується реплік персонажів).
- Глосарій проєкту обов'язковий: терміни й імена перекладай саме так, як у глосарії, змінюючи лише відмінкові форми (крім незмінюваних)."""


def _clean(value: Any) -> str:
    return " ".join(str(value).split()) if value is not None else ""


def build_system_prompt(
    glossary_entries: Iterable[Mapping[str, Any]],
    catalog_rules: Iterable[Mapping[str, Any]],
    translation_rules: str | None,
) -> str:
    """Stable, cacheable instructions for every batch of a project."""
    entries = sorted(
        (entry for entry in glossary_entries if entry.get("active", True) and _clean(entry.get("source")) and _clean(entry.get("target"))),
        key=lambda entry: (_clean(entry.get("source")).casefold(), _clean(entry.get("target"))),
    )
    characters = [entry for entry in entries if entry.get("characterGender") or entry.get("speechRegister")]
    terms = [entry for entry in entries if not (entry.get("characterGender") or entry.get("speechRegister"))]

    def term_line(entry: Mapping[str, Any]) -> str:
        line = f"- {_clean(entry['source'])} → {_clean(entry['target'])}"
        if entry.get("indeclinable"):
            line += " (не відмінюється)"
        if _clean(entry.get("note")):
            line += f" — {_clean(entry.get('note'))}"
        return line

    def character_line(entry: Mapping[str, Any]) -> str:
        parts = [f"- {_clean(entry['source'])} → {_clean(entry['target'])}"]
        gender = _CHARACTER_GENDER_LABELS.get(entry.get("characterGender"))
        if gender:
            parts.append(f"рід: {gender}")
        if _clean(entry.get("speechRegister")):
            parts.append(f"мовний регістр: {_clean(entry.get('speechRegister'))}")
        if entry.get("indeclinable"):
            parts.append("не відмінюється")
        if _clean(entry.get("note")):
            parts.append(f"примітка: {_clean(entry.get('note'))}")
        return "; ".join(parts)

    rules = sorted(
        (rule for rule in catalog_rules if rule.get("active", True) and _clean(rule.get("text"))),
        key=lambda rule: (str(rule.get("priority") or ""), _clean(rule.get("text"))),
    )
    rule_lines = [f"- {_clean(rule['text'])}" for rule in rules]
    project_rules = (translation_rules or "").strip()

    sections = [
        _FORMAT_RULES,
        "ПЕРСОНАЖІ (ім'я в оригіналі → в перекладі; граматичний рід; мовний регістр — витримуй його в репліках персонажа):\n"
        + ("\n".join(character_line(entry) for entry in characters) or "Немає."),
        "ГЛОСАРІЙ ПРОЄКТУ (оригінал → переклад):\n" + ("\n".join(term_line(entry) for entry in terms) or "Немає."),
        "ПРАВИЛА ПЕРЕКЛАДУ ПРОЄКТУ:\n" + ("\n".join(filter(None, [*rule_lines, project_rules])) or "Немає."),
    ]
    return "\n\n".join(sections)


def build_user_message(
    chunk_xml: str,
    paragraph_ids: Sequence[str],
    narrators: Mapping[str, str | None],
    source_context: Sequence[str],
    translated_context: Sequence[str],
) -> str:
    """Batch-specific part: preceding context, per-paragraph narrator, the chunk itself."""
    narrator_lines = [
        f"[{paragraph_id}]: оповідач — {NARRATOR_LABELS[narrators[paragraph_id]]}"
        for paragraph_id in paragraph_ids
        if narrators.get(paragraph_id) in NARRATOR_LABELS
    ]
    parts = []
    if source_context:
        parts.append(
            "ПОПЕРЕДНІЙ КОНТЕКСТ — ОРИГІНАЛ (не перекладати):\n<context_source>\n"
            + "\n\n".join(source_context)
            + "\n</context_source>"
        )
    if translated_context:
        parts.append(
            "ПОПЕРЕДНІЙ КОНТЕКСТ — ВЖЕ ПЕРЕКЛАДЕНО (не повторювати; витримуй ті самі імена й тон):\n<context_translation>\n"
            + "\n\n".join(translated_context)
            + "\n</context_translation>"
        )
    parts.append(
        "СТАТЬ/ОСОБА ОПОВІДАЧА для наративних речень кожного абзацу:\n"
        + ("\n".join(narrator_lines) if narrator_lines else "(не позначено — не роби припущень про стать оповідача)")
    )
    parts.append("Переклади цей фрагмент:\n" + chunk_xml)
    return "\n\n".join(parts)


__all__ = ["build_system_prompt", "build_user_message"]
