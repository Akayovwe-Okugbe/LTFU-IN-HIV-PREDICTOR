from typing import Annotated
from uuid import UUID
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.enums import AccountStatus
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.entities import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login')
DbSession = Annotated[Session, Depends(get_db)]

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DbSession) -> User:
    error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                          detail='Authentication credentials could not be validated.',
                          headers={'WWW-Authenticate': 'Bearer'})
    try:
        payload = decode_access_token(token)
        user_id = UUID(str(payload['sub']))
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise error
    user = db.get(User, user_id)
    if user is None:
        raise error
    if user.account_status != AccountStatus.ACTIVE.value:
        raise HTTPException(status_code=403, detail='This account is not active.')
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

def require_roles(*roles: str):
    def dependency(current_user: CurrentUser) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail='You do not have permission to perform this action.')
        return current_user
    return dependency
