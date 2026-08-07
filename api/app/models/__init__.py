"""
=========================================================
MEDISCOPE Database Models Package

Purpose:
    Import and expose all SQLAlchemy entity classes.

    Importing this package registers every mapped table
    in Base.metadata so that Alembic can discover and
    compare the MEDISCOPE schema.

Author:
    Akayovwe Okugbe

=========================================================
"""

from .entities import (
    AuditLog,
    ClinicalRecord,
    ClinicianPatientAssignment,
    EmailVerificationToken,
    HealthRecordChangeRequest,
    Message,
    MessageRecipient,
    ModelRegistry,
    PasswordResetToken,
    Patient,
    Prediction,
    User,
)


from .authentication import (
    MfaRecoveryCode,
    PendingTotpEnrollment,
    RefreshTokenSession,
)


__all__ = [
    "AuditLog",
    "ClinicalRecord",
    "ClinicianPatientAssignment",
    "EmailVerificationToken",
    "HealthRecordChangeRequest",
    "Message",
    "MessageRecipient",
    "ModelRegistry",
    "PasswordResetToken",
    "Patient",
    "Prediction",
    "User",
    "MfaRecoveryCode",
    "PendingTotpEnrollment",
    "RefreshTokenSession",
]
