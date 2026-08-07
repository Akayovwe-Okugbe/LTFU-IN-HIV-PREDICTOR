"""
=========================================================
MEDISCOPE Database Entities

LTFU Prediction in HIV Treatment Programmes
Rome Business School Capstone Project

File:
    entities.py

Purpose:
    Define the SQLAlchemy database models used by the
    MEDISCOPE web application.

    The models represent:

    - user accounts and authentication records;
    - synthetic patients;
    - clinician-patient assignments;
    - clinical records;
    - health-record amendment requests;
    - deployed machine-learning models;
    - saved LTFU predictions;
    - internal messages;
    - audit and security logs.

Important:
    MEDISCOPE currently stores synthetic demonstration
    patient records only. These records do not represent
    real individuals.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations


# =====================================================
# STANDARD LIBRARY IMPORTS
# =====================================================

from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4


# =====================================================
# SQLALCHEMY IMPORTS
# =====================================================

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)


# =====================================================
# APPLICATION IMPORTS
# =====================================================

from app.core.enums import (
    AccountStatus,
    ChangeRequestStatus,
    UserRole,
)

from app.db.base import Base


# =====================================================
# DATE AND TIME UTILITY
# =====================================================

def utcnow() -> datetime:
    """
    Returns the current timezone-aware UTC datetime.

    UTC is used consistently throughout MEDISCOPE so that
    timestamps remain reliable if the application is later
    deployed across different geographical locations.
    """

    return datetime.now(UTC)


# =====================================================
# REUSABLE MODEL MIXINS
# =====================================================

class IdMixin:
    """
    Adds a universally unique identifier to a model.

    UUIDs are preferred over sequential integer identifiers
    because they are considerably more difficult to guess in
    web application URLs and API requests.
    """

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )


class TimeMixin:
    """
    Adds creation and last-updated timestamps to a model.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )


# =====================================================
# USER ACCOUNT
# =====================================================

class User(
    IdMixin,
    TimeMixin,
    Base,
):
    """
    Represents a MEDISCOPE user account.

    Supported application roles currently include:

    - USER
    - CLINICIAN
    - ADMINISTRATOR

    A standard user may optionally be linked to one
    synthetic patient profile.
    """

    __tablename__ = "users"

    # -------------------------------------------------
    # ACCOUNT IDENTITY
    # -------------------------------------------------

    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
    )

    # Only the Argon2id password hash is stored.
    # Plaintext passwords must never be saved.
    password_hash: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    phone: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    gender: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    profile_picture_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Stores the protected TOTP authenticator secret.
    # A real deployment must encrypt this value using
    # a key stored separately from PostgreSQL.
    mfa_secret_encrypted: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    # -------------------------------------------------
    # ROLE AND ACCOUNT STATUS
    # -------------------------------------------------

    role: Mapped[str] = mapped_column(
        String(40),
        default=UserRole.USER.value,
        index=True,
        nullable=False,
    )

    account_status: Mapped[str] = mapped_column(
        String(60),
        default=(
            AccountStatus
            .PENDING_EMAIL_VERIFICATION
            .value
        ),
        index=True,
        nullable=False,
    )

    email_verified_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # -------------------------------------------------
    # MULTI-FACTOR AUTHENTICATION
    # -------------------------------------------------

    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # This can later store an encrypted TOTP secret.
    # It must never be logged or exposed through an API.
    mfa_secret_encrypted: Mapped[
        str | None
    ] = mapped_column(
        String(1024),
        nullable=True,
    )

    # -------------------------------------------------
    # LOGIN SECURITY
    # -------------------------------------------------

    failed_login_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    locked_until: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_login_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Soft deletion prevents immediate destruction of
    # security and audit relationships.
    deleted_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # -------------------------------------------------
    # RELATIONSHIPS
    # -------------------------------------------------

    patient_profile: Mapped[
        Patient | None
    ] = relationship(
        back_populates="linked_user",
        uselist=False,
        foreign_keys="Patient.linked_user_id",
    )


# =====================================================
# EMAIL VERIFICATION TOKEN
# =====================================================

class EmailVerificationToken(
    IdMixin,
    Base,
):
    """
    Stores a hashed email-verification OTP.

    The plaintext OTP is sent to the user's email address,
    but only its cryptographic hash is stored.

    Verification tokens are:

    - time limited;
    - single use;
    - attempt limited.
    """

    __tablename__ = "email_verification_tokens"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    consumed_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )


# =====================================================
# PASSWORD RESET TOKEN
# =====================================================

