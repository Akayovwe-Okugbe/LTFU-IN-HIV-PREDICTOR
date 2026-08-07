"""Unit tests for Phase 2 authentication security helpers."""
from uuid import uuid4

import pyotp

from app.core.auth_security import (
    build_totp_provisioning_uri,
    create_mfa_challenge_token,
    decode_mfa_challenge_token,
    generate_numeric_otp,
    generate_recovery_codes,
    generate_totp_secret,
    hash_secret,
    verify_totp_code,
)


def test_numeric_otp_is_six_digits():
    otp = generate_numeric_otp()
    assert len(otp) == 6
    assert otp.isdigit()


def test_secret_hash_is_not_plaintext():
    value = "high-entropy-test-token"
    hashed = hash_secret(value)
    assert hashed != value
    assert len(hashed) == 64


def test_mfa_challenge_round_trip():
    user_id = uuid4()
    token = create_mfa_challenge_token(subject=user_id, role="CLINICIAN")
    claims = decode_mfa_challenge_token(token)
    assert claims["sub"] == str(user_id)
    assert claims["type"] == "mfa_challenge"


def test_totp_code_verification():
    secret = generate_totp_secret()
    code = pyotp.TOTP(secret).now()
    assert verify_totp_code(secret=secret, code=code)


def test_provisioning_uri_contains_issuer():
    uri = build_totp_provisioning_uri(
        email="clinician@example.test",
        secret=generate_totp_secret(),
    )
    assert uri.startswith("otpauth://totp/")
    assert "MEDISCOPE" in uri


def test_recovery_codes_are_unique():
    codes = generate_recovery_codes(10)
    assert len(codes) == 10
    assert len(set(codes)) == 10
