"""
Data Encryption & Privacy Module

Provides AES-256 encryption for PII fields, data anonymization for analytics,
and utilities for FERPA, COPPA, and GDPR compliance.

Task: 14.6 - Data Encryption & Privacy Measures
"""

import base64
import hashlib
import secrets
import re
from typing import Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from ..config import settings


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive PII data.
    Uses AES-256 encryption via Fernet (symmetric encryption).
    """

    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Initialize encryption service with a key.

        Args:
            encryption_key: Base64-encoded Fernet key. If None, derives from settings.
        """
        if encryption_key is None:
            encryption_key = self._derive_key_from_secret(settings.secret_key)

        self.fernet = Fernet(encryption_key)

    @staticmethod
    def _derive_key_from_secret(secret: str) -> bytes:
        """
        Derive a Fernet key from the application secret key using PBKDF2.

        Args:
            secret: Application secret key

        Returns:
            Base64-encoded Fernet key (32 bytes)
        """
        # Use a fixed salt for deterministic key derivation
        # In production, consider using a unique salt stored securely
        salt = b'tutormax_encryption_salt_v1'  # IMPORTANT: Change in production

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,  # OWASP recommended minimum for 2023
            backend=default_backend()
        )

        # Derive 32 bytes and encode as URL-safe base64 for Fernet
        key = kdf.derive(secret.encode())
        return base64.urlsafe_b64encode(key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string using AES-256.

        Args:
            plaintext: Data to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return plaintext

        encrypted = self.fernet.encrypt(plaintext.encode())
        return encrypted.decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an AES-256 encrypted string.

        Args:
            ciphertext: Encrypted data (base64-encoded)

        Returns:
            Decrypted plaintext string
        """
        if not ciphertext:
            return ciphertext

        try:
            decrypted = self.fernet.decrypt(ciphertext.encode())
            return decrypted.decode()
        except Exception:
            # If decryption fails, return as-is (might not be encrypted)
            return ciphertext

    def encrypt_email(self, email: str) -> str:
        """Encrypt email address for storage."""
        return self.encrypt(email)

    def decrypt_email(self, encrypted_email: str) -> str:
        """Decrypt email address."""
        return self.decrypt(encrypted_email)

    def encrypt_phone(self, phone: str) -> str:
        """Encrypt phone number for storage."""
        return self.encrypt(phone)

    def decrypt_phone(self, encrypted_phone: str) -> str:
        """Decrypt phone number."""
        return self.decrypt(encrypted_phone)


class AnonymizationService:
    """
    Service for anonymizing and pseudonymizing data for analytics.
    Ensures compliance with FERPA, COPPA, and GDPR requirements.
    """

    @staticmethod
    def pseudonymize_id(user_id: Union[int, str], salt: str = "tutormax_pseudo") -> str:
        """
        Create a pseudonymous ID for analytics while maintaining uniqueness.

        Args:
            user_id: Original user ID
            salt: Salt for hashing (should be kept secret)

        Returns:
            Pseudonymous hash that can be used for analytics
        """
        data = f"{user_id}:{salt}".encode()
        return hashlib.sha256(data).hexdigest()[:16]  # Use first 16 chars

    @staticmethod
    def anonymize_email(email: str) -> str:
        """
        Anonymize email for display (e.g., user****@example.com).

        Args:
            email: Email address to anonymize

        Returns:
            Partially masked email
        """
        if not email or '@' not in email:
            return "***@***.***"

        local, domain = email.split('@', 1)

        if len(local) <= 4:
            masked_local = local[0] + "***"
        else:
            masked_local = local[:2] + "****" + local[-2:]

        # Mask domain except TLD
        domain_parts = domain.split('.')
        if len(domain_parts) > 1:
            masked_domain = "***." + domain_parts[-1]
        else:
            masked_domain = "***"

        return f"{masked_local}@{masked_domain}"

    @staticmethod
    def anonymize_phone(phone: str) -> str:
        """
        Anonymize phone number for display (e.g., ***-***-1234).

        Args:
            phone: Phone number to anonymize

        Returns:
            Partially masked phone number
        """
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)

        if len(digits) < 4:
            return "***-***-****"

        # Show last 4 digits only
        return f"***-***-{digits[-4:]}"

    @staticmethod
    def anonymize_name(full_name: str) -> str:
        """
        Anonymize name for display (e.g., J*** D***).

        Args:
            full_name: Full name to anonymize

        Returns:
            Anonymized name with first letters only
        """
        if not full_name:
            return "***"

        parts = full_name.split()
        anonymized = []

        for part in parts:
            if len(part) > 0:
                anonymized.append(part[0] + "***")

        return " ".join(anonymized) if anonymized else "***"

    @staticmethod
    def hash_for_analytics(value: str, salt: Optional[str] = None) -> str:
        """
        Create a one-way hash suitable for analytics aggregation.
        Cannot be reversed but allows grouping.

        Args:
            value: Value to hash
            salt: Optional salt (defaults to settings secret)

        Returns:
            SHA-256 hash
        """
        if salt is None:
            salt = settings.secret_key

        data = f"{value}:{salt}".encode()
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def is_coppa_protected(age: Optional[int]) -> bool:
        """
        Determine if user is protected under COPPA (under 13 years old).

        Args:
            age: User's age

        Returns:
            True if user is under 13 (COPPA protected)
        """
        return age is not None and age < 13

    @staticmethod
    def mask_ssn(ssn: str) -> str:
        """
        Mask SSN for display (e.g., ***-**-1234).

        Args:
            ssn: Social Security Number

        Returns:
            Masked SSN
        """
        digits = re.sub(r'\D', '', ssn)

        if len(digits) != 9:
            return "***-**-****"

        return f"***-**-{digits[-4:]}"


class DataPrivacyHelper:
    """
    Helper class for managing PII fields and privacy compliance.
    """

    # Define which fields contain PII and should be encrypted/anonymized
    PII_FIELDS = {
        'email',
        'phone',
        'phone_number',
        'address',
        'street_address',
        'ssn',
        'social_security_number',
        'date_of_birth',
        'dob',
        'birth_date',
        'ip_address',
        'device_id',
    }

    # Fields that require anonymization for under-13 users (COPPA)
    COPPA_RESTRICTED_FIELDS = {
        'full_name',
        'email',
        'phone',
        'address',
        'photo_url',
        'profile_picture',
    }

    @classmethod
    def is_pii_field(cls, field_name: str) -> bool:
        """Check if a field name indicates PII data."""
        return field_name.lower() in cls.PII_FIELDS

    @classmethod
    def is_coppa_restricted(cls, field_name: str) -> bool:
        """Check if a field is restricted for COPPA-protected users."""
        return field_name.lower() in cls.COPPA_RESTRICTED_FIELDS

    @staticmethod
    def generate_encryption_key() -> bytes:
        """
        Generate a new Fernet encryption key.

        Returns:
            Base64-encoded encryption key

        Note:
            This should be stored securely (e.g., AWS Secrets Manager, environment variable)
        """
        return Fernet.generate_key()

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """
        Generate a cryptographically secure random token.

        Args:
            length: Length of token in bytes

        Returns:
            Hex-encoded secure token
        """
        return secrets.token_hex(length)


# Global service instances
encryption_service = EncryptionService()
anonymization_service = AnonymizationService()
privacy_helper = DataPrivacyHelper()
