"""Patch 22: footnotes, part 2 — editor UI (index.html/app.js/styles.css),
api.js, and DOCX export (export_service.py).

Depends on patch 21 (backend). See patch 21's docstring for the marker
mechanism (an invisible Private-Use-Area token, \\uE000<footnoteId>\\uE000,
embedded directly inside translation_text).

UX implemented here (per Katya's spec, revised from the first draft):
- No text-selection based creation (selection is used to copy into an AI
  chat). Instead: place the caret where the footnote belongs, click the
  pin button in the quick-actions-bar, type the note, save.
- Clicking an existing marker re-opens the same dialog, pre-filled, with
  a delete option.
- Numbering shown in the editor comes from get_book_structure's
  book-wide continuous numbering computed at last load; a brand-new
  footnote shows a "•" placeholder until the project is next opened/
  reloaded, when the real number appears. No forced refetch-after-save,
  to avoid disturbing in-progress edits/scroll position.
- DOCX export: translation_only gets real page-bottom Word footnotes
  (python-docx has no native footnote support, so this is done via raw
  OOXML — a hand-built word/footnotes.xml part related to the document).
  bilingual gets just the plain footnote number as superscript text,
  no linked footnote (per Katya's call — two-column table doesn't need it).
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent


_LIKELY_DIRS = [".", "frontend", "backend", "static", "public", "web", "app"]
_IGNORED_PARTS = {
    "node_modules", ".git", "__pycache__", ".mypy_cache", ".pytest_cache",
    ".cache", ".venv", "venv", "site-packages", "dist", "build",
    "playwright-report", "test-results",
}


def _find(filename: str) -> Path:
    """Locate `filename` in one of the likely project directories first
    (frontend files may live at the repo root or under frontend/ depending on
    the checkout); only falls back to a full repo-wide search, with vendor/
    cache directories excluded, if none of those have it."""
    for directory in _LIKELY_DIRS:
        candidate = REPO_ROOT / directory / filename
        if candidate.is_file():
            return candidate

    candidates = [
        path for path in REPO_ROOT.rglob(filename)
        if not any(part in _IGNORED_PARTS for part in path.parts)
    ]
    if not candidates:
        raise SystemExit(f"Could not find {filename} anywhere under {REPO_ROOT} — aborting.")
    if len(candidates) > 1:
        raise SystemExit(f"Found more than one {filename} under {REPO_ROOT}: {candidates} — aborting, resolve manually.")
    return candidates[0]


API_JS_PATH = _find("api.js")
APP_JS_PATH = _find("app.js")
STYLES_CSS_PATH = _find("styles.css")
INDEX_HTML_PATH = _find("index.html")
EXPORT_SERVICE_PATH = _find("export_service.py")


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"{label}: expected text not found — file may have changed, aborting.")
    if text.count(old) > 1:
        raise SystemExit(f"{label}: expected text is not unique — aborting to avoid a wrong edit.")
    return text.replace(old, new, 1)


# ---------------------------------------------------------------- api.js ---

def patch_api_js() -> None:
    text = API_JS_PATH.read_text(encoding="utf-8")
    text = _replace_once(
        text,
        '''    updateParagraph(paragraphId, data) {
        return this.request(`/api/paragraphs/${encodeURIComponent(paragraphId)}`, { method: 'PUT', body: JSON.stringify(data) });
    },
''',
        '''    updateParagraph(paragraphId, data) {
        return this.request(`/api/paragraphs/${encodeURIComponent(paragraphId)}`, { method: 'PUT', body: JSON.stringify(data) });
    },

    listParagraphFootnotes(paragraphId) {
        return this.request(`/api/paragraphs/${encodeURIComponent(paragraphId)}/footnotes`);
    },

    createParagraphFootnote(paragraphId, data) {
        return this.request(`/api/paragraphs/${encodeURIComponent(paragraphId)}/footnotes`, { method: 'POST', body: JSON.stringify(data) });
    },

    updateParagraphFootnote(paragraphId, footnoteId, data) {
        return this.request(`/api/paragraphs/${encodeURIComponent(paragraphId)}/footnotes/${encodeURIComponent(footnoteId)}`, { method: 'PUT', body: JSON.stringify(data) });
    },

    deleteParagraphFootnote(paragraphId, footnoteId) {
        return this.request(`/api/paragraphs/${encodeURIComponent(paragraphId)}/footnotes/${encodeURIComponent(footnoteId)}`, { method: 'DELETE' });
    },
''',
        "api.js footnote methods",
    )
    API_JS_PATH.write_text(text, encoding="utf-8")
    print(f"Patched {API_JS_PATH}")


# ------------------------------------------------------------ index.html ---

def patch_index_html() -> None:
    text = INDEX_HTML_PATH.read_text(encoding="utf-8")

    text = _replace_once(
        text,
        '''                        <button id="open-search" class="translation-action-icon" type="button" aria-label="Пошук" title="Пошук">🔍</button>
                        <button id="save-translation" class="translation-action-icon" type="button" aria-label="Зберегти" title="Зберегти">💾</button>''',
        '''                        <button id="open-search" class="translation-action-icon" type="button" aria-label="Пошук" title="Пошук">🔍</button>
                        <button id="add-footnote" class="translation-action-icon" type="button" aria-label="Додати зноску" title="Додати зноску (постав курсор у місце в перекладі)">📌</button>
                        <button id="save-translation" class="translation-action-icon" type="button" aria-label="Зберегти" title="Зберегти">💾</button>''',
        "index.html add-footnote button",
    )

    text = _replace_once(
        text,
        '''        <script src="/api.js?v=5" defer></script>
        <script src="/app.js?v=10" defer></script>
</body>
</html>''',
        '''        <div id="footnote-dialog" class="new-project-dialog" hidden>
                <div class="new-project-dialog-content" role="dialog" aria-modal="true" aria-labelledby="footnote-dialog-title">
                        <div class="dialog-header">
                                <div>
                                        <p class="project-label">Зноска</p>
                                        <h2 id="footnote-dialog-title">Текст зноски</h2>
                                </div>
                                <button id="close-footnote-dialog" class="icon-btn" type="button" aria-label="Закрити">×</button>
                        </div>
                        <textarea id="footnote-text-input" class="footnote-text-input" rows="4" placeholder="Текст зноски..."></textarea>
                        <div class="footnote-dialog-actions">
                                <button id="delete-footnote" class="text-btn danger-btn" type="button" hidden>Видалити</button>
                                <button id="save-footnote" class="primary-btn" type="button">Зберегти</button>
                        </div>
                </div>
        </div>

        <script src="/api.js?v=5" defer></script>
        <script src="/app.js?v=10" defer></script>
</body>
</html>''',
        "index.html footnote dialog markup",
    )

    INDEX_HTML_PATH.write_text(text, encoding="utf-8")
    print(f"Patched {INDEX_HTML_PATH}")


# ------------------------------------------------------------ styles.css ---

def patch_styles_css() -> None:
    text = STYLES_CSS_PATH.read_text(encoding="utf-8")
    text = _replace_once(
        text,
        '''.translation-history-actions {
    display: flex;
    gap: 8px;
}
''',
        '''.translation-history-actions {
    display: flex;
    gap: 8px;
}

.footnote-marker {
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
}

.footnote-text-input {
    width: 100%;
    resize: vertical;
    font: inherit;
    padding: 8px 10px;
    border-radius: 8px;
    border: 1px solid var(--color-border);
    background: var(--color-bg-surface);
    color: var(--color-text-primary);
}

.footnote-dialog-actions {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    margin-top: 12px;
}
''',
        "styles.css footnote styling",
    )
    STYLES_CSS_PATH.write_text(text, encoding="utf-8")
    print(f"Patched {STYLES_CSS_PATH}")


# ----------------------------------------------------------------- app.js --

def patch_app_js() -> None:
    text = APP_JS_PATH.read_text(encoding="utf-8")

    # 1. DOM references for the new button + dialog.
    text = _replace_once(
        text,
        '''const saveTranslationButton = document.querySelector('#save-translation');
const undoTranslationButton = document.querySelector('#undo-translation');
const redoTranslationButton = document.querySelector('#redo-translation');
''',
        '''const saveTranslationButton = document.querySelector('#save-translation');
const undoTranslationButton = document.querySelector('#undo-translation');
const redoTranslationButton = document.querySelector('#redo-translation');
const addFootnoteButton = document.querySelector('#add-footnote');
const footnoteDialog = document.querySelector('#footnote-dialog');
const closeFootnoteDialogButton = document.querySelector('#close-footnote-dialog');
const footnoteTextInput = document.querySelector('#footnote-text-input');
const saveFootnoteButton = document.querySelector('#save-footnote');
const deleteFootnoteButton = document.querySelector('#delete-footnote');
''',
        "app.js footnote DOM references",
    )

    # 2. Footnote token constant + renderFootnoteMarkers, next to the rich-text helpers.
    text = _replace_once(
        text,
        '''const RICH_TEXT_TAGS = new Set(['b', 'i', 's', 'strong', 'em', 'del', 'strike']);
const RICH_TEXT_TAG_ALIASES = { strong: 'b', em: 'i', del: 's', strike: 's' };
''',
        '''const RICH_TEXT_TAGS = new Set(['b', 'i', 's', 'strong', 'em', 'del', 'strike']);
const RICH_TEXT_TAG_ALIASES = { strong: 'b', em: 'i', del: 's', strike: 's' };

// Footnote position marker embedded directly inside translation_text, mirrors
// backend FOOTNOTE_TOKEN_RE (storage.py): \\uE000<footnoteId>\\uE000.
const FOOTNOTE_TOKEN_PATTERN = /\\uE000([0-9a-zA-Z_-]+)\\uE000/g;

function renderFootnoteMarkers(html, footnotes) {
    const numberById = new Map((footnotes || []).map((footnote) => [footnote.footnoteId, footnote.number]));
    return (html || '').replace(FOOTNOTE_TOKEN_PATTERN, (match, footnoteId) => {
        const number = numberById.has(footnoteId) ? numberById.get(footnoteId) : '•';
        return `<sup class="footnote-marker" contenteditable="false" data-footnote-id="${footnoteId}">${number}</sup>`;
    });
}

function getParagraphElementByIndex(chapterIndex, paragraphIndex) {
    const chapter = loadedChapters[chapterIndex];
    if (!chapter) {
        return null;
    }
    const paragraphElements = chapter.elements.filter((element) => element.type === 'paragraph');
    return paragraphElements[paragraphIndex] || null;
}

function getPlainTextOffset(root, node, offset) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let total = 0;
    let current;
    while ((current = walker.nextNode())) {
        if (current === node) {
            return total + offset;
        }
        total += current.nodeValue.length;
    }
    return total;
}
''',
        "app.js footnote marker helpers",
    )

    # 3. serializeRichText: turn a live <sup class="footnote-marker"> element back
    #    into the plain-text marker token when reading the draft out of the DOM.
    text = _replace_once(
        text,
        '''function serializeRichText(element) {
    function serialize(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            return node.nodeValue || '';
        }
        if (node.nodeType !== Node.ELEMENT_NODE) {
            return '';
        }
        if (node.tagName === 'BR') {
            return '\\n';
        }
        const content = Array.from(node.childNodes, serialize).join('');
        const tag = node.tagName.toLowerCase();
        if (!RICH_TEXT_TAGS.has(tag)) {
            return content;
        }
        const canonicalTag = RICH_TEXT_TAG_ALIASES[tag] || tag;
        return `<${canonicalTag}>${content}</${canonicalTag}>`;
    }

    return Array.from(element.childNodes, serialize).join('');
}''',
        '''function serializeRichText(element) {
    function serialize(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            return node.nodeValue || '';
        }
        if (node.nodeType !== Node.ELEMENT_NODE) {
            return '';
        }
        if (node.tagName === 'BR') {
            return '\\n';
        }
        if (node.classList && node.classList.contains('footnote-marker')) {
            return `\\uE000${node.dataset.footnoteId}\\uE000`;
        }
        const content = Array.from(node.childNodes, serialize).join('');
        const tag = node.tagName.toLowerCase();
        if (!RICH_TEXT_TAGS.has(tag)) {
            return content;
        }
        const canonicalTag = RICH_TEXT_TAG_ALIASES[tag] || tag;
        return `<${canonicalTag}>${content}</${canonicalTag}>`;
    }

    return Array.from(element.childNodes, serialize).join('');
}''',
        "serializeRichText footnote marker handling",
    )

    # 4. normalizeBookStructure currently drops any field it doesn't explicitly
    #    whitelist — it was silently discarding "footnotes" from the backend.
    text = _replace_once(
        text,
        '''                if (typeof rawParagraph !== 'string') {
                    return {
                        type: 'paragraph',
                        paragraphId: rawParagraph.paragraphId || null,
                        originalText: rawParagraph.originalText || '',
                        translationText: rawParagraph.translationText || null,
                        reviewed: Boolean(rawParagraph.reviewed),
                        isService: Boolean(rawParagraph.isService),
                    };
                }
                return {
                    type: 'paragraph',
                    paragraphId: null,
                    originalText: rawParagraph,
                    translationText: null,
                    reviewed: false,
                    isService: false,
                };''',
        '''                if (typeof rawParagraph !== 'string') {
                    return {
                        type: 'paragraph',
                        paragraphId: rawParagraph.paragraphId || null,
                        originalText: rawParagraph.originalText || '',
                        translationText: rawParagraph.translationText || null,
                        reviewed: Boolean(rawParagraph.reviewed),
                        isService: Boolean(rawParagraph.isService),
                        footnotes: Array.isArray(rawParagraph.footnotes) ? rawParagraph.footnotes : [],
                    };
                }
                return {
                    type: 'paragraph',
                    paragraphId: null,
                    originalText: rawParagraph,
                    translationText: null,
                    reviewed: false,
                    isService: false,
                    footnotes: [],
                };''',
        "normalizeBookStructure footnotes passthrough",
    )

    # 5. Initial paragraph render: wrap with renderFootnoteMarkers.
    text = _replace_once(
        text,
        '''        translation.innerHTML = sanitizeRichText(draft.translationText);
        translation.dataset.placeholder = 'Введіть переклад абзацу...';''',
        '''        translation.innerHTML = renderFootnoteMarkers(sanitizeRichText(draft.translationText), paragraph.footnotes);
        translation.dataset.placeholder = 'Введіть переклад абзацу...';''',
        "initial paragraph render with footnote markers",
    )

    # 6. Post-DeepL-translate render: same wrapping (old footnotes, if any, no
    #    longer match the freshly translated text and simply won't be found).
    text = _replace_once(
        text,
        '''                translation.innerHTML = sanitizeRichText(translated.translationText || '');
                scheduleParagraphHeightsSync();''',
        '''                translation.innerHTML = renderFootnoteMarkers(sanitizeRichText(translated.translationText || ''), paragraph.footnotes);
                scheduleParagraphHeightsSync();''',
        "post-translate render with footnote markers",
    )

    # 7. Undo/redo restore render.
    text = _replace_once(
        text,
        '''function renderTranslationFields(values) {
    translationRows.querySelectorAll('.translation-row').forEach((row, index) => {
        const translation = row.querySelector('.translation-paragraph');
        translation.innerHTML = sanitizeRichText(values[index].translationText);
        row.querySelector('.paragraph-review input').checked = values[index].reviewed;
        updateParagraphVisualState(row, values[index]);
    });''',
        '''function renderTranslationFields(values) {
    translationRows.querySelectorAll('.translation-row').forEach((row, index) => {
        const translation = row.querySelector('.translation-paragraph');
        const chapterIndex = Number(row.dataset.chapterIndex);
        const paragraphElement = getParagraphElementByIndex(chapterIndex, index);
        translation.innerHTML = renderFootnoteMarkers(sanitizeRichText(values[index].translationText), paragraphElement?.footnotes);
        row.querySelector('.paragraph-review input').checked = values[index].reviewed;
        updateParagraphVisualState(row, values[index]);
    });''',
        "undo/redo restore render with footnote markers",
    )

    # 8. Wire up the caret tracker, the toolbar button, the dialog, and the
    #    click-to-edit handler on existing markers.
    text = _replace_once(
        text,
        '''saveTranslationButton.addEventListener('click', saveCurrentTranslation);
undoTranslationButton.addEventListener('click', undoTranslation);
redoTranslationButton.addEventListener('click', redoTranslation);
''',
        '''saveTranslationButton.addEventListener('click', saveCurrentTranslation);
undoTranslationButton.addEventListener('click', undoTranslation);
redoTranslationButton.addEventListener('click', redoTranslation);

let lastTranslationCaret = null;
let footnoteDialogContext = null;

document.addEventListener('selectionchange', () => {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) {
        return;
    }
    const range = selection.getRangeAt(0);
    const container = range.startContainer.nodeType === Node.TEXT_NODE
        ? range.startContainer.parentElement
        : range.startContainer;
    const translationElement = container && container.closest ? container.closest('.translation-paragraph') : null;
    if (!translationElement) {
        return;
    }
    lastTranslationCaret = {
        element: translationElement,
        paragraphId: translationElement.dataset.paragraphId,
        chapterIndex: Number(translationElement.dataset.chapterIndex),
        paragraphIndex: Number(translationElement.dataset.paragraphIndex),
        offset: getPlainTextOffset(translationElement, range.startContainer, range.startOffset),
    };
});

addFootnoteButton.addEventListener('click', () => {
    if (!lastTranslationCaret || !lastTranslationCaret.paragraphId) {
        window.alert('Постав курсор у місце в перекладі, де потрібна зноска.');
        return;
    }
    footnoteDialogContext = { mode: 'create', ...lastTranslationCaret };
    footnoteTextInput.value = '';
    deleteFootnoteButton.hidden = true;
    footnoteDialog.hidden = false;
    footnoteTextInput.focus();
});

translationRows.addEventListener('click', (event) => {
    const marker = event.target.closest('.footnote-marker');
    if (!marker) {
        return;
    }
    event.preventDefault();
    const translationElement = marker.closest('.translation-paragraph');
    if (!translationElement) {
        return;
    }
    const chapterIndex = Number(translationElement.dataset.chapterIndex);
    const paragraphIndex = Number(translationElement.dataset.paragraphIndex);
    const footnoteId = marker.dataset.footnoteId;
    const paragraphElement = getParagraphElementByIndex(chapterIndex, paragraphIndex);
    const existing = (paragraphElement?.footnotes || []).find((footnote) => footnote.footnoteId === footnoteId);
    footnoteDialogContext = {
        mode: 'edit',
        footnoteId,
        paragraphId: translationElement.dataset.paragraphId,
        chapterIndex,
        paragraphIndex,
        markerElement: marker,
    };
    footnoteTextInput.value = existing?.noteText || '';
    deleteFootnoteButton.hidden = false;
    footnoteDialog.hidden = false;
    footnoteTextInput.focus();
});

closeFootnoteDialogButton.addEventListener('click', closeFootnoteDialog);

function closeFootnoteDialog() {
    footnoteDialog.hidden = true;
    footnoteDialogContext = null;
}

function insertFootnoteMarker(translationElement, offset, footnoteId) {
    selectEditableText(translationElement, offset, offset);
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) {
        return;
    }
    const range = selection.getRangeAt(0);
    const marker = document.createElement('sup');
    marker.className = 'footnote-marker';
    marker.contentEditable = 'false';
    marker.dataset.footnoteId = footnoteId;
    marker.textContent = '•';
    range.insertNode(marker);
    range.setStartAfter(marker);
    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);
    const row = translationElement.closest('.translation-row');
    const original = row ? row.querySelector('.original-paragraph') : null;
    if (original) {
        syncParagraphPairHeight(original, translationElement);
    }
}

saveFootnoteButton.addEventListener('click', async () => {
    if (!footnoteDialogContext) {
        return;
    }
    const noteText = footnoteTextInput.value.trim();
    if (!noteText) {
        window.alert('Введіть текст зноски.');
        return;
    }
    saveFootnoteButton.disabled = true;
    try {
        if (footnoteDialogContext.mode === 'create') {
            const footnote = await WorkbenchApi.createParagraphFootnote(footnoteDialogContext.paragraphId, { noteText });
            insertFootnoteMarker(footnoteDialogContext.element, footnoteDialogContext.offset, footnote.footnoteId);
        } else {
            await WorkbenchApi.updateParagraphFootnote(footnoteDialogContext.paragraphId, footnoteDialogContext.footnoteId, { noteText });
        }
        const state = translationStates.get(footnoteDialogContext.chapterIndex);
        if (state) {
            updateDraftFromControls(state);
        }
        closeFootnoteDialog();
    } catch (error) {
        window.alert(error.message);
    } finally {
        saveFootnoteButton.disabled = false;
    }
});

deleteFootnoteButton.addEventListener('click', async () => {
    if (!footnoteDialogContext || footnoteDialogContext.mode !== 'edit') {
        return;
    }
    if (!window.confirm('Видалити зноску?')) {
        return;
    }
    deleteFootnoteButton.disabled = true;
    try {
        await WorkbenchApi.deleteParagraphFootnote(footnoteDialogContext.paragraphId, footnoteDialogContext.footnoteId);
        footnoteDialogContext.markerElement?.remove();
        const state = translationStates.get(footnoteDialogContext.chapterIndex);
        if (state) {
            updateDraftFromControls(state);
        }
        closeFootnoteDialog();
    } catch (error) {
        window.alert(error.message);
    } finally {
        deleteFootnoteButton.disabled = false;
    }
});
''',
        "app.js footnote UI wiring",
    )

    # 9. Close the footnote dialog on Escape too, next to the search-dialog's own handler.
    text = _replace_once(
        text,
        '''document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !searchDialog.hidden) {
        closeSearchPanel();
    }
});''',
        '''document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !searchDialog.hidden) {
        closeSearchPanel();
    }
    if (event.key === 'Escape' && !footnoteDialog.hidden) {
        closeFootnoteDialog();
    }
});''',
        "Escape key closes footnote dialog",
    )

    APP_JS_PATH.write_text(text, encoding="utf-8")
    print(f"Patched {APP_JS_PATH}")


# ------------------------------------------------------- export_service.py --

def patch_export_service() -> None:
    expected_original = '''from io import BytesIO
import re

from docx import Document
from docx.shared import Inches
from PIL import Image

try:
    from .storage import Storage
except ImportError:
    from storage import Storage


IMAGE_EXPORT_WIDTH_INCHES = 2.5
INLINE_TAG_PATTERN = re.compile(r"<(/?)(b|i|s)>")


class ExportService:
    def __init__(self, storage: Storage):
        self.storage = storage

    def _get_image_as_png(self, image_id: str) -> BytesIO | None:
        image = self.storage.get_inline_image(image_id)
        if image is None:
            return None
        source = Image.open(BytesIO(image["data"]))
        output = BytesIO()
        source.convert("RGB").save(output, format="PNG")
        output.seek(0)
        return output

    @staticmethod
    def _append_formatted_text(paragraph, text: str) -> None:
        active_tags: list[str] = []

        def append_run(value: str) -> None:
            if not value:
                return
            run = paragraph.add_run(value)
            run.bold = "b" in active_tags
            run.italic = "i" in active_tags
            run.font.strike = "s" in active_tags

        position = 0
        for match in INLINE_TAG_PATTERN.finditer(text):
            append_run(text[position:match.start()])
            position = match.end()
            closing, tag = match.group(1), match.group(2)
            if closing:
                if active_tags and active_tags[-1] == tag:
                    active_tags.pop()
            else:
                active_tags.append(tag)
        append_run(text[position:])

    @classmethod
    def _set_formatted_paragraph(cls, paragraph, text: str) -> None:
        paragraph.clear()
        cls._append_formatted_text(paragraph, text)

    def generate_docx(self, project_id: str, format: str) -> BytesIO:
        if format not in {"bilingual", "translation_only"}:
            raise ValueError("Unsupported DOCX export format.")

        structure = self.storage.get_book_structure(project_id)
        if structure is None:
            raise ValueError("Book structure not found.")

        document = Document()
        image_counter = 0
        pending_images: list[tuple[int, str]] = []

        for chapter in structure["chapters"]:
            if chapter["excludeFromExport"]:
                continue

            title = chapter.get("translationTitle") or chapter.get("title") or ""
            document.add_heading(title, level=1)

            if format == "bilingual":
                table = document.add_table(rows=1, cols=2)
                table.rows[0].cells[0].text = "Оригінал"
                table.rows[0].cells[1].text = "Переклад"
                for element in chapter["elements"]:
                    if element["type"] == "paragraph":
                        cells = table.add_row().cells
                        self._set_formatted_paragraph(cells[0].paragraphs[0], element.get("originalText") or "")
                        self._set_formatted_paragraph(cells[1].paragraphs[0], element.get("translationText") or "")
                    elif element["type"] == "image":
                        image_counter += 1
                        pending_images.append((image_counter, element["imageId"]))
                        marker = f"[Зображення {image_counter}]"
                        cells = table.add_row().cells
                        cells[0].text = marker
                        cells[1].text = marker
            else:
                for element in chapter["elements"]:
                    if element["type"] == "paragraph":
                        paragraph = document.add_paragraph()
                        self._append_formatted_text(paragraph, element.get("translationText") or "")
                    elif element["type"] == "image":
                        png_image = self._get_image_as_png(element["imageId"])
                        if png_image is not None:
                            document.add_picture(png_image, width=Inches(IMAGE_EXPORT_WIDTH_INCHES))

        if format == "bilingual" and pending_images:
            document.add_heading("Зображення", level=1)
            for image_counter, image_id in pending_images:
                document.add_paragraph(f"Зображення {image_counter} ⬇️")
                png_image = self._get_image_as_png(image_id)
                if png_image is not None:
                    document.add_picture(png_image, width=Inches(IMAGE_EXPORT_WIDTH_INCHES))

        output = BytesIO()
        document.save(output)
        output.seek(0)
        return output'''

    new_content = '''from io import BytesIO
from xml.sax.saxutils import escape as xml_escape
import re

from docx import Document
from docx.opc.packuri import PackURI
from docx.opc.part import Part
from docx.oxml import parse_xml
from docx.shared import Inches
from PIL import Image

try:
    from .storage import Storage
except ImportError:
    from storage import Storage


IMAGE_EXPORT_WIDTH_INCHES = 2.5
INLINE_TAG_PATTERN = re.compile(r"<(/?)(b|i|s)>|\\uE000([0-9a-zA-Z_-]+)\\uE000")

# python-docx has no native footnote support (no add_footnote, no Footnotes
# part) — footnotes here are built by hand as raw OOXML and related into the
# package. word/footnotes.xml holds the note bodies; each reference in the
# body text is a <w:footnoteReference> run pointing at one by w:id. Word
# numbers footnotes itself, continuously, based on the order the references
# appear in the document — we don't need to (and can't reliably) tell it
# what number to show.
FOOTNOTES_RELATIONSHIP_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes"
FOOTNOTES_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"
WORD_NAMESPACE = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


class ExportService:
    def __init__(self, storage: Storage):
        self.storage = storage

    def _get_image_as_png(self, image_id: str) -> BytesIO | None:
        image = self.storage.get_inline_image(image_id)
        if image is None:
            return None
        source = Image.open(BytesIO(image["data"]))
        output = BytesIO()
        source.convert("RGB").save(output, format="PNG")
        output.seek(0)
        return output

    @staticmethod
    def _append_formatted_text(paragraph, text: str, footnote_notes_by_id: dict | None = None, on_footnote=None) -> None:
        """Append `text` to `paragraph` as formatted runs, honouring the b/i/s
        inline tags and, when a footnote marker is found, calling
        `on_footnote(paragraph, footnote_id, note_text)` at that point instead
        of emitting literal text. `on_footnote=None` silently drops markers
        (used nowhere currently, kept as a safe default)."""
        active_tags: list[str] = []

        def append_run(value: str) -> None:
            if not value:
                return
            run = paragraph.add_run(value)
            run.bold = "b" in active_tags
            run.italic = "i" in active_tags
            run.font.strike = "s" in active_tags

        position = 0
        for match in INLINE_TAG_PATTERN.finditer(text):
            append_run(text[position:match.start()])
            position = match.end()
            closing, tag, footnote_id = match.group(1), match.group(2), match.group(3)
            if footnote_id is not None:
                note_text = (footnote_notes_by_id or {}).get(footnote_id)
                if note_text is not None and on_footnote is not None:
                    on_footnote(paragraph, footnote_id, note_text)
                continue
            if closing:
                if active_tags and active_tags[-1] == tag:
                    active_tags.pop()
            else:
                active_tags.append(tag)
        append_run(text[position:])

    @classmethod
    def _set_formatted_paragraph(cls, paragraph, text: str, footnote_notes_by_id: dict | None = None, on_footnote=None) -> None:
        paragraph.clear()
        cls._append_formatted_text(paragraph, text, footnote_notes_by_id, on_footnote)

    @staticmethod
    def _append_bilingual_footnote_number(paragraph, footnote_id: str, numbers_by_id: dict) -> None:
        # Bilingual export doesn't carry real footnotes (no room for them in a
        # two-column table) — just leave the plain number, superscript.
        run = paragraph.add_run(str(numbers_by_id.get(footnote_id, "?")))
        run.font.superscript = True

    def _append_real_footnote(self, paragraph, note_text: str, footnote_definitions: list) -> None:
        word_footnote_id = len(footnote_definitions) + 1
        footnote_definitions.append((word_footnote_id, note_text))
        reference_xml = (
            f'<w:r xmlns:w="{WORD_NAMESPACE}">'
            '<w:rPr><w:vertAlign w:val="superscript"/></w:rPr>'
            f'<w:footnoteReference w:id="{word_footnote_id}"/></w:r>'
        )
        paragraph._p.append(parse_xml(reference_xml))

    @staticmethod
    def _attach_footnotes_part(document, footnote_definitions: list) -> None:
        if not footnote_definitions:
            return
        body = [
            '<w:footnote w:type="separator" w:id="-1"><w:p><w:r><w:separator/></w:r></w:p></w:footnote>',
            '<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:r><w:continuationSeparator/></w:r></w:p></w:footnote>',
        ]
        for word_footnote_id, note_text in footnote_definitions:
            body.append(
                f'<w:footnote w:id="{word_footnote_id}"><w:p>'
                '<w:r><w:rPr><w:vertAlign w:val="superscript"/></w:rPr><w:footnoteRef/></w:r>'
                f'<w:r><w:t xml:space="preserve"> {xml_escape(note_text)}</w:t></w:r>'
                '</w:p></w:footnote>'
            )
        footnotes_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:footnotes xmlns:w="{WORD_NAMESPACE}">' + "".join(body) + '</w:footnotes>'
        ).encode("utf-8")
        part = Part(PackURI("/word/footnotes.xml"), FOOTNOTES_CONTENT_TYPE, footnotes_xml, document.part.package)
        document.part.relate_to(part, FOOTNOTES_RELATIONSHIP_TYPE)

    def generate_docx(self, project_id: str, format: str) -> BytesIO:
        if format not in {"bilingual", "translation_only"}:
            raise ValueError("Unsupported DOCX export format.")

        structure = self.storage.get_book_structure(project_id)
        if structure is None:
            raise ValueError("Book structure not found.")

        document = Document()
        image_counter = 0
        pending_images: list[tuple[int, str]] = []
        footnote_definitions: list[tuple[int, str]] = []

        for chapter in structure["chapters"]:
            if chapter["excludeFromExport"]:
                continue

            title = chapter.get("translationTitle") or chapter.get("title") or ""
            document.add_heading(title, level=1)

            if format == "bilingual":
                table = document.add_table(rows=1, cols=2)
                table.rows[0].cells[0].text = "Оригінал"
                table.rows[0].cells[1].text = "Переклад"
                for element in chapter["elements"]:
                    if element["type"] == "paragraph":
                        cells = table.add_row().cells
                        self._set_formatted_paragraph(cells[0].paragraphs[0], element.get("originalText") or "")
                        footnotes = element.get("footnotes") or []
                        notes_by_id = {footnote["footnoteId"]: footnote["noteText"] for footnote in footnotes}
                        numbers_by_id = {footnote["footnoteId"]: footnote["number"] for footnote in footnotes}
                        self._set_formatted_paragraph(
                            cells[1].paragraphs[0],
                            element.get("translationText") or "",
                            notes_by_id,
                            lambda p, fid, note, numbers=numbers_by_id: self._append_bilingual_footnote_number(p, fid, numbers),
                        )
                    elif element["type"] == "image":
                        image_counter += 1
                        pending_images.append((image_counter, element["imageId"]))
                        marker = f"[Зображення {image_counter}]"
                        cells = table.add_row().cells
                        cells[0].text = marker
                        cells[1].text = marker
            else:
                for element in chapter["elements"]:
                    if element["type"] == "paragraph":
                        paragraph = document.add_paragraph()
                        footnotes = element.get("footnotes") or []
                        notes_by_id = {footnote["footnoteId"]: footnote["noteText"] for footnote in footnotes}
                        self._append_formatted_text(
                            paragraph,
                            element.get("translationText") or "",
                            notes_by_id,
                            lambda p, fid, note: self._append_real_footnote(p, note, footnote_definitions),
                        )
                    elif element["type"] == "image":
                        png_image = self._get_image_as_png(element["imageId"])
                        if png_image is not None:
                            document.add_picture(png_image, width=Inches(IMAGE_EXPORT_WIDTH_INCHES))

        if format == "bilingual" and pending_images:
            document.add_heading("Зображення", level=1)
            for image_counter, image_id in pending_images:
                document.add_paragraph(f"Зображення {image_counter} ⬇️")
                png_image = self._get_image_as_png(image_id)
                if png_image is not None:
                    document.add_picture(png_image, width=Inches(IMAGE_EXPORT_WIDTH_INCHES))

        if format == "translation_only":
            self._attach_footnotes_part(document, footnote_definitions)

        output = BytesIO()
        document.save(output)
        output.seek(0)
        return output'''

    text = EXPORT_SERVICE_PATH.read_text(encoding="utf-8")
    if text.strip() != expected_original.strip():
        raise SystemExit("export_service.py: file doesn't match the expected original — aborting to avoid a wrong overwrite.")
    EXPORT_SERVICE_PATH.write_text(new_content + "\n", encoding="utf-8")
    print(f"Patched {EXPORT_SERVICE_PATH}")


if __name__ == "__main__":
    patch_api_js()
    patch_index_html()
    patch_styles_css()
    patch_app_js()
    patch_export_service()
