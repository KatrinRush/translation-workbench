from io import BytesIO
from pathlib import PurePosixPath
from zipfile import BadZipFile, ZipFile
import re
import base64
import posixpath
from urllib.parse import unquote
import xml.etree.ElementTree as ET


_WORD_PATTERN = re.compile(r"\b[\w'-]+\b", re.UNICODE)


_BLOCK_TAGS = {"p", "blockquote", "li"}
_CONTAINER_TAGS = {"div", "section", "article", "main", "figure", "body"}
_HEADING_TAGS = {"h1", "h2", "h3"}


def _normalized_text(parts):
    return " ".join("".join(parts).split())


def _extract_ordered_content(markup, files, chapter_path):
    root = ET.fromstring(markup)
    body = next((element for element in root.iter() if _local_name(element.tag) == "body"), root)
    title = None
    elements = []

    def append_paragraph(parts):
        value = _normalized_text(parts)
        if value:
            elements.append({"type": "paragraph", "text": value})

    def append_image(element):
        source = element.attrib.get("src")
        image_path = _resolve_epub_path(PurePosixPath(chapter_path).parent, source)
        image_data = files.get(image_path) if image_path else None
        if image_data and _is_image(image_data):
            elements.append({
                "type": "image",
                "source": image_path,
                "imageData": base64.b64encode(image_data).decode("utf-8"),
            })

    def collect_inline(element, parts):
        if element.text:
            parts.append(element.text)
        for child in element:
            tag = _local_name(child.tag)
            if tag == "img":
                append_paragraph(parts)
                parts.clear()
                append_image(child)
            elif tag == "br":
                parts.append("\n")
            elif tag in _HEADING_TAGS:
                # A heading nested in a text block remains metadata, never paragraph text.
                register_heading(child)
            elif tag in _BLOCK_TAGS or tag in _CONTAINER_TAGS:
                append_paragraph(parts)
                parts.clear()
                walk(child)
            else:
                collect_inline(child, parts)
            if child.tail:
                parts.append(child.tail)

    def register_heading(element):
        nonlocal title
        if title is None:
            value = _normalized_text(element.itertext())
            if value:
                title = value

    def walk(element):
        tag = _local_name(element.tag)
        if tag in _HEADING_TAGS:
            register_heading(element)
            return
        if tag == "img":
            append_image(element)
            return
        if tag in _BLOCK_TAGS:
            parts = []
            collect_inline(element, parts)
            append_paragraph(parts)
            return
        if tag in _CONTAINER_TAGS:
            parts = []
            if element.text:
                parts.append(element.text)
            for child in element:
                child_tag = _local_name(child.tag)
                if child_tag in _HEADING_TAGS:
                    append_paragraph(parts)
                    parts.clear()
                    register_heading(child)
                elif child_tag == "img":
                    append_paragraph(parts)
                    parts.clear()
                    append_image(child)
                elif child_tag in _BLOCK_TAGS or child_tag in _CONTAINER_TAGS:
                    append_paragraph(parts)
                    parts.clear()
                    walk(child)
                else:
                    collect_inline(child, parts)
                if child.tail:
                    parts.append(child.tail)
            append_paragraph(parts)
            return

        parts = []
        collect_inline(element, parts)
        append_paragraph(parts)

    walk(body)
    return title, elements


def _word_count(text):
    return len(_WORD_PATTERN.findall(text))


def _local_name(tag):
    return tag.rsplit("}", 1)[-1]


def _metadata_value(metadata, name):
    for element in metadata:
        if _local_name(element.tag) == name and element.text:
            return element.text.strip()
    return None


def _resolve_epub_path(base_path, href):
    clean_href = unquote((href or "").split("#", 1)[0]).strip()
    if not clean_href:
        return None
    # Normalize relative references like ../images/cover.jpg against OPF base path.
    joined = PurePosixPath(base_path) / clean_href
    normalized = posixpath.normpath(str(joined))
    return normalized.lstrip("/")


def _find_cover_id_from_metadata(metadata):
    if metadata is None:
        return None
    for element in metadata:
        if _local_name(element.tag) != "meta":
            continue
        name = (element.attrib.get("name") or "").strip().lower()
        if name != "cover":
            continue
        content = (element.attrib.get("content") or "").strip()
        if content:
            return content
    return None


