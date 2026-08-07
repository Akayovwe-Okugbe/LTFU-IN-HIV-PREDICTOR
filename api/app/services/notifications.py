"""Internal notification helpers for MEDISCOPE Phase 3."""
from __future__ import annotations
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.enums import UserRole
from app.models.entities import Message, MessageRecipient, User


def create_system_message(
    db: Session,
    *,
    recipient_ids: list[UUID],
    subject: str,
    body: str,
) -> Message:
    """Create one system message for one or more recipients."""
    message = Message(
        sender_id=None,
        message_type="SYSTEM",
        subject=subject,
        body=body,
    )
    db.add(message)
    db.flush()

    for recipient_id in set(recipient_ids):
        db.add(
            MessageRecipient(
                message_id=message.id,
                recipient_id=recipient_id,
            )
        )
    return message


def send_welcome_message(db: Session, *, user: User) -> None:
    """Send the standard MEDISCOPE welcome message."""
    create_system_message(
        db,
        recipient_ids=[user.id],
        subject="Welcome to MEDISCOPE",
        body=(
            "Welcome to MEDISCOPE. This prototype uses synthetic patient data "
            "for demonstration and testing. Complete your profile and contact "
            "your administrator or assigned clinician if you need assistance."
        ),
    )


def notify_administrators_of_registration(
    db: Session,
    *,
    new_user: User,
) -> None:
    """Notify administrators that a new account was registered."""
    administrators = db.scalars(
        select(User).where(
            User.role == UserRole.ADMINISTRATOR.value,
            User.deleted_at.is_(None),
        )
    ).all()

    if not administrators:
        return

    create_system_message(
        db,
        recipient_ids=[admin.id for admin in administrators],
        subject="New MEDISCOPE account",
        body=(
            f"A new account was registered for {new_user.first_name} "
            f"{new_user.last_name}. Review role and access requirements if needed."
        ),
    )


def notify_clinician_assignment(
    db: Session,
    *,
    clinician: User,
    patient_number: str,
) -> None:
    """Notify a clinician that a synthetic patient was assigned."""
    create_system_message(
        db,
        recipient_ids=[clinician.id],
        subject="New patient assignment",
        body=(
            f"Synthetic patient {patient_number} has been assigned to you. "
            "Open the clinician workspace to review the patient record."
        ),
    )
