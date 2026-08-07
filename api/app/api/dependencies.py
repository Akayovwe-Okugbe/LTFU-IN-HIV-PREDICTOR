"""
=========================================================
MEDISCOPE API Dependencies

LTFU Prediction Platform

Purpose:
    Provide reusable FastAPI dependencies shared across
    the MEDISCOPE backend.

Responsibilities:
    - Database session management
    - JWT Bearer authentication
    - Current authenticated user resolution
    - Role-based authorisation

Security:
    MEDISCOPE authenticates users using JWT bearer tokens
    issued after successful login.

    Swagger therefore uses the HTTP Bearer security scheme
    instead of the generic OAuth2 password-flow interface.

Author:
    Akayovwe Okugbe
=========================================================
"""

from __future__ import annotations

# =====================================================
# STANDARD LIBRARY IMPORTS
# =====================================================

from typing import Annotated
from uuid import UUID

# =====================================================
# THIRD-PARTY IMPORTS
# =====================================================

import jwt

from fastapi import (
    Depends,
    HTTPException,
    status,
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from sqlalchemy.orm import Session

# =====================================================
# APPLICATION IMPORTS
# =====================================================

from app.core.enums import AccountStatus

from app.core.security import decode_access_token

from app.db.session import get_db

from app.models.entities import User


# =====================================================
# DATABASE SESSION DEPENDENCY
# =====================================================

DbSession = Annotated[
    Session,
    Depends(get_db),
]


# =====================================================
# HTTP BEARER AUTHENTICATION SCHEME
#
# Swagger now displays a simple Bearer token input rather
# than the OAuth2 username/password credentials form.
# =====================================================

bearer_scheme = HTTPBearer(
    scheme_name="MEDISCOPE Bearer Authentication",
    description=(
        "Paste a JWT access token returned by "
        "/api/v1/auth/login or "
        "/api/v1/auth/mfa/totp/login."
    ),
    auto_error=True,
)


# =====================================================
# CURRENT AUTHENTICATED USER
# =====================================================

def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer_scheme),
    ],
    db: DbSession,
) -> User:
    """
    Resolve the currently authenticated user from the
    supplied JWT bearer token.

    The function verifies:

    - JWT validity
    - User existence
    - Active account status
    """

    authentication_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication credentials could not be validated.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Extract the raw JWT from the Authorization header.
        token = credentials.credentials

        # Validate the JWT.
        payload = decode_access_token(token)

        # Convert the JWT subject back into a UUID.
        user_id = UUID(str(payload["sub"]))

    except (
        jwt.InvalidTokenError,
        KeyError,
        ValueError,
    ):
        raise authentication_error

    # Retrieve the authenticated user.
    user = db.get(
        User,
        user_id,
    )

    if user is None:
        raise authentication_error

    # Only active accounts may access protected endpoints.
    if (
        user.account_status
        != AccountStatus.ACTIVE.value
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not active.",
        )

    return user


# =====================================================
# CURRENT USER TYPE ALIAS
# =====================================================

CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]


# =====================================================
# ROLE-BASED AUTHORISATION
# =====================================================

def require_roles(
    *roles: str,
):
    """
    Create a dependency that restricts access to one or
    more MEDISCOPE roles.

    Example
    -------
    @router.get(...)
    def endpoint(
        current_user: Annotated[
            User,
            Depends(
                require_roles(
                    UserRole.ADMIN.value
                )
            )
        ]
    ):
        ...
    """

    def dependency(
        current_user: CurrentUser,
    ) -> User:
        """
        Verify that the authenticated user possesses one
        of the permitted roles.
        """

        if current_user.role not in roles:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You do not have permission to "
                    "perform this action."
                ),
            )

        return current_user

    return dependency
