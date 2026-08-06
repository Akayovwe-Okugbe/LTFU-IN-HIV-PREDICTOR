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
    payload = decode_access_token(create_access_token(user_id, 'CLINICIAN'))
    assert payload['sub'] == str(user_id)
    assert payload['role'] == 'CLINICIAN'

def test_short_password_rejected():
    with pytest.raises(ValueError):
        hash_password('too-short')
