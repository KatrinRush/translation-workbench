import sqlite3
import tempfile
import unittest
from pathlib import Path

from backend.storage import Storage


class IntegrationStorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "workbench.sqlite3"
        self.storage = Storage(self.database_path)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_connection_metadata_never_exposes_ciphertext(self):
        created = self.storage.create_integration_connection("deepl", "DeepL", b"encrypted-value")

        self.assertNotIn("credentialsCiphertext", created)
        self.assertNotIn("credentialsCiphertext", self.storage.list_integration_connections()[0])
        self.assertEqual(
            b"encrypted-value",
            self.storage.get_integration_connection_record(created["connectionId"])["credentialsCiphertext"],
        )

    def test_plaintext_secret_is_not_stored(self):
        self.storage.create_integration_connection("deepl", "DeepL", b"ciphertext-without-secret")

        with sqlite3.connect(self.database_path) as connection:
            database_bytes = b"".join(
                bytes(row[0]) for row in connection.execute("SELECT credentials_ciphertext FROM integration_connections")
            )

        self.assertNotIn(b"api-key-secret", database_bytes)

    def test_updates_status_and_deletes_without_credentials(self):
        created = self.storage.create_integration_connection("deepl", "DeepL", b"ciphertext")
        connection_id = created["connectionId"]

        status = self.storage.update_integration_connection_status(
            connection_id,
            "connected",
            "ok",
            "Connection successful.",
            {"characterCount": 10},
        )

        self.assertEqual("connected", status["testStatus"])
        self.assertEqual({"characterCount": 10}, status["providerMetadata"])
        self.assertTrue(self.storage.delete_integration_connection(connection_id))
        self.assertIsNone(self.storage.get_integration_connection(connection_id))


if __name__ == "__main__":
    unittest.main()