# core/encryption.py
from cryptography.fernet import Fernet
from pathlib import Path


class CredentialEncryption:
    """Handles encryption and decryption of sensitive credentials using Fernet symmetric encryption"""

    def __init__(self, key_file: Path = Path(".secret.key")):
        """
        Initialize encryption with key file.

        Args:
            key_file: Path to encryption key file (default: .secret.key)
        """
        self.key_file = key_file
        self.cipher = self._load_or_create_key()

    def _load_or_create_key(self) -> Fernet:
        """
        Load existing encryption key or create new one.

        Returns:
            Fernet cipher instance

        Note:
            If key is created, user should back it up immediately
        """
        if self.key_file.exists():
            key = self.key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            print(f"⚠️  Encryption key created: {self.key_file}")
            print(f"⚠️  IMPORTANT: Back up this key file! Without it, encrypted passwords cannot be recovered.")
        return Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""
        return self.cipher.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext string.

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string
        """
        if not ciphertext:
            return ""
        return self.cipher.decrypt(ciphertext.encode()).decode()
