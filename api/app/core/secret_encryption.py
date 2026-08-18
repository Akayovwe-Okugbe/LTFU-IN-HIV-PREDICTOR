"""
=========================================================
MEDISCOPE Secret Encryption Utilities

Purpose:
    Protect application secrets that must remain
    recoverable by the MEDISCOPE backend.

Current use:
    - TOTP authenticator secrets.

Security model:
    User passwords are NOT handled here. Passwords are
    one-way hashed using Argon2id.

    Random reset tokens, refresh tokens and recovery codes
    are NOT handled here either. Those values are stored
    using cryptographic hashes because MEDISCOPE does not
    need to recover their original plaintext.

    TOTP secrets are different: the server must recover the
    shared secret when verifying authenticator codes.

    MEDISCOPE therefore protects TOTP secrets using Fernet
    authenticated symmetric encryption.

Important:
    TOTP_ENCRYPTION_KEY must:

    - remain confidential;
    - remain separate from the JWT signing SECRET_KEY;
    - remain stable while encrypted MFA credentials exist;
    - never be stored in source control or audit logs.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations


# =====================================================
# STANDARD LIBRARY IMPORTS
# =====================================================

from functools import lru_cache


# =====================================================
# THIRD-PARTY IMPORTS
# =====================================================

from cryptography.fernet import (
    Fernet,
    InvalidToken,
)


# =====================================================
# APPLICATION IMPORTS
# =====================================================

from app.core.config import (
    get_settings,
)


# =====================================================
# DOMAIN ERROR
# =====================================================

class SecretEncryptionError(
    ValueError
):
    """
    Raised when a protected application secret cannot be
    encrypted or decrypted safely.

    The original cryptographic exception is deliberately
    not exposed to callers or API clients.
    """


# =====================================================
# FERNET INSTANCE
# =====================================================

@lru_cache(
    maxsize=1,
)
def _get_fernet() -> Fernet:
    """
    Return the shared Fernet encryption instance.

    The key is loaded from MEDISCOPE configuration and is
    cached so it does not need to be reconstructed for
    every MFA verification request.
    """

    settings = get_settings()

    try:
        return Fernet(
            settings
            .totp_encryption_key
            .encode("utf-8")
        )

    except (
        TypeError,
        ValueError,
    ) as error:
        raise SecretEncryptionError(
            "The configured TOTP encryption key is invalid."
        ) from error


# =====================================================
# TOTP SECRET ENCRYPTION
# =====================================================

def encrypt_totp_secret(
    secret: str,
) -> str:
    """
    Encrypt a plaintext Base32 TOTP secret.

    Parameters
    ----------
    secret:
        Plaintext TOTP secret generated during authenticator
        enrolment.

    Returns
    -------
    str
        URL-safe Fernet ciphertext suitable for database
        persistence.

    Raises
    ------
    SecretEncryptionError
        If the supplied secret is empty or encryption
        cannot be completed.
    """

    if not secret:
        raise SecretEncryptionError(
            "A TOTP secret is required."
        )

    try:
        encrypted = (
            _get_fernet()
            .encrypt(
                secret.encode(
                    "utf-8"
                )
            )
        )

        return encrypted.decode(
            "utf-8"
        )

    except SecretEncryptionError:
        raise

    except Exception as error:
        # Cryptographic implementation details must not
        # escape into route/API error messages.
        raise SecretEncryptionError(
            "Unable to protect the TOTP secret."
        ) from error


# =====================================================
# TOTP SECRET DECRYPTION
# =====================================================

def decrypt_totp_secret(
    encrypted_secret: str,
) -> str:
    """
    Decrypt and authenticate a persisted TOTP secret.

    Fernet verifies ciphertext integrity before returning
    the plaintext. A modified value, an incorrect key or
    legacy plaintext will therefore be rejected.

    Parameters
    ----------
    encrypted_secret:
        Fernet ciphertext stored in PostgreSQL.

    Returns
    -------
    str
        Original Base32 TOTP secret.

    Raises
    ------
    SecretEncryptionError
        If the stored value cannot be authenticated or
        decrypted.
    """

    if not encrypted_secret:
        raise SecretEncryptionError(
            "An encrypted TOTP secret is required."
        )

    try:
        plaintext = (
            _get_fernet()
            .decrypt(
                encrypted_secret.encode(
                    "utf-8"
                )
            )
        )

        secret = plaintext.decode(
            "utf-8"
        )

        if not secret:
            raise SecretEncryptionError(
                "The decrypted TOTP secret is empty."
            )

        return secret

    except SecretEncryptionError:
        raise

    except (
        InvalidToken,
        TypeError,
        ValueError,
        UnicodeDecodeError,
    ) as error:
        raise SecretEncryptionError(
            "Unable to decrypt the protected TOTP secret."
        ) from error