class PasswordResetToken(
    IdMixin,
    Base,
):
    """
    Stores a hashed password-reset token.

    Password-reset tokens are short-lived and may only be
    used once. Plaintext reset tokens must never be stored.
    """

    __tablename__ = "password_reset_tokens"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    consumed_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )


# =====================================================
# SYNTHETIC PATIENT PROFILE
# =====================================================

class Patient(
    IdMixin,
    TimeMixin,
    Base,
):
    """
    Represents a synthetic MEDISCOPE patient.

    Patient records used by the capstone prototype must
    always have is_synthetic set to True.
    """

    __tablename__ = "patients"

    linked_user_id: Mapped[
        UUID | None
    ] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        unique=True,
        nullable=True,
    )

    synthetic_patient_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    date_of_birth: Mapped[
        date | None
    ] = mapped_column(
        Date,
        nullable=True,
    )

    sex: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    lga: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(40),
        default="ACTIVE",
        index=True,
        nullable=False,
    )

    is_synthetic: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    last_updated_by: Mapped[
        UUID | None
    ] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    # -------------------------------------------------
    # RELATIONSHIPS
    # -------------------------------------------------

    linked_user: Mapped[
        User | None
    ] = relationship(
        back_populates="patient_profile",
        foreign_keys=[linked_user_id],
    )

    clinical_records: Mapped[
        list[ClinicalRecord]
    ] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    clinician_assignments: Mapped[
        list[ClinicianPatientAssignment]
    ] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
    )


# =====================================================
# CLINICIAN-PATIENT ASSIGNMENT
# =====================================================

class ClinicianPatientAssignment(
    IdMixin,
    Base,
):
    """
    Links clinicians to patients.

    The table supports:

    - one clinician being assigned multiple patients;
    - one patient being assigned multiple clinicians;
    - preserving historical assignments.

    Duplicate active assignments are prevented by the
    application service before insertion.
    """

    __tablename__ = "clinician_patient_assignments"

    clinician_user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )

    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "patients.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )

    assigned_by: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    ended_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
        nullable=False,
    )

    # -------------------------------------------------
    # RELATIONSHIPS
    # -------------------------------------------------

    patient: Mapped[Patient] = relationship(
        back_populates="clinician_assignments",
    )


# =====================================================
# CLINICAL RECORD
# =====================================================

class ClinicalRecord(
    IdMixin,
    TimeMixin,
    Base,
):
    """
    Stores synthetic clinical information used to support
    LTFU risk prediction.

    Only authorised clinicians should directly modify an
    approved clinical record.
    """

    __tablename__ = "clinical_records"

    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "patients.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )

    recorded_by: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    art_start_date: Mapped[
        date | None
    ] = mapped_column(
        Date,
        nullable=True,
    )

    age_at_art_initiation: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    last_regimen: Mapped[
        str | None
    ] = mapped_column(
        String(200),
        nullable=True,
    )

    days_of_arv_refill: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    current_viral_load: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    pregnancy_status: Mapped[
        str | None
    ] = mapped_column(
        String(100),
        nullable=True,
    )

    last_clinic_visit_date: Mapped[
        date | None
    ] = mapped_column(
        Date,
        nullable=True,
    )

    notes: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    # -------------------------------------------------
    # RELATIONSHIPS
    # -------------------------------------------------

    patient: Mapped[Patient] = relationship(
        back_populates="clinical_records",
    )


# =====================================================
# HEALTH-RECORD CHANGE REQUEST
# =====================================================

class HealthRecordChangeRequest(
    IdMixin,
    TimeMixin,
    Base,
):
    """
    Stores a health-record amendment proposed by a user.

    The authoritative clinical record is not changed until
    an authorised clinician approves the request.
    """

    __tablename__ = "health_record_change_requests"

    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "patients.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )

    clinical_record_id: Mapped[
        UUID | None
    ] = mapped_column(
        ForeignKey(
            "clinical_records.id",
            ondelete="CASCADE",
        ),
        nullable=True,
    )

    requested_by: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    field_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    previous_value: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    proposed_value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    reason: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default=ChangeRequestStatus.PENDING.value,
        index=True,
        nullable=False,
    )

    reviewed_by: Mapped[
        UUID | None
    ] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    reviewed_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    review_comment: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )


# =====================================================
# MACHINE-LEARNING MODEL REGISTRY
# =====================================================

