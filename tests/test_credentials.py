import os
import unittest
from unittest.mock import patch

from cryptography.fernet import Fernet

from backend.integrations.credentials import CredentialVault, CredentialVaultError


class CredentialVaultTests(unittest.TestCase):
    def test_missing_key_leaves_vault_unavailable(self):
        with patch.dict(os.environ, {}, clear=True):
            vault = CredentialVault.from_environment()

        self.assertFalse(vault.available)
        with self.assertRaises(CredentialVaultError):
            vault.encrypt({"apiKey": "secret"})

    def test_invalid_key_leaves_vault_unavailable(self):
        with patch.dict(os.environ, {"WORKBENCH_CREDENTIALS_KEY": "invalid"}, clear=True):
            vault = CredentialVault.from_environment()

        self.assertFalse(vault.available)

    def test_credentials_round_trip_without_plaintext_ciphertext(self):
        key = Fernet.generate_key().decode("ascii")
        with patch.dict(os.environ, {"WORKBENCH_CREDENTIALS_KEY": key}, clear=True):
            vault = CredentialVault.from_environment()

        ciphertext = vault.encrypt({"apiKey": "deepl-secret"})

        self.assertTrue(vault.available)
        self.assertNotIn(b"deepl-secret", ciphertext)
        self.assertEqual({"apiKey": "deepl-secret"}, vault.decrypt(ciphertext))

    def test_wrong_key_cannot_decrypt_credentials(self):
        first = CredentialVault(Fernet(Fernet.generate_key()))
        second = CredentialVault(Fernet(Fernet.generate_key()))

        with self.assertRaises(CredentialVaultError):
            second.decrypt(first.encrypt({"apiKey": "secret"}))


if __name__ == "__main__":
    unittest.main()
