"""
SQLAlchemy Custom Types for Encrypted Fields

Provides transparent encryption/decryption for database columns containing PII.
Data is encrypted before storage and decrypted on retrieval using AES-256.

Task: 14.6 - Data Encryption & Privacy Measures
"""

from typing import Optional
from sqlalchemy import TypeDecorator, String, Text
from sqlalchemy.engine import Dialect

from src.api.security.encryption import encryption_service


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy type for encrypted string fields.

    Transparently encrypts data before INSERT/UPDATE and decrypts on SELECT.
    Uses AES-256 encryption via Fernet.

    Usage:
        class User(Base):
            __tablename__ = "users"

            id = Column(Integer, primary_key=True)
            email = Column(EncryptedString(255), nullable=False)  # Encrypted!
            phone = Column(EncryptedString(50))  # Encrypted!
            name = Column(String(100))  # Not encrypted

    Example:
        # Writing to database (automatic encryption)
        user = User(email="student@example.com", phone="555-1234")
        session.add(user)
        session.commit()

        # Reading from database (automatic decryption)
        user = session.query(User).first()
        print(user.email)  # Prints: "student@example.com" (decrypted)

    Note:
        - The database stores encrypted base64 strings
        - Encrypted values are longer than plaintext (~1.4x)
        - Use sufficient VARCHAR length (e.g., VARCHAR(500) for 255-char plaintext)
    """

    impl = String
    cache_ok = True

    def __init__(self, length: int = 500, *args, **kwargs):
        """
        Initialize encrypted string type.

        Args:
            length: Maximum length of the VARCHAR column (should be larger than plaintext)
        """
        super().__init__(length, *args, **kwargs)

    def process_bind_param(self, value: Optional[str], dialect: Dialect) -> Optional[str]:
        """
        Encrypt value before storing in database.

        Args:
            value: Plaintext string to encrypt
            dialect: SQLAlchemy dialect

        Returns:
            Encrypted string (base64-encoded) or None
        """
        if value is None:
            return None

        return encryption_service.encrypt(value)

    def process_result_value(self, value: Optional[str], dialect: Dialect) -> Optional[str]:
        """
        Decrypt value after retrieving from database.

        Args:
            value: Encrypted string from database
            dialect: SQLAlchemy dialect

        Returns:
            Decrypted plaintext string or None
        """
        if value is None:
            return None

        return encryption_service.decrypt(value)


class EncryptedText(TypeDecorator):
    """
    SQLAlchemy type for encrypted TEXT fields.

    Same as EncryptedString but for larger text content.

    Usage:
        class MedicalRecord(Base):
            __tablename__ = "medical_records"

            id = Column(Integer, primary_key=True)
            notes = Column(EncryptedText())  # Encrypted large text
            diagnosis = Column(EncryptedText())  # Encrypted
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Optional[str], dialect: Dialect) -> Optional[str]:
        """Encrypt value before storing."""
        if value is None:
            return None

        return encryption_service.encrypt(value)

    def process_result_value(self, value: Optional[str], dialect: Dialect) -> Optional[str]:
        """Decrypt value after retrieving."""
        if value is None:
            return None

        return encryption_service.decrypt(value)


# Convenience type aliases for common PII fields
EncryptedEmail = EncryptedString  # For email addresses
EncryptedPhone = EncryptedString  # For phone numbers
EncryptedAddress = EncryptedText  # For postal addresses
EncryptedSSN = EncryptedString  # For social security numbers


# Example usage and migration guide
"""
## Migration Guide: Adding Encryption to Existing Columns

### Step 1: Create migration to change column type
```python
# alembic/versions/xxx_encrypt_user_fields.py

def upgrade():
    # Note: This is a non-reversible migration for existing data!
    # Consider backing up data first.

    # Option A: For new deployments (empty tables)
    op.alter_column('users', 'email',
                    type_=sa.String(500),  # Increase size for encrypted data
                    existing_type=sa.String(255))

    # Option B: For existing data (requires manual migration)
    # 1. Add new encrypted column
    op.add_column('users', sa.Column('email_encrypted', sa.String(500)))

    # 2. Migrate data using Python script
    # (See encrypt_existing_data.py example below)

    # 3. Drop old column and rename new one
    op.drop_column('users', 'email')
    op.alter_column('users', 'email_encrypted', new_column_name='email')


def downgrade():
    # Decryption would require the same encryption key!
    # Consider this irreversible in production.
    pass
```

### Step 2: Data migration script
```python
# scripts/encrypt_existing_data.py

from sqlalchemy import create_engine, text
from src.api.security.encryption import encryption_service

engine = create_engine('postgresql://...')

with engine.connect() as conn:
    # Get all users
    result = conn.execute(text("SELECT id, email FROM users"))

    for row in result:
        user_id, email = row
        if email:
            encrypted_email = encryption_service.encrypt(email)
            conn.execute(
                text("UPDATE users SET email_encrypted = :enc WHERE id = :id"),
                {"enc": encrypted_email, "id": user_id}
            )

    conn.commit()
```

### Step 3: Update models
```python
# Before:
class User(Base):
    __tablename__ = "users"
    email = Column(String(255), nullable=False)

# After:
class User(Base):
    __tablename__ = "users"
    email = Column(EncryptedString(500), nullable=False)  # Now encrypted!
```

## Best Practices

1. **Column Length**: Encrypted data is ~1.4x longer. Use 2x length to be safe.
   - VARCHAR(255) → VARCHAR(500) for encrypted fields

2. **Indexing**: Cannot index encrypted fields for searching
   - Create separate hash columns for searching if needed
   - Use `anonymization_service.hash_for_analytics()` for search indexes

3. **Performance**: Encryption adds ~0.1ms per field
   - Minimize encrypted fields to only PII
   - Consider caching decrypted values in application layer

4. **Key Rotation**: Plan for encryption key rotation
   - Store key version with data
   - Implement re-encryption strategy

5. **Backup & Recovery**: Encrypted backups require the encryption key
   - Store encryption keys separately (e.g., AWS Secrets Manager)
   - Test recovery procedures regularly
"""
