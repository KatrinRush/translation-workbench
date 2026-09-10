import unittest
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from backend.parsers.epub import _extract_ordered_content, parse_epub


FORMATTED_BODY = """
<p>Simple <b>bold</b>, <i>italic</i>, <em>emphasis</em>, <strong>strong</strong>, <s>gone</s>, <strike>struck</strike>, <del>deleted</del>.</p>
<p>Nested <em><strong>formatting</strong></em> works.</p>
<p>Space stays between<b> </b>words.</p>
<div><strong>Direct</strong> child.</div>
"""

PLAIN_BODY = """
<p>Simple bold, italic, emphasis, strong, gone, struck, deleted.</p>
<p>Nested formatting works.</p>
<p>Space stays between words.</p>
<div>Direct child.</div>
"""


def xhtml(body):
    return f'<html xmlns="http://www.w3.org/1999/xhtml"><body>{body}</body></html>'


def epub_bytes(body):
    container = """<?xml version="1.0"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OPS/package.opf"/></rootfiles>
</container>"""
    package = """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf">
  <metadata><title>Inline formatting</title><creator>Test</creator><language>en</language></metadata>
  <manifest><item id="chapter" href="chapter.xhtml" media-type="application/xhtml+xml"/></manifest>
  <spine><itemref idref="chapter"/></spine>
</package>"""
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OPS/package.opf", package)
        archive.writestr("OPS/chapter.xhtml", xhtml(body))
    return output.getvalue()


class EpubInlineFormattingTests(unittest.TestCase):
    def test_extract_ordered_content_preserves_canonical_inline_formatting(self):
        elements = _extract_ordered_content(
            xhtml(FORMATTED_BODY),
            {},
            "OPS/chapter.xhtml",
        )

        self.assertEqual(
            [element["text"] for element in elements],
            [
                "Simple <b>bold</b>, <i>italic</i>, <i>emphasis</i>, <b>strong</b>, "
                "<s>gone</s>, <s>struck</s>, <s>deleted</s>.",
                "Nested <i><b>formatting</b></i> works.",
                "Space stays between words.",
                "<b>Direct</b> child.",
            ],
        )
        self.assertEqual(
            [element["wordCount"] for element in elements],
            [8, 3, 4, 2],
        )

    def test_parse_epub_word_count_matches_unformatted_text(self):
        formatted = parse_epub("formatted.epub", epub_bytes(FORMATTED_BODY))
        plain = parse_epub("plain.epub", epub_bytes(PLAIN_BODY))

        self.assertEqual(formatted["chapters"][0]["wordCount"], plain["chapters"][0]["wordCount"])
        self.assertEqual(formatted["wordCount"], plain["wordCount"])
        self.assertEqual(formatted["wordCount"], 17)


if __name__ == "__main__":
    unittest.main()
