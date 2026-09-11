"""Patch 20: translation progress % on project cards.

Backfills the "Прогрес перекладу" value on project cards, which has always
shown 0% because storage.list_projects() never returned a `progress` field
(the frontend already reads project.progress.progress — this just supplies it).
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
STORAGE_PATH = REPO_ROOT / "backend" / "storage.py"


def apply_patch() -> None:
    text = STORAGE_PATH.read_text(encoding="utf-8")

    old_list_projects = '''    def list_projects(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT project_id, title, author_id, series_id, status "
                "FROM book_projects ORDER BY created_at"
            ).fetchall()
        return [self._project_summary_from_row(row) for row in rows]
'''
    new_list_projects = '''    def list_projects(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT project_id, title, author_id, series_id, status "
                "FROM book_projects ORDER BY created_at"
            ).fetchall()
            progress_rows = connection.execute(
                "SELECT bdoc.project_id AS project_id, "
                "COUNT(*) AS total_paragraphs, "
                "SUM(CASE WHEN bp.reviewed = 1 THEN 1 ELSE 0 END) AS reviewed_paragraphs "
                "FROM book_paragraphs bp "
                "JOIN book_chapters bch ON bch.chapter_id = bp.chapter_id "
                "JOIN book_documents bdoc ON bdoc.book_id = bch.book_id "
                "WHERE bp.is_service = 0 "
                "GROUP BY bdoc.project_id"
            ).fetchall()
        progress_by_project = {
            row["project_id"]: (row["reviewed_paragraphs"] or 0, row["total_paragraphs"] or 0)
            for row in progress_rows
        }
        return [
            self._project_summary_from_row(row, progress_by_project.get(row["project_id"], (0, 0)))
            for row in rows
        ]
'''
    if old_list_projects not in text:
        raise SystemExit("list_projects() body not found — file may have changed, aborting.")
    text = text.replace(old_list_projects, new_list_projects, 1)

    old_summary = '''    @staticmethod
    def _project_summary_from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "projectId": row["project_id"],
            "title": row["title"],
            "authorId": row["author_id"],
            "seriesId": row["series_id"],
            "status": row["status"],
        }
'''
    new_summary = '''    @staticmethod
    def _project_summary_from_row(row: sqlite3.Row, progress: tuple[int, int] = (0, 0)) -> dict[str, Any]:
        reviewed, total = progress
        percent = round((reviewed / total) * 100) if total else 0
        return {
            "projectId": row["project_id"],
            "title": row["title"],
            "authorId": row["author_id"],
            "seriesId": row["series_id"],
            "status": row["status"],
            "progress": {"progress": percent},
        }
'''
    if old_summary not in text:
        raise SystemExit("_project_summary_from_row() body not found — file may have changed, aborting.")
    text = text.replace(old_summary, new_summary, 1)

    STORAGE_PATH.write_text(text, encoding="utf-8")
    print(f"Patched {STORAGE_PATH}")


if __name__ == "__main__":
    apply_patch()
