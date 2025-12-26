"""
Encryption Utilities for Trendyol Profitability SaaS

Provides secure encryption/decryption for sensitive data like API credentials.
Uses Fernet symmetric encryption (AES-128-CBC with HMAC).
"""

import base64
import hashlib
from typing import Optional

from django.conf import settings
from cryptography.fernet import Fernet, InvalidToken

from .exceptions import EncryptionError


class CredentialEncryptor:
    """
    Encrypts and decrypts sensitive credentials using Fernet.
    
    Fernet guarantees that a message encrypted using it cannot be 
    manipulated or read without the key.
    """
    
    def __init__(self, key: Optional[str] = None):
        """
        Initialize encryptor with a key.
        
        Args:
            key: Base64-encoded 32-byte encryption key.
                 If not provided, uses ENCRYPTION_KEY from settings.
        """
        self.key = key or settings.ENCRYPTION_KEY
        
        if not self.key:
            raise EncryptionError(
                "Şifreleme anahtarı yapılandırılmamış. "
                "ENCRYPTION_KEY ortam değişkenini ayarlayın."
            )
        
        try:
            # Ensure key is properly formatted for Fernet
            self._fernet = self._get_fernet_instance()
        except Exception as e:
            raise EncryptionError(f"Geçersiz şifreleme anahtarı: {str(e)}")
    
    def _get_fernet_instance(self) -> Fernet:
        """Create a Fernet instance from the key."""
        # If key is not a valid Fernet key, derive one
        try:
            return Fernet(self.key.encode() if isinstance(self.key, str) else self.key)
        except (ValueError, InvalidToken):
            # Key is not a valid Fernet key, derive one using SHA256
            key_bytes = self.key.encode() if isinstance(self.key, str) else self.key
            derived_key = base64.urlsafe_b64encode(
                hashlib.sha256(key_bytes).digest()
            )
            return Fernet(derived_key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.
        
        Args:
            plaintext: The string to encrypt.
            
        Returns:
            Base64-encoded encrypted string.
        """
        if not plaintext:
            return ''
        
        try:
            encrypted = self._fernet.encrypt(plaintext.encode('utf-8'))
            return encrypted.decode('utf-8')
        except Exception as e:
            raise EncryptionError(f"Şifreleme hatası: {str(e)}")
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string.
        
        Args:
            ciphertext: Base64-encoded encrypted string.
            
        Returns:
            Decrypted plaintext string.
        """
        if not ciphertext:
            return ''
        
        try:
            decrypted = self._fernet.decrypt(ciphertext.encode('utf-8'))
            return decrypted.decode('utf-8')
        except InvalidToken:
            raise EncryptionError(
                "Şifre çözme başarısız. Veri bozulmuş veya anahtar yanlış."
            )
        except Exception as e:
            raise EncryptionError(f"Şifre çözme hatası: {str(e)}")


# Singleton instance for easy access
_encryptor: Optional[CredentialEncryptor] = None


def get_encryptor() -> CredentialEncryptor:
    """Get the singleton encryptor instance."""
    global _encryptor
    if _encryptor is None:
        _encryptor = CredentialEncryptor()
    return _encryptor


def encrypt_credential(plaintext: str) -> str:
    """Convenience function to encrypt a credential."""
    return get_encryptor().encrypt(plaintext)


def decrypt_credential(ciphertext: str) -> str:
    """Convenience function to decrypt a credential."""
    return get_encryptor().decrypt(ciphertext)
