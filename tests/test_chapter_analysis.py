import tempfile
import unittest
from pathlib import Path

from cryptography.fernet import Fernet

from backend.integrations.base import ConnectionTestResult, IntegrationProvider, ProviderDescriptor
from backend.integrations.credentials import CredentialVault
from backend.integrations.registry import ProviderRegistry
from backend.storage import Storage
from backend.translations.service import TranslationService


class FakeAnalysisProvider(IntegrationProvider):
    def __init__(self, provider_id):
        self.provider_id = provider_id
        self.analysis_prompts = []

    @property
    def descriptor(self):
        return ProviderDescriptor(self.provider_id, self.provider_id.title(), "", ())

    def validate_credentials(self, credentials):
        return dict(credentials)

    def test_connection(self, credentials):
        return ConnectionTestResult("connected", "ok", "ok")

    def translate(self, credentials, request):
        raise AssertionError("translate() should not be called")

    def analyze(self, credentials, prompt):
        self.analysis_prompts.append(prompt)
        return f"analysis from {self.provider_id}"


class ChapterAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")
        self.vault = CredentialVault(Fernet(Fernet.generate_key()))
        self.providers = [FakeAnalysisProvider("openai"), FakeAnalysisProvider("gemini"), FakeAnalysisProvider("claude")]
        self.service = TranslationService(self.storage, self.vault, ProviderRegistry(self.providers))
        self.project = self.storage.create_project({
            "title": "Analysis book",
            "status": "translation",
            "translationRules": "Keep names consistent.",
            "projectRuleIds": [],
            "projectGlossaryEntryIds": [],
            "aiConfiguration": {},
        })
        self.storage.save_book_structure(
            self.project["projectId"],
            "book.epub",
            "application/epub+zip",
            b"book",
            {"chapters": [{"title": "Opening", "elements": [{"type": "paragraph", "text": "The river was silent."}]}]},
        )
        self.chapter = self.storage.get_book_structure(self.project["projectId"])["chapters"][0]
        self.connections = []
        for provider in self.providers:
            connection = self.storage.create_integration_connection(
                provider.provider_id,
                provider.provider_id,
                self.vault.encrypt({"apiKey": f"{provider.provider_id}-secret"}),
            )
            self.storage.update_integration_connection_status(connection["connectionId"], "connected", "ok", "ok", {})
            self.connections.append(connection)
        self.storage.update_project(self.project["projectId"], {
            "aiConfiguration": {"analysisConnectionIds": [self.connections[0]["connectionId"], self.connections[1]["connectionId"]]},
        })

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_selected_models_receive_same_original_and_results_are_persisted_separately(self):
        response = self.service.analyze_chapter(
            self.project["projectId"],
            self.chapter["chapterId"],
            {
                "categories": ["POV / оповідач", "Атмосфера"],
                "customPrompt": "Зверни увагу на ритм.",
                "connectionIds": [self.connections[0]["connectionId"], self.connections[1]["connectionId"]],
            },
        )

        self.assertEqual("analysis from openai", response["results"]["openai"]["text"])
        self.assertEqual("analysis from gemini", response["results"]["gemini"]["text"])
        self.assertNotIn("claude", response["results"])
        self.assertEqual(1, len(self.providers[0].analysis_prompts))
        self.assertEqual(1, len(self.providers[1].analysis_prompts))
        self.assertEqual([], self.providers[2].analysis_prompts)
        self.assertEqual(self.providers[0].analysis_prompts, self.providers[1].analysis_prompts)
        self.assertIn("The river was silent.", self.providers[0].analysis_prompts[0])
        self.assertIn("POV / оповідач", self.providers[0].analysis_prompts[0])
        self.assertIn("Зверни увагу на ритм.", self.providers[0].analysis_prompts[0])

        restored = self.storage.get_book_structure(self.project["projectId"])["chapters"][0]
        self.assertEqual("analysis from openai", restored["aiAnalysisResults"]["openai"]["text"])
        self.assertEqual("analysis from gemini", restored["aiAnalysisResults"]["gemini"]["text"])

    def test_unconfigured_connection_is_rejected(self):
        with self.assertRaisesRegex(Exception, "configured for this project"):
            self.service.analyze_chapter(
                self.project["projectId"],
                self.chapter["chapterId"],
                {"categories": ["Атмосфера"], "connectionIds": [self.connections[2]["connectionId"]]},
            )


if __name__ == "__main__":
    unittest.main()
