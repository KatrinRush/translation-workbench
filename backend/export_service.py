from io import BytesIO
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
INLINE_TAG_PATTERN = re.compile(r"<(/?)(b|i|s)>|\uE000([0-9a-zA-Z_-]+)\uE000")

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
        return output
