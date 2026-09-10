from io import BytesIO
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
        return output