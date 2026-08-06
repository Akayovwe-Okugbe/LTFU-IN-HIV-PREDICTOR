from datetime import UTC, datetime
from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select
from app.api.dependencies import DbSession
from app.core.enums import AccountStatus, UserRole
from app.core.security import create_access_token, hash_password, verify_password
from app.models.entities import User
from app.schemas.auth import GenericResponse, LoginRequest, RegisterRequest, TokenResponse
from app.services.audit import write_audit_log

router = APIRouter(prefix='/auth', tags=['Authentication'])
_UNIFORM_MESSAGE = ('If this email can be registered or is already associated with an account, '
                    'further instructions will be sent.')

@router.post('/register', response_model=GenericResponse, status_code=status.HTTP_202_ACCEPTED)
def register(payload: RegisterRequest, request: Request, db: DbSession) -> GenericResponse:
    email = str(payload.email).lower()
    existing = db.scalar(select(User).where(User.email == email))
    if existing is None:
        user = User(email=email, password_hash=hash_password(payload.password),
                    first_name=payload.first_name.strip(), last_name=payload.last_name.strip(),
                    phone=payload.phone, gender=payload.gender,
                    role=UserRole.USER.value,
                    account_status=AccountStatus.PENDING_EMAIL_VERIFICATION.value)
        db.add(user); db.flush()
        write_audit_log(db, actor_user_id=user.id, action='ACCOUNT_REGISTERED', outcome='SUCCESS',
                        resource_type='USER', resource_id=user.id,
                        ip_address=request.client.host if request.client else None,
                        user_agent=request.headers.get('user-agent'))
        # Next milestone: hashed OTP creation, email queue, admin and welcome messages.
    else:
        write_audit_log(db, actor_user_id=existing.id, action='DUPLICATE_REGISTRATION_ATTEMPT',
                        outcome='REJECTED', resource_type='USER', resource_id=existing.id,
                        ip_address=request.client.host if request.client else None)
    db.commit()
    return GenericResponse(message=_UNIFORM_MESSAGE)

@router.post('/login', response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: DbSession) -> TokenResponse:
    email = str(payload.email).lower()
    user = db.scalar(select(User).where(User.email == email))
    valid = user is not None and verify_password(payload.password, user.password_hash)
    if not valid:
        write_audit_log(db, actor_user_id=user.id if user else None,
                        action='LOGIN_ATTEMPT', outcome='FAILED',
                        resource_type='USER', resource_id=user.id if user else None,
                        ip_address=request.client.host if request.client else None)
        db.commit()
        raise HTTPException(status_code=401, detail='Invalid email or password.')
    if user.account_status != AccountStatus.ACTIVE.value:
        raise HTTPException(status_code=403, detail='Account verification or activation is required.')
    user.failed_login_count = 0
    user.last_login_at = datetime.now(UTC)
    write_audit_log(db, actor_user_id=user.id, action='LOGIN_ATTEMPT', outcome='SUCCESS',
                    resource_type='USER', resource_id=user.id,
                    ip_address=request.client.host if request.client else None)
    db.commit()
    return TokenResponse(access_token=create_access_token(user.id, user.role))
