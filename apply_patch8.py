."""
Apply patch 8: preserve <b>/<i>/<s> inline formatting through DeepL translation.

What it does:
- _build_chunk_xml now turns literal "<b>/<i>/<s>" markers in originalText into
  real nested XML sub-elements before sending to DeepL, so tag_handling="xml"
  can actually carry the formatting through the translation instead of DeepL
  seeing them as plain escaped text.
- _parse_chunk_xml_result now reconstructs the same canonical "<b>...</b>" text
  form from the translated response, instead of flattening/losing the tags
  with a plain itertext() join.

Run from the repo root:
    python3 apply_patch8.py

Then verify:
    node --check ...   (not needed here, this touches backend/*.py only)
    pytest
"""

import re
import sys
from pathlib import Path

TARGET = Path("backend/translations/service.py")


def main():
    if not TARGET.exists():
        print(f"ERROR: {TARGET} not found. Run this from the repo root, "
              f"or edit the TARGET path at the top of this script.")
        sys.exit(1)

    content = TARGET.read_text(encoding="utf-8")

    old_import = "import hashlib\nimport json\nimport logging\nimport xml.etree.ElementTree as ET"
    new_import = "import hashlib\nimport json\nimport logging\nimport re\nimport xml.etree.ElementTree as ET"
    if old_import not in content:
        print("ERROR: import block not found — file content differs from what this patch expects.")
        sys.exit(1)
    content = content.replace(old_import, new_import, 1)

    old_methods = '''    @staticmethod
    def _build_chunk_xml(paragraphs: list[dict[str, str]]) -> str:
        root = ET.Element("chunk")
        for paragraph in paragraphs:
            element = ET.SubElement(root, "p", {"id": paragraph["paragraphId"]})
            element.text = paragraph["originalText"]
        return ET.tostring(root, encoding="unicode")

    @staticmethod
    def _parse_chunk_xml_result(text: str, expected_paragraph_ids: list[str]) -> dict[str, str]:
        try:
            root = ET.fromstring(text)
        except ET.ParseError as error:
            raise TranslationServiceError("Provider response did not preserve chunk XML.", 502, "chunk_mapping_failed") from error

        translated: dict[str, str] = {}
        actual_paragraph_ids = []
        for element in root.findall(".//p"):
            paragraph_id = element.attrib.get("id")
            if paragraph_id is None:
                continue
            actual_paragraph_ids.append(paragraph_id)
            translated[paragraph_id] = "".join(element.itertext())

        if actual_paragraph_ids != expected_paragraph_ids:
            raise TranslationServiceError("Provider response paragraph IDs did not match chunk source IDs.", 502, "chunk_mapping_failed")
        return translated'''

    new_methods = '''    # Canonical inline formatting markers produced by the EPUB parser
    # (backend/parsers/epub.py's _FORMATTING_TAGS): bold/italic/strikethrough
    # spans are stored in originalText as literal "<b>...</b>" etc. text.
    _INLINE_TAGS = {"b", "i", "s"}
    _INLINE_TAG_PATTERN = re.compile(r"<(/?)(b|i|s)>")

    @classmethod
    def _append_inline_markup(cls, parent: ET.Element, text: str) -> None:
        """Turn literal <b>/<i>/<s> markers in `text` into real nested
        sub-elements of `parent`, so DeepL's tag_handling=xml can carry the
        formatting through the translation instead of seeing it as plain text."""
        stack = [parent]

        def append_chunk(chunk: str) -> None:
            if not chunk:
                return
            current = stack[-1]
            if len(current) == 0:
                current.text = (current.text or "") + chunk
            else:
                last_child = current[-1]
                last_child.tail = (last_child.tail or "") + chunk

        pos = 0
        for match in cls._INLINE_TAG_PATTERN.finditer(text):
            append_chunk(text[pos:match.start()])
            pos = match.end()
            closing, tag = match.group(1), match.group(2)
            if closing:
                # Only pop a matching open tag; ignore stray/unbalanced closers
                # defensively rather than raising on malformed source markup.
                if len(stack) > 1 and stack[-1].tag == tag:
                    stack.pop()
            else:
                stack.append(ET.SubElement(stack[-1], tag))
        append_chunk(text[pos:])

    @staticmethod
    def _serialize_inline_markup(element: ET.Element) -> str:
        """Inverse of _append_inline_markup: walk a translated <p> element back
        into the same literal "<b>...</b>" text form used everywhere else
        (storage, export), instead of flattening/losing the tags."""
        parts: list[str] = []
        if element.text:
            parts.append(element.text)
        for child in element:
            tag = child.tag
            parts.append(f"<{tag}>")
            parts.append(TranslationService._serialize_inline_markup(child))
            parts.append(f"</{tag}>")
            if child.tail:
                parts.append(child.tail)
        return "".join(parts)

    @classmethod
    def _build_chunk_xml(cls, paragraphs: list[dict[str, str]]) -> str:
        root = ET.Element("chunk")
        for paragraph in paragraphs:
            element = ET.SubElement(root, "p", {"id": paragraph["paragraphId"]})
            cls._append_inline_markup(element, paragraph["originalText"])
        return ET.tostring(root, encoding="unicode")

    @staticmethod
    def _parse_chunk_xml_result(text: str, expected_paragraph_ids: list[str]) -> dict[str, str]:
        try:
            root = ET.fromstring(text)
        except ET.ParseError as error:
            raise TranslationServiceError("Provider response did not preserve chunk XML.", 502, "chunk_mapping_failed") from error

        translated: dict[str, str] = {}
        actual_paragraph_ids = []
        for element in root.findall(".//p"):
            paragraph_id = element.attrib.get("id")
            if paragraph_id is None:
                continue
            actual_paragraph_ids.append(paragraph_id)
            translated[paragraph_id] = TranslationService._serialize_inline_markup(element)

        if actual_paragraph_ids != expected_paragraph_ids:
            raise TranslationServiceError("Provider response paragraph IDs did not match chunk source IDs.", 502, "chunk_mapping_failed")
        return translated'''

    if old_methods not in content:
        print("ERROR: target methods not found — file content differs from what this patch expects.")
        sys.exit(1)
    content = content.replace(old_methods, new_methods, 1)

    TARGET.write_text(content, encoding="utf-8")
    print(f"Patched successfully: {TARGET}")


if __name__ == "__main__":
    main()
