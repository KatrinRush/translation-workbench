import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet

from backend import server
from backend.integrations.base import ConnectionTestResult, GlossaryDefinition, GlossaryLimitError, GlossarySummary, IntegrationProvider, ProviderDescriptor, TranslationRequest, TranslationResult
from backend.integrations.credentials import CredentialVault
from backend.integrations.registry import ProviderRegistry
from backend.storage import Storage
from backend.translations.service import TranslationService


class FakeHandler:
    def __init__(self, payload=None):
        self.payload = payload

    def read_json(self):
        return self.payload


class FakeGlossaryProvider(IntegrationProvider):
    def __init__(self):
        self.created = []
        self.deleted = []

    @property
    def descriptor(self):
        return ProviderDescriptor("deepl", "DeepL", "", ())

    def validate_credentials(self, credentials):
        return dict(credentials)

    def test_connection(self, credentials):
        return ConnectionTestResult("connected", "ok", "ok")

    def create_glossary(self, credentials, glossary: GlossaryDefinition):
        glossary_id = f"remote-{len(self.created) + 1}"
        self.created.append((glossary_id, glossary))
        return glossary_id

    def delete_glossary(self, credentials, glossary_id):
        self.deleted.append(glossary_id)

    def translate(self, credentials, request: TranslationRequest):
        return TranslationResult("переклад", "EN")


class FakeAccountScopedGlossaryProvider(FakeGlossaryProvider):
    """Models DeepL's real behavior: only one glossary may exist per language pair on the
    whole account, regardless of which local connection_id or glossary_rule_id created it.
    Unlike FakeGlossaryProvider, this also supports list_glossaries, so it can be used to
    exercise the takeover-recovery path in TranslationService."""

    def __init__(self):
        super().__init__()
        self._remote = {}
        self._counter = 0

    def create_glossary(self, credentials, glossary: GlossaryDefinition):
        for source_language, target_language in self._remote.values():
            if source_language == glossary.source_language and target_language == glossary.target_language:
                raise GlossaryLimitError("DeepL досяг ліміту глосаріїв.")
        self._counter += 1
        glossary_id = f"remote-{self._counter}"
        self._remote[glossary_id] = (glossary.source_language, glossary.target_language)
        self.created.append((glossary_id, glossary))
        return glossary_id

    def delete_glossary(self, credentials, glossary_id):
        self._remote.pop(glossary_id, None)
        self.deleted.append(glossary_id)

    def list_glossaries(self, credentials):
        return [
            GlossarySummary(glossary_id, source_language, target_language)
            for glossary_id, (source_language, target_language) in self._remote.items()
        ]


class GlossaryLimitTakeoverTests(unittest.TestCase):
    """Regression coverage for the scenario where DeepL already holds a glossary for a
    language pair that our own provider_glossary_sync bookkeeping doesn't know about,
    because that bookkeeping is keyed by our local connection_id rather than by the actual
    DeepL account. This happens in practice when two local connections end up pointing at
    the same DeepL account (e.g. one was deleted and re-created to rotate the API key,
    leaving old tracking rows behind before connection-delete cleanup existed)."""

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")
        self.vault = CredentialVault(Fernet(Fernet.generate_key()))
        self.provider = FakeAccountScopedGlossaryProvider()
        self.service = TranslationService(self.storage, self.vault, ProviderRegistry([self.provider]))

    def _connected_connection(self, display_name="DeepL"):
        connection = self.storage.create_integration_connection(
            "deepl", display_name, self.vault.encrypt({"apiKey": "test-key"})
        )
        self.storage.update_integration_connection_status(
            connection["connectionId"], "connected", "ok", "ok", {}
        )
        return connection

    def _commit_glossary(self, project_id, connection_id=None):
        item = self.storage.create_glossary_entry(
            {"source": "river", "target": "ріка", "note": "", "active": True}
        )
        data = {
            "sourceLanguage": "EN",
            "targetLanguage": "UK",
            "glossaryEntryIds": [item["glossaryEntryId"]],
        }
        if connection_id is not None:
            data["connectionId"] = connection_id
        return self.service.commit_project_glossary_draft(project_id, data)

    def test_takes_over_slot_occupied_via_a_different_local_connection(self):
        old_connection = self._connected_connection("DeepL (old key)")
        old_project = self.storage.create_project({"title": "Old owner", "status": "translation"})
        first = self._commit_glossary(old_project["projectId"], old_connection["connectionId"])
        self.assertEqual("synced", first["providerSyncResult"]["status"])
        occupied_remote_id = first["providerSync"]["remoteGlossaryId"]

        # A second local connection ends up pointing at the same actual DeepL account
        # (e.g. the old one was deleted and re-created to rotate the key). Committing a
        # different project's glossary for the same language pair through it must not
        # surface DeepL's limit error to the user — it must take over the slot.
        new_connection = self._connected_connection("DeepL (new key)")
        new_project = self.storage.create_project({"title": "Fool me once", "status": "translation"})
        second = self._commit_glossary(new_project["projectId"], new_connection["connectionId"])

        self.assertEqual("synced", second["providerSyncResult"]["status"])
        self.assertEqual([occupied_remote_id], self.provider.deleted)
        self.assertNotEqual(occupied_remote_id, second["providerSync"]["remoteGlossaryId"])

        # The stale tracking row under the old connection must be gone too, not just the
        # remote glossary, otherwise it would keep pointing at a deleted glossary_id forever.
        self.assertIsNone(
            self.storage.get_provider_glossary_sync(old_connection["connectionId"], "EN", "UK")
        )

    def test_limit_error_without_a_recoverable_conflict_still_surfaces(self):
        # If the provider can't explain the 456 (nothing it lists matches the pair, or the
        # provider doesn't support listing at all), we must not swallow the error.
        class NonRecoverableProvider(FakeAccountScopedGlossaryProvider):
            def create_glossary(self, credentials, glossary):
                raise GlossaryLimitError("DeepL досяг ліміту глосаріїв.")

            def list_glossaries(self, credentials):
                return []

        self.provider = NonRecoverableProvider()
        self.service = TranslationService(self.storage, self.vault, ProviderRegistry([self.provider]))
        connection = self._connected_connection()
        project = self.storage.create_project({"title": "Blocked", "status": "translation"})

        result = self._commit_glossary(project["projectId"], connection["connectionId"])

        self.assertEqual("failed", result["providerSyncResult"]["status"])
        self.assertEqual("glossary_limit_reached", result["providerSyncResult"]["code"])


class ReleaseProjectGlossariesTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")
        self.vault = CredentialVault(Fernet(Fernet.generate_key()))
        self.provider = FakeGlossaryProvider()
        self.service = TranslationService(self.storage, self.vault, ProviderRegistry([self.provider]))
        self.project = self.storage.create_project({"title": "Glossary book", "status": "translation"})
        self.connection = self.storage.create_integration_connection(
            "deepl", "DeepL", self.vault.encrypt({"apiKey": "test-key"})
        )
        self.storage.update_integration_connection_status(
            self.connection["connectionId"], "connected", "ok", "ok", {}
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _delete_project(self):
        with patch.object(server, "storage", self.storage), \
                patch.object(server, "translation_service", self.service):
            return server.WorkbenchHandler.handle_api(
                FakeHandler(), "DELETE", f"/api/projects/{self.project['projectId']}"
            )

    def _create_synced_glossary(self):
        item = self.storage.create_glossary_entry(
            {"source": "river", "target": "ріка", "note": "", "active": True}
        )
        return self.service.commit_project_glossary_draft(
            self.project["projectId"],
            {
                "sourceLanguage": "EN",
                "targetLanguage": "UK",
                "glossaryEntryIds": [item["glossaryEntryId"]],
            },
        )

    def test_project_delete_releases_remote_glossary(self):
        saved = self._create_synced_glossary()
        remote_glossary_id = saved["providerSync"]["remoteGlossaryId"]

        status, _ = self._delete_project()

        self.assertEqual(204, status)
        self.assertEqual([remote_glossary_id], self.provider.deleted)
        self.assertIsNone(self.storage.get_project(self.project["projectId"]))
        remaining = self.storage.list_project_translation_glossaries(self.project["projectId"])
        self.assertEqual([], remaining)

    def test_project_delete_succeeds_when_remote_delete_fails(self):
        saved = self._create_synced_glossary()
        glossary_rule_id = saved["glossaryRuleId"]
        connection_id = self.connection["connectionId"]

        def failing_delete(credentials, glossary_id):
            raise ValueError("DeepL unavailable")

        self.provider.delete_glossary = failing_delete

        status, _ = self._delete_project()

        self.assertEqual(204, status)
        self.assertIsNone(self.storage.get_project(self.project["projectId"]))

    def test_provider_is_not_called_for_glossary_without_sync(self):
        self.storage.upsert_project_translation_glossary(self.project["projectId"], {
            "sourceLanguage": "EN",
            "targetLanguage": "UK",
            "entries": [{"source": "river", "target": "ріка", "context": ""}],
            "contentHash": "content-hash",
        })

        with patch.object(self.provider, "delete_glossary") as delete_mock:
            status, _ = self._delete_project()

        self.assertEqual(204, status)
        delete_mock.assert_not_called()
        self.assertIsNone(self.storage.get_project(self.project["projectId"]))

    def test_project_delete_does_not_release_slot_taken_over_by_another_project(self):
        first = self._create_synced_glossary()
        second_project = self.storage.create_project({"title": "Second book", "status": "translation"})
        second_item = self.storage.create_glossary_entry(
            {"source": "forest", "target": "ліс", "note": "", "active": True}
        )
        second = self.service.commit_project_glossary_draft(
            second_project["projectId"],
            {"sourceLanguage": "EN", "targetLanguage": "UK", "glossaryEntryIds": [second_item["glossaryEntryId"]]},
        )
        self.assertEqual([first["providerSync"]["remoteGlossaryId"]], self.provider.deleted)

        status, _ = self._delete_project()

        self.assertEqual(204, status)
        self.assertEqual([first["providerSync"]["remoteGlossaryId"]], self.provider.deleted)
        active = self.storage.get_provider_glossary_sync(self.connection["connectionId"], "EN", "UK")
        self.assertEqual(second["glossaryRuleId"], active["glossaryRuleId"])


class ReleaseConnectionGlossariesTests(unittest.TestCase):
    """Deleting a connection has no FK cascade into provider_glossary_sync, so without
    explicit release-on-delete, remote glossaries synced through it are never removed
    from the provider account and pile up until the account's glossary limit is hit."""

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")
        self.vault = CredentialVault(Fernet(Fernet.generate_key()))
        self.provider = FakeGlossaryProvider()
        self.service = TranslationService(self.storage, self.vault, ProviderRegistry([self.provider]))
        self.project = self.storage.create_project({"title": "Glossary book", "status": "translation"})
        self.connection = self.storage.create_integration_connection(
            "deepl", "DeepL", self.vault.encrypt({"apiKey": "test-key"})
        )
        self.storage.update_integration_connection_status(
            self.connection["connectionId"], "connected", "ok", "ok", {}
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _delete_connection(self, connection_id):
        with patch.object(server, "storage", self.storage), \
                patch.object(server, "translation_service", self.service), \
                patch.object(server, "integration_service") as integration_service_mock:
            integration_service_mock.delete_connection.side_effect = (
                lambda cid: self.storage.delete_integration_connection(cid)
            )
            return server.WorkbenchHandler.handle_api(
                FakeHandler(), "DELETE", f"/api/connections/{connection_id}"
            )

    def _create_synced_glossary(self):
        item = self.storage.create_glossary_entry(
            {"source": "river", "target": "ріка", "note": "", "active": True}
        )
        return self.service.commit_project_glossary_draft(
            self.project["projectId"],
            {
                "sourceLanguage": "EN",
                "targetLanguage": "UK",
                "glossaryEntryIds": [item["glossaryEntryId"]],
            },
        )

    def test_connection_delete_releases_remote_glossary(self):
        saved = self._create_synced_glossary()
        remote_glossary_id = saved["providerSync"]["remoteGlossaryId"]
        connection_id = self.connection["connectionId"]

        status, _ = self._delete_connection(connection_id)

        self.assertEqual(204, status)
        self.assertEqual([remote_glossary_id], self.provider.deleted)
        self.assertIsNone(self.storage.get_integration_connection(connection_id))
        self.assertEqual([], self.storage.list_provider_glossary_sync_for_connection(connection_id))

    def test_connection_delete_succeeds_when_remote_delete_fails(self):
        self._create_synced_glossary()
        connection_id = self.connection["connectionId"]

        def failing_delete(credentials, glossary_id):
            raise ValueError("DeepL unavailable")

        self.provider.delete_glossary = failing_delete

        status, _ = self._delete_connection(connection_id)

        self.assertEqual(204, status)
        self.assertIsNone(self.storage.get_integration_connection(connection_id))
        # Local tracking is dropped even though the remote delete failed (best-effort,
        # matching release_project_glossaries), so no stale rows survive the connection.
        self.assertEqual([], self.storage.list_provider_glossary_sync_for_connection(connection_id))

    def test_no_remote_call_for_connection_without_synced_glossaries(self):
        connection_id = self.connection["connectionId"]

        with patch.object(self.provider, "delete_glossary") as delete_mock:
            status, _ = self._delete_connection(connection_id)

        self.assertEqual(204, status)
        delete_mock.assert_not_called()
        self.assertIsNone(self.storage.get_integration_connection(connection_id))

    def test_reconnecting_after_delete_does_not_leave_old_remote_glossary_orphaned(self):
        """Regression test for the original bug: deleting and recreating a DeepL connection
        (e.g. to rotate the API key) used to leak the old connection's remote glossary
        forever, since nothing released it and there was no FK cascade to notice it."""
        saved = self._create_synced_glossary()
        old_remote_glossary_id = saved["providerSync"]["remoteGlossaryId"]
        old_connection_id = self.connection["connectionId"]

        status, _ = self._delete_connection(old_connection_id)
        self.assertEqual(204, status)
        self.assertEqual([old_remote_glossary_id], self.provider.deleted)

        new_connection = self.storage.create_integration_connection(
            "deepl", "DeepL", self.vault.encrypt({"apiKey": "rotated-key"})
        )
        self.storage.update_integration_connection_status(
            new_connection["connectionId"], "connected", "ok", "ok", {}
        )
        resynced = self._create_synced_glossary()

        # The only remote deletion so far is the one triggered by releasing the old
        # connection; before the fix, nothing ever called delete_glossary for it and
        # it would remain on the provider account indefinitely.
        self.assertEqual([old_remote_glossary_id], self.provider.deleted)
        self.assertEqual(2, len(self.provider.created))
        self.assertNotEqual(old_remote_glossary_id, resynced["providerSync"]["remoteGlossaryId"])


if __name__ == "__main__":
    unittest.main()
