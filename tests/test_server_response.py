from io import BytesIO
import unittest

from backend.server import WorkbenchHandler


class FakeHandler:
    def __init__(self):
        self.status = None
        self.headers = {}
        self.wfile = BytesIO()

    def send_response(self, status):
        self.status = status

    def send_header(self, name, value):
        self.headers[name] = value

    def end_headers(self):
        pass


class WorkbenchHandlerResponseTests(unittest.TestCase):
    def test_204_response_has_no_body(self):
        handler = FakeHandler()

        WorkbenchHandler.send_json(handler, 204, None)

        self.assertEqual(handler.status, 204)
        self.assertEqual(handler.headers.get("Content-Length"), "0")
        self.assertNotIn("Content-Type", handler.headers)
        self.assertEqual(handler.wfile.getvalue(), b"")


if __name__ == "__main__":
    unittest.main()