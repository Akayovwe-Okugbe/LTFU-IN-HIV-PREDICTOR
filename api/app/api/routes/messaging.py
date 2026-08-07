"""Role-aware internal messaging endpoints."""
from __future__ import annotations
from datetime import UTC, datetime
from uuid import UUID
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.api.dependencies import CurrentUser, DbSession
from app.core.enums import UserRole
from app.models.entities import ClinicianPatientAssignment, Message, MessageRecipient, Patient, User
from app.schemas.messaging import InboxMessageResponse, MessageCreateRequest, MessageResponse

router = APIRouter(prefix="/messages", tags=["Messaging"])


def _allowed_user_recipients(db: DbSession, *, user: User) -> set[UUID]:
    """Return administrators and assigned clinicians available to a standard user."""
    administrator_ids = set(
        db.scalars(
            select(User.id).where(
                User.role == UserRole.ADMINISTRATOR.value,
                User.deleted_at.is_(None),
            )
        ).all()
    )

    patient = db.scalar(select(Patient).where(Patient.linked_user_id == user.id))
    if patient is None:
        return administrator_ids

    clinician_ids = set(
        db.scalars(
            select(ClinicianPatientAssignment.clinician_user_id).where(
                ClinicianPatientAssignment.patient_id == patient.id,
                ClinicianPatientAssignment.is_active.is_(True),
            )
        ).all()
    )
    return administrator_ids | clinician_ids


@router.post("", response_model=MessageResponse, status_code=201)
def send_message(
    payload: MessageCreateRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> Message:
    """Send a direct message while enforcing role-based recipient rules."""
    recipient_ids = set(payload.recipient_ids)

    existing = set(
        db.scalars(
            select(User.id).where(
                User.id.in_(recipient_ids),
                User.deleted_at.is_(None),
            )
        ).all()
    )
    if existing != recipient_ids:
        raise HTTPException(status_code=400, detail="One or more recipients are invalid.")

    if current_user.role == UserRole.USER.value:
        allowed = _allowed_user_recipients(db, user=current_user)
        if not recipient_ids.issubset(allowed):
            raise HTTPException(
                status_code=403,
                detail="Users may message administrators and assigned clinicians only.",
            )

    message = Message(
        sender_id=current_user.id,
        message_type="DIRECT",
        subject=payload.subject,
        body=payload.body,
    )
    db.add(message)
    db.flush()

    for recipient_id in recipient_ids:
        db.add(MessageRecipient(message_id=message.id, recipient_id=recipient_id))

    db.commit()
    db.refresh(message)
    return message


@router.get("/inbox", response_model=list[InboxMessageResponse])
def inbox(
    db: DbSession,
    current_user: CurrentUser,
) -> list[InboxMessageResponse]:
    """Return the authenticated user's inbox."""
    rows = db.execute(
        select(Message, MessageRecipient)
        .join(MessageRecipient, MessageRecipient.message_id == Message.id)
        .where(MessageRecipient.recipient_id == current_user.id)
        .order_by(Message.created_at.desc())
    ).all()

    return [
        InboxMessageResponse(
            message_id=message.id,
            sender_id=message.sender_id,
            subject=message.subject,
            body=message.body,
            created_at=message.created_at,
            read_at=recipient.read_at,
        )
        for message, recipient in rows
    ]


@router.post("/{message_id}/read", status_code=204)
def mark_message_read(
    message_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Mark a received message as read."""
    recipient = db.scalar(
        select(MessageRecipient).where(
            MessageRecipient.message_id == message_id,
            MessageRecipient.recipient_id == current_user.id,
        )
    )
    if recipient is None:
        raise HTTPException(status_code=404, detail="Message not found.")

    if recipient.read_at is None:
        recipient.read_at = datetime.now(UTC)

    db.commit()
