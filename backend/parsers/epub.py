from io import BytesIO
from pathlib import PurePosixPath
from zipfile import BadZipFile, ZipFile
import re
import base64
import posixpath
from urllib.parse import unquote
import xml.etree.ElementTree as ET
import html.entities


_WORD_PATTERN = re.compile(r"\b[\w'-]+\b", re.UNICODE)

# The 5 entities XML itself defines. Everything else (nbsp, mdash, rsquo, hellip, ...)
# is only legal in HTML because it's declared in an external DTD that ET.fromstring
# never loads, so it must be resolved to a literal character before parsing or the
# whole document fails with "undefined entity" and gets silently dropped upstream.
_XML_BUILTIN_ENTITIES = {"amp", "lt", "gt", "apos", "quot"}
_NAMED_ENTITY_PATTERN = re.compile(r"&([a-zA-Z][a-zA-Z0-9]*);")


def _resolve_named_entity(match):
    name = match.group(1)
    if name in _XML_BUILTIN_ENTITIES:
        return match.group(0)
    char = html.entities.html5.get(name + ";")
    if char is None:
        return match.group(0)
    # Escape in case the resolved character is itself XML-special (rare, but e.g.
    # some legacy entities resolve to '<'/'>'/'&').
    if char in ("&", "<", ">"):
        return {"&": "&amp;", "<": "&lt;", ">": "&gt;"}[char]
    return char


def _normalize_html_entities(markup):
    """Replace HTML named entities (invalid bare XML) with literal characters."""
    return _NAMED_ENTITY_PATTERN.sub(_resolve_named_entity, markup)


_BLOCK_TAGS = {"p", "blockquote", "li"}
_CONTAINER_TAGS = {"div", "section", "article", "main", "figure", "body"}
_HEADING_TAGS = {"h1", "h2", "h3"}
# Some EPUBs (esp. Word/Calibre conversions) mark chapter starts with a styled
# <p class="Chapter"> instead of a real heading tag. Treated as an equal
# chapter-boundary signal alongside h1/h2/h3.
_CHAPTER_MARKER_CLASS = "Chapter"
_FORMATTING_TAGS = {
    "b": "b",
    "strong": "b",
    "i": "i",
    "em": "i",
    "s": "s",
    "strike": "s",
    "del": "s",
}


def _normalized_text(parts):
    return " ".join("".join(parts).split())


def _is_chapter_marker(element):
    classes = (element.attrib.get("class") or "").split()
    return _CHAPTER_MARKER_CLASS in classes


