from uuid import uuid4
import pytest
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password

def test_password_hash_and_verify():
    password = 'A-strong-demonstration-password!'
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password('wrong-password', hashed)

def test_access_token_round_trip():
    user_id = uuid4()
    token = create_access_token(
        subject=user_id,
        role="CLINICIAN",
        mfa_verified=True,
    )
    payload = decode_access_token(
        token
    )
    assert payload["sub"] == str(user_id)
    assert payload["role"] == "CLINICIAN"
    assert payload["type"] == "access"
    assert payload["mfa_verified"] is True

def test_short_password_rejected():
    with pytest.raises(ValueError):
        hash_password('too-short')
