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

    def test_updates_paragraph_with_literal_formatting_markers(self):
        marked_text = "Текст <i><b>із форматуванням</b></i>"
        handler = FakeApiHandler({"translationText": marked_text, "reviewed": True})
        saved = {"paragraphId": "paragraph-1", "translationText": marked_text, "reviewed": True}
        with patch("backend.server.storage.update_paragraph", return_value=saved) as updater:
            status, payload = WorkbenchHandler.handle_api(handler, "PATCH", "/api/paragraphs/paragraph-1")

        self.assertEqual(200, status)
        self.assertEqual(saved, payload)
        updater.assert_called_once_with("paragraph-1", marked_text, True, None, None)

    def test_sets_paragraph_narrator_change(self):
        handler = FakeApiHandler({"narratorChange": "masc"})
        saved = {"paragraphId": "paragraph-1", "narratorChange": "masc"}
        with patch("backend.server.storage.set_paragraph_narrator_change", return_value=saved) as setter:
            status, payload = WorkbenchHandler.handle_api(handler, "PUT", "/api/paragraphs/paragraph-1/narrator-change")

        self.assertEqual(200, status)
        self.assertEqual(saved, payload)
        setter.assert_called_once_with("paragraph-1", "masc")

    def test_clears_paragraph_narrator_change(self):
        handler = FakeApiHandler({"narratorChange": None})
        saved = {"paragraphId": "paragraph-1", "narratorChange": None}
        with patch("backend.server.storage.set_paragraph_narrator_change", return_value=saved) as setter:
            status, payload = WorkbenchHandler.handle_api(handler, "PATCH", "/api/paragraphs/paragraph-1/narrator-change")

        self.assertEqual(200, status)
        self.assertEqual(saved, payload)
        setter.assert_called_once_with("paragraph-1", None)

    def test_rejects_invalid_paragraph_narrator_change(self):
        handler = FakeApiHandler({"narratorChange": "nonbinary"})
        with patch("backend.server.storage.set_paragraph_narrator_change", side_effect=ValueError("Narrator gender must be 'masc', 'femn', 'third', or omitted.")):
            status, payload = WorkbenchHandler.handle_api(handler, "PUT", "/api/paragraphs/paragraph-1/narrator-change")

        self.assertEqual(400, status)
        self.assertIn("error", payload)

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