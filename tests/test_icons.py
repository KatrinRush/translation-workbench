"""The interface has one icon set (Lucide, inline sprite): no pictographs in the markup, every icon that is used exists."""

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent
HTML = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
JS = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
PICTOGRAPHS = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐↩↪⏩-⏺▲▼▴▾⋯]️?")


def visible_markup():
    without_comments = re.sub(r"<!--.*?-->", "", HTML, flags=re.S)
    return re.sub(r"<symbol .*?</symbol>", "", without_comments, flags=re.S)


class IconTests(unittest.TestCase):
    def test_no_pictographs_in_the_markup(self):
        found = sorted({match.group(0) for match in PICTOGRAPHS.finditer(visible_markup())})
        self.assertEqual(found, [], "use an <svg class=\"icon\"> from the sprite instead of: " + " ".join(found))

    def test_no_pictographs_drawn_by_the_script(self):
        offenders = []
        for number, line in enumerate(JS.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith(("//", "/*", "*")):
                continue
            # a mark kept for screen readers is the last argument of iconLabel(...), the only place a glyph may stay
            code = re.sub(r"iconLabel\([^;]*?, '(?:✓|≠|⚠|✎)'\)", "iconLabel(...)", line)
            code = re.sub(r"srMark\('(?:✓|≠|⚠|✎)'\)", "srMark(...)", code)
            if re.search("[\U0001F300-\U0001FAFF☀-➿▲▼▴▾⋯]️?", code) and "⚠" not in code:
                offenders.append(f"{number}: {stripped[:100]}")
        self.assertEqual(offenders, [], "pictographs in app.js:\n" + "\n".join(offenders[:15]))

    def test_every_icon_in_use_is_in_the_sprite(self):
        defined = set(re.findall(r'<symbol id="i-([a-z0-9-]+)"', HTML))
        used = set(re.findall(r'href="#i-([a-z0-9-]+)"', HTML)) | set(re.findall(r"icon\('([a-z0-9-]+)'\)", JS)) \
            | set(re.findall(r"iconLabel\('([a-z0-9-]+)'", JS)) | set(re.findall(r"icon\([^)]*\? '([a-z0-9-]+)' : '([a-z0-9-]+)'\)", JS) and [])
        for pair in re.findall(r"icon\([^()]*\? '([a-z0-9-]+)' : '([a-z0-9-]+)'\)", JS):
            used.update(pair)
        self.assertGreater(len(defined), 15)
        self.assertEqual(sorted(used - defined), [], "icons used but missing from the sprite")

    def test_the_licence_of_the_icon_set_is_stated(self):
        self.assertIn("Lucide", HTML)
        self.assertIn("ISC", HTML)
        self.assertIn("Lucide", README)


if __name__ == "__main__":
    unittest.main()
