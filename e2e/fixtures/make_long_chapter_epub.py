"""Build test-data/long-chapter.epub: one long chapter (80 paragraphs, the word
"lighthouse" only in paragraph 60) followed by eleven short chapters, so the chapter
strip overflows and the page scrolls far. Run: python e2e/fixtures/make_long_chapter_epub.py
"""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

OUTPUT = Path(__file__).resolve().parents[2] / "test-data" / "long-chapter.epub"
CHAPTER_COUNT = 12


def chapter_html(index: int) -> str:
    if index == 1:
        paragraphs = [
            f"Paragraph {number} of the long chapter keeps the reader walking along the grey shore, "
            f"{'past the old lighthouse that nobody has lit for years, ' if number == 60 else ''}"
            "counting waves and listening to the gulls argue over the morning catch."
            for number in range(1, 81)
        ]
    else:
        paragraphs = [f"Chapter {index} is short: a single paragraph to fill the chapter strip."]
    body = "\n".join(f"    <p>{text}</p>" for text in paragraphs)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE html>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml">\n'
        f"<head><title>Chapter {index}</title></head>\n<body>\n    <h1>Chapter {index}</h1>\n{body}\n</body>\n</html>"
    )


def main() -> None:
    manifest = "\n".join(
        f'        <item id="c{i}" href="chapter{i}.html" media-type="application/xhtml+xml"/>' for i in range(1, CHAPTER_COUNT + 1)
    )
    spine = "\n".join(f'        <itemref idref="c{i}"/>' for i in range(1, CHAPTER_COUNT + 1))
    nav = "\n".join(
        f'        <navPoint id="n{i}" playOrder="{i}"><navLabel><text>Chapter {i}</text></navLabel>'
        f'<content src="chapter{i}.html"/></navPoint>'
        for i in range(1, CHAPTER_COUNT + 1)
    )
    with ZipFile(OUTPUT, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip", compress_type=ZIP_STORED)
        archive.writestr("META-INF/container.xml", (
            '<?xml version="1.0"?>\n<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
            '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>'
        ), compress_type=ZIP_DEFLATED)
        archive.writestr("OEBPS/content.opf", (
            '<?xml version="1.0" encoding="UTF-8"?>\n<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="id">\n'
            '    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Long Chapter Book</dc:title>'
            '<dc:creator>Test Author</dc:creator><dc:language>en</dc:language></metadata>\n'
            f'    <manifest>\n        <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>\n{manifest}\n    </manifest>\n'
            f'    <spine toc="ncx">\n{spine}\n    </spine>\n</package>'
        ), compress_type=ZIP_DEFLATED)
        archive.writestr("OEBPS/toc.ncx", (
            '<?xml version="1.0" encoding="UTF-8"?>\n<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">'
            '<head><meta name="dtb:uid" content="long"/></head><docTitle><text>Long Chapter Book</text></docTitle>'
            f'<navMap>\n{nav}\n</navMap></ncx>'
        ), compress_type=ZIP_DEFLATED)
        for index in range(1, CHAPTER_COUNT + 1):
            archive.writestr(f"OEBPS/chapter{index}.html", chapter_html(index), compress_type=ZIP_DEFLATED)


if __name__ == "__main__":
    main()
