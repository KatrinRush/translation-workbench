"""Patch 50 — fix tests broken by patch 44's queuedForQa param.

Run from the repo root: python apply_patch50.py

Patch 44 added a 5th positional param to storage.update_paragraph
(queued_for_qa) and server.py's PATCH/PUT /api/paragraphs/{id} handler
now always forwards it (None when the request doesn't include
"queuedForQa"). Two existing tests asserted the old 4-arg call shape
and now fail — this just updates both expectations to include the
trailing None, matching current, correct behavior (no queuedForQa key
in the request body means "leave the flag alone").

Run the suite after applying to confirm both are green:
    python -m unittest tests.test_server_response tests.test_chapter_routes
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"Expected exactly 1 match in {path} for a replacement, found {count}.\n"
            f"--- old_str ---\n{old}\n--- end ---"
        )
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_test_server_response() -> None:
    path = REPO_ROOT / "tests" / "test_server_response.py"
    replace_once(
        path,
        '''        update_paragraph.assert_called_once_with("paragraph-1", "Переклад", True, True)''',
        '''        update_paragraph.assert_called_once_with("paragraph-1", "Переклад", True, True, None)''',
    )
    print(f"test_server_response.py patched: {path}")


def patch_test_chapter_routes() -> None:
    path = REPO_ROOT / "tests" / "test_chapter_routes.py"
    replace_once(
        path,
        '''        updater.assert_called_once_with("paragraph-1", marked_text, True, None)''',
        '''        updater.assert_called_once_with("paragraph-1", marked_text, True, None, None)''',
    )
    print(f"test_chapter_routes.py patched: {path}")


if __name__ == "__main__":
    patch_test_server_response()
    patch_test_chapter_routes()
    print("Patch 50 applied.")
