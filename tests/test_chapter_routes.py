from io import BytesIO
import unittest
from unittest.mock import patch

from backend.server import WorkbenchHandler


class FakeApiHandler:
    def __init__(self, payload=None, path=""):
        self.payload = payload
        self.path = path
        self.status = None
        self.headers = {}
        self.wfile = BytesIO()

    def read_json(self):
        return self.payload

    def send_response(self, status):
        self.status = status

    def send_header(self, name, value):
        self.headers[name] = value

    def end_headers(self):
        pass

    send_json = WorkbenchHandler.send_json
    send_download = WorkbenchHandler.send_download


class ChapterRoutesTests(unittest.TestCase):
    def test_updates_chapter_export_flag(self):
        handler = FakeApiHandler({"excludeFromExport": True})
        structure = {"chapters": [{"chapterId": "chapter-1"}]}
        with (
            patch("backend.server.storage.get_book_structure", return_value=structure),
            patch("backend.server.storage.set_chapter_export_flag", return_value=True) as setter,
        ):
            status, payload = WorkbenchHandler.handle_api(
                handler,
                "PATCH",
                "/api/projects/project-1/chapters/chapter-1/export-flag",
            )

        self.assertEqual(200, status)
        self.assertEqual({"chapterId": "chapter-1", "excludeFromExport": True}, payload)
        setter.assert_called_once_with("chapter-1", True)

    def test_downloads_docx_with_expected_headers(self):
        handler = FakeApiHandler(path="/api/projects/project-1/export/docx?format=bilingual")
        with (
            patch("backend.server.storage.get_project", return_value={"title": "My Book"}),
            patch("backend.server.export_service.generate_docx", return_value=BytesIO(b"docx")) as generate,
        ):
            WorkbenchHandler.do_GET(handler)

        self.assertEqual(200, handler.status)
        self.assertEqual("application/vnd.openxmlformats-officedocument.wordprocessingml.document", handler.headers["Content-Type"])
        self.assertIn('filename="My_Book-bilingual.docx"', handler.headers["Content-Disposition"])
        self.assertEqual(b"docx", handler.wfile.getvalue())
        generate.assert_called_once_with("project-1", "bilingual")


if __name__ == "__main__":
    unittest.main()