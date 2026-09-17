import tempfile
import unittest
from pathlib import Path

from cryptography.fernet import Fernet

from backend.integrations.base import ConnectionTestResult, IntegrationProvider, ProviderDescriptor
from backend.integrations.credentials import CredentialVault
from backend.integrations.registry import ProviderRegistry
from backend.qa.service import QaService
from backend.storage import Storage


class FakeQaProvider(IntegrationProvider):
    @property
    def descriptor(self):
        return ProviderDescriptor("claude", "Claude", "", ())

    def validate_credentials(self, credentials):
        return dict(credentials)

    def test_connection(self, credentials):
        return ConnectionTestResult("connected", "ok", "ok")

    def translate(self, credentials, request):
        raise AssertionError("translate() should not be called")

    def analyze(self, credentials, prompt):
        return "===JSON===\n[]"


class QaRunStorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_record_and_count_qa_runs_by_configured_provider(self):
        project = self.storage.create_project({"title": "QA Runs", "status": "translation"})
        structure = self.storage.save_book_structure(
            project["projectId"],
            "book.epub",
            "application/epub+zip",
            b"book",
            {"chapters": [{"title": "One", "elements": [{"type": "paragraph", "text": "Hello"}]}]},
        )
        chapter_id = structure["chapters"][0]["chapterId"]
        claude = self.storage.create_integration_connection("claude", "Claude", b"secret")
        gemini = self.storage.create_integration_connection("gemini", "Gemini", b"secret")
        self.storage.create_integration_connection("openai", "GPT", b"secret")
        self.storage.update_project(project["projectId"], {
            "aiConfiguration": {"qaConnectionIds": [claude["connectionId"], gemini["connectionId"]]},
        })

        self.storage.record_qa_run(chapter_id, "claude")
        self.storage.record_qa_run(chapter_id, "claude")

        self.assertEqual(
            {"claude": 2, "gemini": 0},
            self.storage.count_qa_runs_by_provider(chapter_id),
        )


class QaRunServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")
        self.vault = CredentialVault(Fernet(Fernet.generate_key()))
        self.service = QaService(self.storage, self.vault, ProviderRegistry([FakeQaProvider()]))

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_successful_multi_batch_qa_logs_one_run_for_last_batch_only(self):
        project = self.storage.create_project({"title": "QA Batches", "status": "translation"})
        structure = self.storage.save_book_structure(
            project["projectId"],
            "book.epub",
            "application/epub+zip",
            b"book",
            {"chapters": [{"title": "One", "elements": [
                {"type": "paragraph", "text": f"Original {index}"} for index in range(6)
            ]}]},
        )
        chapter = structure["chapters"][0]
        for element in chapter["elements"]:
            self.storage.update_paragraph(element["paragraphId"], "Переклад", False)
        connection = self.storage.create_integration_connection(
            "claude",
            "Claude",
            self.vault.encrypt({"apiKey": "secret"}),
        )
        self.storage.update_integration_connection_status(connection["connectionId"], "connected", "ok", "ok", {})

        first = self.service.check_chapter_translation_quality(
            project["projectId"], chapter["chapterId"], [connection["connectionId"]], batch_index=0, batch_size=5,
        )
        self.assertEqual({}, self.storage.count_qa_runs_by_provider(chapter["chapterId"]))

        second = self.service.check_chapter_translation_quality(
            project["projectId"], chapter["chapterId"], [connection["connectionId"]], batch_index=1, batch_size=5,
        )

        self.assertEqual(2, first["totalBatches"])
        self.assertEqual(2, second["totalBatches"])
        self.assertEqual({"claude": 1}, self.storage.count_qa_runs_by_provider(chapter["chapterId"]))

    def test_run_resumed_from_a_nonzero_batch_still_gets_counted(self):
        # A UI-driven QA pass can be interrupted and resumed later, starting
        # from whatever batch_index localStorage last saved — never
        # replaying batch 0. The run must still be counted once it reaches
        # the chapter's final batch.
        project = self.storage.create_project({"title": "QA Resume", "status": "translation"})
        structure = self.storage.save_book_structure(
            project["projectId"],
            "book.epub",
            "application/epub+zip",
            b"book",
            {"chapters": [{"title": "One", "elements": [
                {"type": "paragraph", "text": f"Original {index}"} for index in range(6)
            ]}]},
        )
        chapter = structure["chapters"][0]
        for element in chapter["elements"]:
            self.storage.update_paragraph(element["paragraphId"], "Переклад", False)
        connection = self.storage.create_integration_connection(
            "claude",
            "Claude",
            self.vault.encrypt({"apiKey": "secret"}),
        )
        self.storage.update_integration_connection_status(connection["connectionId"], "connected", "ok", "ok", {})

        resumed = self.service.check_chapter_translation_quality(
            project["projectId"], chapter["chapterId"], [connection["connectionId"]], batch_index=1, batch_size=5,
        )

        self.assertEqual(2, resumed["totalBatches"])
        self.assertEqual({"claude": 1}, self.storage.count_qa_runs_by_provider(chapter["chapterId"]))


if __name__ == "__main__":
    unittest.main()