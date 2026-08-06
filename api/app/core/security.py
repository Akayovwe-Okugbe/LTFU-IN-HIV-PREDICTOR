from datetime import UTC, datetime, timedelta
from uuid import UUID
import secrets
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from .config import get_settings

_hasher = PasswordHasher()

def hash_password(password: str) -> str:
    settings = get_settings()
    if len(password) < settings.password_min_length:
        raise ValueError(f'Password must contain at least {settings.password_min_length} characters.')
    return _hasher.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False

def create_access_token(subject: UUID | str, role: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        'sub': str(subject), 'role': role, 'type': 'access',
        'iat': now,
        'exp': now + timedelta(minutes=settings.access_token_expire_minutes),
        'jti': secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

def decode_access_token(token: str) -> dict:
    settings = get_settings()
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get('type') != 'access':
        raise jwt.InvalidTokenError('Unexpected token type.')
    return payload
