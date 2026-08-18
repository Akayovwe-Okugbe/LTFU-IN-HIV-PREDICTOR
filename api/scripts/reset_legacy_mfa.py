"""
=========================================================
MEDISCOPE Legacy MFA Reset

Purpose:
    One-time development utility used after introducing
    encryption-at-rest for TOTP authenticator secrets.

    MFA enrolments created before this hardening change
    stored Base32 TOTP secrets directly in fields intended
    for encrypted values.

    This script resets those enrolments so users can
    securely re-enrol.

Important:
    This utility is intended for the current synthetic
    demonstration environment.

    Do not use this approach against real production users
    without an explicit credential-migration strategy.

=========================================================
"""

from __future__ import annotations

# =====================================================
# SCRIPT IMPORT PATH
#
# When this utility is executed directly using:
#
#     python scripts/reset_legacy_mfa.py
#
# Python places api/scripts on sys.path rather than the
# api directory itself. Add the API root explicitly so
# the normal `app.*` package imports remain available.
# =====================================================

import sys

from pathlib import Path


API_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(API_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(API_ROOT),
    )

# =====================================================
# SQLALCHEMY IMPORTS
# =====================================================

from sqlalchemy import (
    delete,
    select,
)


# =====================================================
# APPLICATION IMPORTS
# =====================================================

from app.db.session import (
    SessionLocal,
)

from app.models.authentication import (
    MfaRecoveryCode,
    PendingTotpEnrollment,
)

from app.models.entities import (
    User,
)


# =====================================================
# RESET
# =====================================================

def reset_legacy_mfa() -> None:
    """
    Remove pre-encryption MFA state and require users to
    enrol their authenticator again.
    """

    db = SessionLocal()

    try:
        users = list(
            db.scalars(
                select(
                    User
                ).where(
                    User
                    .mfa_enabled
                    .is_(True)
                )
            ).all()
        )

        affected_users = (
            len(users)
        )


        for user in users:
            user.mfa_enabled = False

            user.mfa_secret_encrypted = (
                None
            )


        # Recovery codes belong to the previous MFA
        # enrolments and must not survive the reset.
        db.execute(
            delete(
                MfaRecoveryCode
            )
        )


        # Pending setup values created under the legacy
        # plaintext behaviour are also invalid.
        db.execute(
            delete(
                PendingTotpEnrollment
            )
        )


        db.commit()

        print(
            "MEDISCOPE legacy MFA reset complete."
        )

        print(
            f"Accounts requiring re-enrolment: "
            f"{affected_users}"
        )

    except Exception:
        db.rollback()

        raise

    finally:
        db.close()


# =====================================================
# SCRIPT ENTRY POINT
# =====================================================

if __name__ == "__main__":
    reset_legacy_mfa()
