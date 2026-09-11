"""Patch 23: fix test_projects_list_returns_only_card_metadata after patch 20
added a "progress" field to list_projects()'s output. The test's expected
field set was never updated to match — CI caught it, this fixes the test,
not the feature."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
_IGNORED_PARTS = {"node_modules", ".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".cache"}


def _find(filename: str) -> Path:
    candidates = [
        path for path in REPO_ROOT.rglob(filename)
        if not any(part in _IGNORED_PARTS for part in path.parts)
    ]
    if not candidates:
        raise SystemExit(f"Could not find {filename} under {REPO_ROOT} — aborting.")
    if len(candidates) > 1:
        raise SystemExit(f"Found more than one {filename}: {candidates} — aborting, resolve manually.")
    return candidates[0]


def apply_patch() -> None:
    path = _find("test_projects_api.py")
    text = path.read_text(encoding="utf-8")
    old = '''self.assertEqual(set(projects[0]), {"projectId", "title", "authorId", "seriesId", "status"})'''
    new = '''self.assertEqual(set(projects[0]), {"projectId", "title", "authorId", "seriesId", "status", "progress"})'''
    if old not in text:
        raise SystemExit("Expected assertion line not found — file may have changed, aborting.")
    if text.count(old) > 1:
        raise SystemExit("Expected assertion line is not unique — aborting to avoid a wrong edit.")
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    print(f"Patched {path}")


if __name__ == "__main__":
    apply_patch()
