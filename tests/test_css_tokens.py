"""The stylesheet keeps to one scale: spacing, radii and line widths come from the tokens at the top of styles.css."""

from pathlib import Path
import re
import unittest

CSS = (Path(__file__).resolve().parent.parent / "frontend" / "styles.css").read_text(encoding="utf-8")
NO_COMMENTS = re.sub(r"/\*.*?\*/", lambda match: " " * len(match.group(0)), CSS, flags=re.S)
DECLARATION = re.compile(r"(?<![\w-])([a-z-]+)\s*:\s*([^;{}]+)(?:;|(?=\}))")
SPACING = re.compile(r"^(?:padding|margin)(?:-(?:top|right|bottom|left|inline|block)(?:-(?:start|end))?)?$|^(?:gap|row-gap|column-gap)$")
BORDER = re.compile(r"^border(?:-(?:top|right|bottom|left))?(?:-width)?$")
LITERAL = re.compile(r"(?<![\w.\-])(-?\d+(?:\.\d+)?)(px|rem|em)\b")
LARGE_LAYOUT_VALUE = 40  # from this size on a value is a layout size (a sheet width, a bottom reserve), not a gap


def declarations():
    for block in re.finditer(r"\{([^{}]*)\}", NO_COMMENTS):
        for declaration in DECLARATION.finditer(block.group(1)):
            yield declaration.group(1).strip().lower(), declaration.group(2).strip()


class StylesheetTokenTests(unittest.TestCase):
    def test_the_tokens_exist(self):
        for token in ("--space-1: 4px", "--space-2: 8px", "--space-3: 12px", "--space-4: 16px", "--space-5: 24px", "--space-6: 32px",
                      "--radius-control: 12px", "--radius-card: 16px", "--radius-chip: 6px", "--radius-pill: 999px",
                      "--border-width: 1px", "--accent-line: 2px", "--font-ui:", "--shadow-card:", "--shadow-btn:", "--shadow-menu:"):
            self.assertIn(token, CSS)

    def test_spacing_uses_the_scale(self):
        offenders = []
        for prop, value in declarations():
            if not SPACING.match(prop) or "(" in value and "var(" not in value:
                continue
            for number, _unit in ((m.group(1), m.group(2)) for m in LITERAL.finditer(re.sub(r"var\([^)]*\)", "", value))):
                size = float(number)
                if size == 0 or size <= -1 and size >= -8 or abs(size) >= LARGE_LAYOUT_VALUE:
                    continue
                offenders.append(f"{prop}: {value}")
        self.assertEqual(offenders, [], "spacing literals outside the scale (use var(--space-*)):\n" + "\n".join(sorted(set(offenders))[:20]))

    def test_frames_use_the_hairline_or_the_accent_line(self):
        offenders = [f"{prop}: {value}" for prop, value in declarations()
                     if BORDER.match(prop) and LITERAL.search(re.sub(r"var\([^)]*\)", "", value))]
        self.assertEqual(offenders, [], "border widths must be var(--border-width) or var(--accent-line):\n" + "\n".join(sorted(set(offenders))[:20]))

    def test_no_inset_stripe_with_a_literal_width(self):
        offenders = re.findall(r"box-shadow\s*:\s*inset\s+-?\d+px[^;]*;", NO_COMMENTS)
        self.assertEqual(offenders, [], "a stripe is inset var(--accent-line) 0 0 <colour>")

    def test_radii_come_from_the_three_tokens(self):
        offenders = []
        for prop, value in declarations():
            if prop != "border-radius":
                continue
            rest = re.sub(r"var\(--radius-(?:control|card|chip|pill)\)", "", value)
            if re.sub(r"[\s0]|50%", "", rest) != "":
                offenders.append(value)
        self.assertEqual(offenders, [], "radii must be var(--radius-control|card|chip|pill), 0 or 50%:\n" + "\n".join(sorted(set(offenders))))


    def test_corner_radii_of_single_corners_use_tokens_too(self):
        offenders = [f"{prop}: {value}" for prop, value in declarations()
                     if re.match(r"^border-(?:top|bottom)-(?:left|right)-radius$", prop) and not re.fullmatch(r"var\(--radius-[a-z]+\)|0", value)]
        self.assertEqual(offenders, [])

    def test_shadows_come_from_the_tokens(self):
        allowed = (r"none", r"var\(--shadow-[a-z]+\)", r"inset var\(--accent-line\) 0 0 var\(--color-[\w-]+\)", r"0 0 0 1px var\(--color-[\w-]+\)")
        offenders = [value for prop, value in declarations()
                     if prop == "box-shadow" and not any(re.fullmatch(pattern, value) for pattern in allowed)]
        self.assertEqual(offenders, [], "box-shadow must be a --shadow-* token (or a stripe / ring on a colour token)")


if __name__ == "__main__":
    unittest.main()
