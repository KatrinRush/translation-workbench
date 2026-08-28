from io import BytesIO
from zipfile import BadZipFile, ZipFile
import re
import xml.etree.ElementTree as ET


_WORD_PATTERN = re.compile(r"\b[\w'-]+\b", re.UNICODE)


def _local_name(tag):
    return tag.rsplit("}", 1)[-1]


def _property(root, name):
    for element in root.iter():
        if _local_name(element.tag) == name and element.text:
            return element.text.strip()
    return None


def parse_docx(filename, content):
    try:
        with ZipFile(BytesIO(content)) as archive:
            document = ET.fromstring(archive.read("word/document.xml"))
            try:
                properties = ET.fromstring(archive.read("docProps/core.xml"))
            except KeyError:
                properties = None
    except (BadZipFile, KeyError, ET.ParseError) as error:
        raise ValueError("Файл DOCX пошкоджений або має непідтримувану структуру.") from error

    text = " ".join(
        element.text.strip()
        for element in document.iter()
        if _local_name(element.tag) == "t" and element.text and element.text.strip()
    )
    return {
        "filename": filename,
        "title": _property(properties, "title") if properties is not None else None,
        "author": _property(properties, "creator") if properties is not None else None,
        "wordCount": len(_WORD_PATTERN.findall(text)),
    }