class ModelRegistry(
    IdMixin,
    TimeMixin,
    Base,
):
    """
    Stores deployment and evaluation information for each
    trained machine-learning model version.

    Historical predictions remain linked to the exact model
    versions that produced them.
    """

    __tablename__ = "model_registry"

    __table_args__ = (
        UniqueConstraint(
            "model_name",
            "model_version",
            name="uq_model_version",
        ),
    )

    model_name: Mapped[str] = mapped_column(
        String(150),
        index=True,
        nullable=False,
    )

    model_version: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    algorithm: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    artifact_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    trained_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    deployed_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    threshold: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    feature_schema_version: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    evaluation_metrics: Mapped[
        dict[str, Any]
    ] = mapped_column(
        JSON,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        nullable=False,
    )

    notes: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )


# =====================================================
# SAVED MODEL PREDICTION
# =====================================================

class Prediction(
    IdMixin,
    Base,
):
    """
    Stores an immutable snapshot of a two-model LTFU risk
    prediction.

    Results from Logistic Regression and XGBoost are stored
    separately rather than silently averaged.
    """

    __tablename__ = "predictions"

    __table_args__ = (
        Index(
            "ix_predictions_patient_generated",
            "patient_id",
            "generated_at",
        ),
    )

    patient_id: Mapped[
        UUID | None
    ] = mapped_column(
        ForeignKey(
            "patients.id",
            ondelete="SET NULL",
        ),
        index=True,
        nullable=True,
    )

    requested_by: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    logistic_model_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "model_registry.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    xgboost_model_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "model_registry.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    logistic_probability: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    logistic_classification: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    xgboost_probability: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    xgboost_classification: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    agreement_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    threshold_used: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    input_schema_version: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    # The snapshot should contain only the model inputs
    # required for reproducibility and must not include
    # passwords, authentication tokens or direct identifiers.
    input_snapshot: Mapped[
        dict[str, Any]
    ] = mapped_column(
        JSON,
        nullable=False,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        index=True,
        nullable=False,
    )

    clinical_review_status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        nullable=False,
    )

    reviewed_by: Mapped[
        UUID | None
    ] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    reviewed_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


# =====================================================
# INTERNAL MESSAGE
# =====================================================

class Message(
    IdMixin,
    Base,
):
    """
    Stores a direct message, system notification or
    application announcement.
    """

    __tablename__ = "messages"

    sender_id: Mapped[
        UUID | None
    ] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        index=True,
        nullable=True,
    )

    message_type: Mapped[str] = mapped_column(
        String(30),
        default="DIRECT",
        nullable=False,
    )

    subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        index=True,
        nullable=False,
    )


# =====================================================
# MESSAGE RECIPIENT
# =====================================================

class MessageRecipient(
    IdMixin,
    Base,
):
    """
    Associates a message with one recipient.

    A separate recipient table allows a message or system
    announcement to be delivered to multiple users.
    """

    __tablename__ = "message_recipients"

    __table_args__ = (
        UniqueConstraint(
            "message_id",
            "recipient_id",
            name="uq_message_recipient",
        ),
    )

    message_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "messages.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )

    recipient_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )

    read_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Supports hiding a message for one recipient without
    # deleting it for other recipients.
    deleted_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


# =====================================================
# SECURITY AND AUDIT LOG
# =====================================================

class AuditLog(
    IdMixin,
    Base,
):
    """
    Records important system and security events.

    Audit logs should identify:

    - who performed an action;
    - what action was attempted;
    - which resource was affected;
    - when it occurred;
    - whether it succeeded or failed.

    Sensitive values such as passwords, OTPs, tokens and
    full clinical records must never be stored in details.
    """

    __tablename__ = "audit_logs"

    __table_args__ = (
        Index(
            "ix_audit_actor_created",
            "actor_user_id",
            "created_at",
        ),
        Index(
            "ix_audit_resource",
            "resource_type",
            "resource_id",
        ),
    )

    actor_user_id: Mapped[
        UUID | None
    ] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        index=True,
        nullable=True,
    )

    action: Mapped[str] = mapped_column(
        String(120),
        index=True,
        nullable=False,
    )

    resource_type: Mapped[
        str | None
    ] = mapped_column(
        String(120),
        nullable=True,
    )

    # This is intentionally not a foreign key because an
    # audit event may refer to different resource tables.
    resource_id: Mapped[
        UUID | None
    ] = mapped_column(
        nullable=True,
    )

    outcome: Mapped[str] = mapped_column(
        String(30),
        index=True,
        nullable=False,
    )

    ip_address: Mapped[
        str | None
    ] = mapped_column(
        String(64),
        nullable=True,
    )

    user_agent: Mapped[
        str | None
    ] = mapped_column(
        String(500),
        nullable=True,
    )

    details: Mapped[
        dict[str, Any] | None
    ] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        index=True,
        nullable=False,
    )
