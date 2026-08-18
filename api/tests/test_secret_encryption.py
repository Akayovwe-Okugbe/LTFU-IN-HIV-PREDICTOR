"""
Tests for MEDISCOPE recoverable TOTP secret encryption.
"""

import pytest

from app.core.secret_encryption import (
    SecretEncryptionError,
    decrypt_totp_secret,
    encrypt_totp_secret,
)


# =====================================================
# ENCRYPT / DECRYPT ROUND TRIP
# =====================================================

def test_totp_secret_round_trip():
    """
    A TOTP secret should survive a full encryption and
    decryption round trip without being stored as plaintext.
    """

    secret = (
        "JBSWY3DPEHPK3PXP"
    )

    ciphertext = (
        encrypt_totp_secret(
            secret
        )
    )

    assert ciphertext != secret

    assert (
        decrypt_totp_secret(
            ciphertext
        )
        == secret
    )


# =====================================================
# PLAINTEXT MUST NOT BE ACCEPTED AS CIPHERTEXT
# =====================================================

def test_plaintext_totp_secret_is_rejected():
    """
    Legacy/plaintext TOTP secrets must not be silently
    accepted by the encrypted-secret workflow.
    """

    with pytest.raises(
        SecretEncryptionError
    ):
        decrypt_totp_secret(
            "JBSWY3DPEHPK3PXP"
        )


# =====================================================
# TAMPERED CIPHERTEXT MUST FAIL CLOSED
# =====================================================

def test_tampered_ciphertext_is_rejected():
    """
    Modified Fernet ciphertext must fail authentication
    rather than returning a secret.
    """

    ciphertext = (
        encrypt_totp_secret(
            "JBSWY3DPEHPK3PXP"
        )
    )

    tampered = (
        ciphertext[:-1]
        +
        (
            "A"
            if ciphertext[-1]
            != "A"
            else "B"
        )
    )

    with pytest.raises(
        SecretEncryptionError
    ):
        decrypt_totp_secret(
            tampered
        )