def _manifest_items(manifest):
    return [item for item in manifest if _local_name(item.tag) == "item"]


def _find_cover_item(manifest, metadata):
    items = _manifest_items(manifest)

    metadata_cover_id = _find_cover_id_from_metadata(metadata)
    if metadata_cover_id:
        for item in items:
            if item.attrib.get("id") == metadata_cover_id:
                return item

    for item in items:
        properties = (item.attrib.get("properties") or "").split()
        if "cover-image" in properties:
            return item

    for item in items:
        item_id = (item.attrib.get("id") or "").lower()
        if "cover" in item_id:
            return item

    for item in items:
        href = (item.attrib.get("href") or "").lower()
        if "cover" in href:
            return item

    return None


def _extract_cover_image(package, metadata, files, base_path):
    """Extract cover image from EPUB if available. Returns base64-encoded image or None."""
    try:
        manifest = next((element for element in package.iter() if _local_name(element.tag) == "manifest"), None)
        if manifest is None:
            return None

        cover_item = _find_cover_item(manifest, metadata)
        if cover_item is None:
            return None

        href = cover_item.attrib.get("href")
        cover_path = _resolve_epub_path(base_path, href)
        if not cover_path or cover_path not in files:
            return None

        image_data = files[cover_path]
        if _is_image(image_data):
            return base64.b64encode(image_data).decode("utf-8")
    except Exception:
        pass

    return None


def _is_image(data):
    """Check if data is a valid image format (JPEG, PNG, GIF, WebP)."""
    if len(data) < 4:
        return False
    
    # Check JPEG magic number
    if data[:2] == b'\xff\xd8':
        return True
    # Check PNG magic number
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return True
    # Check GIF magic number
    if data[:6] in (b'GIF87a', b'GIF89a'):
        return True
    # Check WebP magic number
    if data[:4] == b'RIFF' and len(data) >= 12 and data[8:12] == b'WEBP':
        return True
    
    return False


def parse_epub(filename, content):
    try:
        with ZipFile(BytesIO(content)) as archive:
            container = ET.fromstring(archive.read("META-INF/container.xml"))
            rootfile = next(
                element for element in container.iter()
                if _local_name(element.tag) == "rootfile"
            )
            package_path = rootfile.attrib["full-path"]
            package = ET.fromstring(archive.read(package_path))
            files = {name: archive.read(name) for name in archive.namelist()}
    except (BadZipFile, KeyError, ET.ParseError, StopIteration, AttributeError) as error:
        raise ValueError("Файл EPUB пошкоджений або має непідтримувану структуру.") from error

    metadata = next((element for element in package.iter() if _local_name(element.tag) == "metadata"), None)
    manifest = next((element for element in package.iter() if _local_name(element.tag) == "manifest"), None)
    spine = next((element for element in package.iter() if _local_name(element.tag) == "spine"), None)
    if metadata is None or manifest is None or spine is None:
        raise ValueError("У файлі EPUB відсутні необхідні дані книги.")

    items = {
        element.attrib.get("id"): element.attrib.get("href")
        for element in manifest
        if element.attrib.get("id") and element.attrib.get("href")
    }
    base_path = PurePosixPath(package_path).parent
    text = []
    chapters = []
    for index, itemref in enumerate(spine, 1):
        href = items.get(itemref.attrib.get("idref"))
        if not href:
            continue
        path = str(base_path / unquote(href.split("#", 1)[0]))
        try:
            title, elements = _extract_ordered_content(files[path].decode("utf-8", errors="replace"), files, path)
            paragraphs = [element["text"] for element in elements if element["type"] == "paragraph"]
            chapter_text = "\n\n".join(paragraphs)
            text.append(chapter_text)
            chapters.append({
                "title": title,
                "wordCount": _word_count(chapter_text),
                "elements": elements,
            })
        except (KeyError, ET.ParseError):
            continue

    return {
        "filename": filename,
        "title": _metadata_value(metadata, "title"),
        "author": _metadata_value(metadata, "creator"),
        "language": _metadata_value(metadata, "language"),
        "sections": len(chapters),
        "wordCount": _word_count(" ".join(text)),
        "chapters": chapters,
        "coverImage": _extract_cover_image(package, metadata, files, base_path),
    }
