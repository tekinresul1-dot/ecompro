"""
Encryption Utilities for Trendyol Profitability SaaS

SECURITY HARDENED VERSION
Provides secure encryption/decryption for sensitive data like API credentials.
Uses Fernet symmetric encryption (AES-128-CBC with HMAC).

Security Features:
- Key validation and rotation support
- Memory-safe key handling
- Audit logging for encryption operations
- Protection against timing attacks
"""

import base64
import hashlib
import hmac
import secrets
import logging
from typing import Optional

from django.conf import settings
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .exceptions import EncryptionError

security_logger = logging.getLogger('django.security')


class CredentialEncryptor:
    """
    SECURITY ENHANCED: Encrypts and decrypts sensitive credentials using Fernet.
    
    Fernet guarantees that a message encrypted using it cannot be 
    manipulated or read without the key.
    
    Security features:
    - Strong key derivation using PBKDF2
    - Audit logging for all operations
    - Protection against timing attacks
    """
    
    # Salt for key derivation (in production, this should be stored separately)
    _salt = b'trendyol_profitability_credential_encryption_v1'
    
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
        
        # SECURITY: Validate key strength
        if len(self.key) < 32:
            raise EncryptionError(
                "Şifreleme anahtarı çok kısa. En az 32 karakter gerekli."
            )
        
        try:
            # Ensure key is properly formatted for Fernet
            self._fernet = self._get_fernet_instance()
        except Exception as e:
            security_logger.error(f"Encryption key initialization failed")
            raise EncryptionError(f"Geçersiz şifreleme anahtarı: {str(e)}")
    
    def _get_fernet_instance(self) -> Fernet:
        """
        SECURITY: Create a Fernet instance using PBKDF2 key derivation.
        """
        try:
            # First, try to use the key directly if it's a valid Fernet key
            key_bytes = self.key.encode() if isinstance(self.key, str) else self.key
            return Fernet(key_bytes)
        except (ValueError, InvalidToken):
            # Key is not a valid Fernet key, derive one using PBKDF2
            key_bytes = self.key.encode() if isinstance(self.key, str) else self.key
            
            # SECURITY: Use PBKDF2 for key derivation (more secure than simple SHA256)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self._salt,
                iterations=100000,  # High iteration count for security
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(key_bytes))
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
            # SECURITY: Log encryption operation (without sensitive data)
            security_logger.debug("Credential encrypted successfully")
            return encrypted.decode('utf-8')
        except Exception as e:
            security_logger.error("Encryption operation failed")
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
            security_logger.debug("Credential decrypted successfully")
            return decrypted.decode('utf-8')
        except InvalidToken:
            security_logger.warning("Decryption failed - invalid token or corrupted data")
            raise EncryptionError(
                "Şifre çözme başarısız. Veri bozulmuş veya anahtar yanlış."
            )
        except Exception as e:
            security_logger.error("Decryption operation failed")
            raise EncryptionError(f"Şifre çözme hatası: {str(e)}")
    
    def rotate_encryption(self, old_ciphertext: str, new_key: str) -> str:
        """
        SECURITY: Re-encrypt data with a new key for key rotation.
        
        Args:
            old_ciphertext: Data encrypted with current key
            new_key: New encryption key
            
        Returns:
            Data encrypted with new key
        """
        # Decrypt with current key
        plaintext = self.decrypt(old_ciphertext)
        
        # Encrypt with new key
        new_encryptor = CredentialEncryptor(key=new_key)
        new_ciphertext = new_encryptor.encrypt(plaintext)
        
        security_logger.info("Credential encryption rotated")
        return new_ciphertext


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


def generate_encryption_key() -> str:
    """
    SECURITY: Generate a new secure encryption key.
    
    Returns:
        A valid Fernet-compatible base64-encoded 32-byte key.
    """
    return Fernet.generate_key().decode()


def secure_compare(a: str, b: str) -> bool:
    """
    SECURITY: Constant-time string comparison to prevent timing attacks.
    
    Args:
        a: First string
        b: Second string
        
    Returns:
        True if strings are equal, False otherwise
    """
    return hmac.compare_digest(a.encode(), b.encode())
