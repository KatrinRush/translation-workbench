"""Patch 24: fix two footnote bugs found in testing (after patch 21-22):

1. The marker was a tiny filled badge (10px, boxed) — the number inside was
   basically unreadable on mobile. Now it's a plain superscript number at
   normal text size (browsers shrink <sup> by default via font-size:smaller
   in the UA stylesheet — this overrides that back to 1em).

2. Clicking a marker right after creating it (same session, before reload)
   showed an empty textarea instead of the note just typed. Cause: the
   in-memory paragraph.footnotes list (read from the last full page load)
   was never updated when a footnote was created/edited client-side, so the
   click handler's lookup found nothing. Now create/edit both keep that
   in-memory list in sync, so re-clicking within the same session works
   immediately, without needing a reload.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
_IGNORED_PARTS = {"node_modules", ".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".cache"}
_LIKELY_DIRS = [".", "frontend", "backend", "static", "public", "web", "app"]


def _find(filename: str) -> Path:
    for directory in _LIKELY_DIRS:
        candidate = REPO_ROOT / directory / filename
        if candidate.is_file():
            return candidate
    candidates = [
        path for path in REPO_ROOT.rglob(filename)
        if not any(part in _IGNORED_PARTS for part in path.parts)
    ]
    if not candidates:
        raise SystemExit(f"Could not find {filename} under {REPO_ROOT} — aborting.")
    if len(candidates) > 1:
        raise SystemExit(f"Found more than one {filename}: {candidates} — aborting, resolve manually.")
    return candidates[0]


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"{label}: expected text not found — file may have changed, aborting.")
    if text.count(old) > 1:
        raise SystemExit(f"{label}: expected text is not unique — aborting to avoid a wrong edit.")
    return text.replace(old, new, 1)


def patch_styles_css() -> None:
    path = _find("styles.css")
    text = path.read_text(encoding="utf-8")
    text = _replace_once(
        text,
        '''.footnote-marker {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 15px;
    height: 15px;
    padding: 0 3px;
    margin: 0 1px;
    border-radius: 4px;
    background: var(--color-warning-bg-subtle);
    border: 1px solid var(--color-warning-border-subtle);
    color: var(--color-warning-text);
    font-size: 10px;
    font-weight: 600;
    line-height: 1;
    cursor: pointer;
    user-select: none;
    vertical-align: super;
}

.footnote-marker:hover {
    background: var(--color-warning-border-subtle);
}''',
        '''.footnote-marker {
    /* Browsers shrink <sup> by default (font-size: smaller in the UA
       stylesheet) — cancel that so the number reads at normal text size. */
    font-size: 1em;
    font-weight: 700;
    color: var(--color-warning-text);
    padding: 0 2px;
    cursor: pointer;
    user-select: none;
    vertical-align: super;
    text-decoration: underline;
    text-decoration-color: var(--color-warning-border-subtle);
    text-decoration-thickness: 2px;
}

.footnote-marker:hover {
    color: var(--color-warning);
}''',
        "footnote-marker CSS size fix",
    )
    path.write_text(text, encoding="utf-8")
    print(f"Patched {path}")


def patch_app_js() -> None:
    path = _find("app.js")
    text = path.read_text(encoding="utf-8")
    text = _replace_once(
        text,
        '''        if (footnoteDialogContext.mode === 'create') {
            const footnote = await WorkbenchApi.createParagraphFootnote(footnoteDialogContext.paragraphId, { noteText });
            insertFootnoteMarker(footnoteDialogContext.element, footnoteDialogContext.offset, footnote.footnoteId);
        } else {
            await WorkbenchApi.updateParagraphFootnote(footnoteDialogContext.paragraphId, footnoteDialogContext.footnoteId, { noteText });
        }''',
        '''        if (footnoteDialogContext.mode === 'create') {
            const footnote = await WorkbenchApi.createParagraphFootnote(footnoteDialogContext.paragraphId, { noteText });
            insertFootnoteMarker(footnoteDialogContext.element, footnoteDialogContext.offset, footnote.footnoteId);
            const paragraphElement = getParagraphElementByIndex(footnoteDialogContext.chapterIndex, footnoteDialogContext.paragraphIndex);
            if (paragraphElement) {
                if (!Array.isArray(paragraphElement.footnotes)) {
                    paragraphElement.footnotes = [];
                }
                paragraphElement.footnotes.push({ footnoteId: footnote.footnoteId, noteText: footnote.noteText, number: null });
            }
        } else {
            await WorkbenchApi.updateParagraphFootnote(footnoteDialogContext.paragraphId, footnoteDialogContext.footnoteId, { noteText });
            const paragraphElement = getParagraphElementByIndex(footnoteDialogContext.chapterIndex, footnoteDialogContext.paragraphIndex);
            const existing = paragraphElement?.footnotes?.find((footnote) => footnote.footnoteId === footnoteDialogContext.footnoteId);
            if (existing) {
                existing.noteText = noteText;
            }
        }''',
        "app.js keep in-memory footnotes list in sync",
    )
    path.write_text(text, encoding="utf-8")
    print(f"Patched {path}")


if __name__ == "__main__":
    patch_styles_css()
    patch_app_js()