def _extract_ordered_content(markup, files, chapter_path):
    root = ET.fromstring(_normalize_html_entities(markup))
    body = next((element for element in root.iter() if _local_name(element.tag) == "body"), root)
    elements = []

    def append_paragraph(parts, raw_parts):
        value = _normalized_text(parts)
        if value:
            elements.append({
                "type": "paragraph",
                "text": value,
                "wordCount": _word_count(_normalized_text(raw_parts)),
            })

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

    def collect_formatted_inline(element, parts, raw_parts, formatting_tag):
        if not any(text.strip() for text in element.itertext()):
            collect_inline(element, parts, raw_parts)
            return

        parts.append(f"<{formatting_tag}>")
        collect_inline(element, parts, raw_parts)
        parts.append(f"</{formatting_tag}>")

    def collect_inline(element, parts, raw_parts):
        if element.text:
            parts.append(element.text)
            raw_parts.append(element.text)
        for child in element:
            tag = _local_name(child.tag)
            if tag == "img":
                append_paragraph(parts, raw_parts)
                parts.clear()
                raw_parts.clear()
                append_image(child)
            elif tag == "br":
                parts.append("\n")
                raw_parts.append("\n")
            elif tag in _HEADING_TAGS:
                # A heading nested in a text block remains metadata, never paragraph text.
                register_heading(child)
            elif tag in _BLOCK_TAGS or tag in _CONTAINER_TAGS:
                append_paragraph(parts, raw_parts)
                parts.clear()
                raw_parts.clear()
                walk(child)
            elif tag in _FORMATTING_TAGS:
                collect_formatted_inline(child, parts, raw_parts, _FORMATTING_TAGS[tag])
            else:
                collect_inline(child, parts, raw_parts)
            if child.tail:
                parts.append(child.tail)
                raw_parts.append(child.tail)

    def register_heading(element):
        # A heading (h1/h2/h3, or a <p class="Chapter">) is never body text —
        # it marks the start of a new chapter. Every one found becomes its own
        # break, not just the document's first (a single spine file can hold
        # more than one real chapter, e.g. back-matter listing several titles).
        value = _normalized_text(element.itertext())
        elements.append({"type": "chapter_break", "title": value or None})

    def walk(element):
        tag = _local_name(element.tag)
        if tag in _HEADING_TAGS:
            register_heading(element)
            return
        if tag == "img":
            append_image(element)
            return
        if tag in _BLOCK_TAGS:
            if _is_chapter_marker(element):
                register_heading(element)
                return
            parts = []
            raw_parts = []
            collect_inline(element, parts, raw_parts)
            append_paragraph(parts, raw_parts)
            return
        if tag in _CONTAINER_TAGS:
            parts = []
            raw_parts = []
            if element.text:
                parts.append(element.text)
                raw_parts.append(element.text)
            for child in element:
                child_tag = _local_name(child.tag)
                if child_tag in _HEADING_TAGS:
                    append_paragraph(parts, raw_parts)
                    parts.clear()
                    raw_parts.clear()
                    register_heading(child)
                elif child_tag == "img":
                    append_paragraph(parts, raw_parts)
                    parts.clear()
                    raw_parts.clear()
                    append_image(child)
                elif child_tag in _BLOCK_TAGS or child_tag in _CONTAINER_TAGS:
                    append_paragraph(parts, raw_parts)
                    parts.clear()
                    raw_parts.clear()
                    walk(child)
                elif child_tag in _FORMATTING_TAGS:
                    collect_formatted_inline(child, parts, raw_parts, _FORMATTING_TAGS[child_tag])
                else:
                    collect_inline(child, parts, raw_parts)
                if child.tail:
                    parts.append(child.tail)
                    raw_parts.append(child.tail)
            append_paragraph(parts, raw_parts)
            return

        parts = []
        raw_parts = []
        collect_inline(element, parts, raw_parts)
        append_paragraph(parts, raw_parts)

    walk(body)
    return elements


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

    # Pass 1: extract every spine document's ordered content up front, so we
    # can tell whether this book marks chapters at all (h1/h2/h3 or a
    # class="Chapter" paragraph) before deciding how to assemble chapters.
    documents = []
    for itemref in spine:
        href = items.get(itemref.attrib.get("idref"))
        if not href:
            continue
        path = str(base_path / unquote(href.split("#", 1)[0]))
        try:
            doc_elements = _extract_ordered_content(
                files[path].decode("utf-8", errors="replace"),
                files,
                path,
            )
        except (KeyError, ET.ParseError):
            continue
        documents.append(doc_elements)

    has_markers = any(
        element["type"] == "chapter_break"
        for doc_elements in documents
        for element in doc_elements
    )

    # Pass 2: assemble chapters.
    # - If the book marks chapters explicitly, a chapter is everything between
    #   two markers — this correctly merges a chapter split across several
    #   spine files, and correctly splits several chapters found in one file
    #   (e.g. back-matter listing multiple titled sections).
    # - If it never marks chapters at all, fall back to one chapter per spine
    #   file (e.g. EPUBs that are already split one-file-per-chapter with no
    #   heading markup) — matches the tool's previous behavior for that case.
    chapters = []
    current_title = None
    current_elements = []
    current_word_count = 0

    def flush_chapter():
        nonlocal current_title, current_elements, current_word_count
        if current_elements:
            chapters.append({
                "title": current_title,
                "wordCount": current_word_count,
                "elements": current_elements,
            })
        current_title = None
        current_elements = []
        current_word_count = 0

    for doc_elements in documents:
        if not has_markers:
            flush_chapter()
        for element in doc_elements:
            if element["type"] == "chapter_break":
                flush_chapter()
                current_title = element["title"]
            elif element["type"] == "paragraph":
                current_elements.append({"type": "paragraph", "text": element["text"]})
                current_word_count += element["wordCount"]
            else:
                current_elements.append(element)

    flush_chapter()

    return {
        "filename": filename,
        "title": _metadata_value(metadata, "title"),
        "author": _metadata_value(metadata, "creator"),
        "language": _metadata_value(metadata, "language"),
        "sections": len(chapters),
        "wordCount": sum(chapter["wordCount"] for chapter in chapters),
        "chapters": chapters,
        "coverImage": _extract_cover_image(package, metadata, files, base_path),
    }
