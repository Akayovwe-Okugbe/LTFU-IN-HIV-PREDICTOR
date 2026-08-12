from __future__ import annotations
from datetime import UTC, datetime
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.dependencies import CurrentUser, DbSession
from app.core.enums import UserRole
from app.models.entities import ClinicianPatientAssignment, Message, MessageRecipient, Patient, User
from app.schemas.messaging import InboxMessageResponse, MessageCreateRequest, MessageRecipientOption, MessageResponse, SentMessageResponse

router = APIRouter(prefix='/messages', tags=['Messaging'])

def _allowed_user_recipients(db: DbSession, *, user: User) -> set[UUID]:
    administrator_ids = set(db.scalars(select(User.id).where(User.role == UserRole.ADMINISTRATOR.value, User.deleted_at.is_(None))).all())
    patient = db.scalar(select(Patient).where(Patient.linked_user_id == user.id))
    if patient is None:
        return administrator_ids
    clinician_ids = set(db.scalars(select(ClinicianPatientAssignment.clinician_user_id).where(ClinicianPatientAssignment.patient_id == patient.id, ClinicianPatientAssignment.is_active.is_(True))).all())
    return administrator_ids | clinician_ids

def _permitted_recipient_ids(db: DbSession, *, current_user: User) -> set[UUID]:
    if current_user.role == UserRole.USER.value:
        return _allowed_user_recipients(db, user=current_user)
    return set(db.scalars(select(User.id).where(User.deleted_at.is_(None), User.id != current_user.id)).all())

@router.get('/recipients', response_model=list[MessageRecipientOption])
def available_recipients(db: DbSession, current_user: CurrentUser) -> list[MessageRecipientOption]:
    allowed_ids = _permitted_recipient_ids(db, current_user=current_user)
    if not allowed_ids:
        return []
    users = list(db.scalars(select(User).where(User.id.in_(allowed_ids), User.deleted_at.is_(None)).order_by(User.first_name.asc(), User.last_name.asc())).all())
    return [MessageRecipientOption(id=u.id, email=u.email, first_name=u.first_name, last_name=u.last_name, role=u.role) for u in users]

@router.post('', response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(payload: MessageCreateRequest, db: DbSession, current_user: CurrentUser) -> Message:
    recipient_ids = set(payload.recipient_ids)
    existing = set(db.scalars(select(User.id).where(User.id.in_(recipient_ids), User.deleted_at.is_(None))).all())
    if existing != recipient_ids:
        raise HTTPException(status_code=400, detail='One or more recipients are invalid.')
    allowed = _permitted_recipient_ids(db, current_user=current_user)
    if not recipient_ids.issubset(allowed):
        raise HTTPException(status_code=403, detail='One or more recipients are not permitted.')
    message = Message(sender_id=current_user.id, message_type='DIRECT', subject=payload.subject.strip(), body=payload.body.strip())
    db.add(message); db.flush()
    for recipient_id in recipient_ids:
        db.add(MessageRecipient(message_id=message.id, recipient_id=recipient_id))
    db.commit(); db.refresh(message)
    return message

@router.get('/inbox', response_model=list[InboxMessageResponse])
def inbox(db: DbSession, current_user: CurrentUser) -> list[InboxMessageResponse]:
    rows = db.execute(select(Message, MessageRecipient, User).join(MessageRecipient, MessageRecipient.message_id == Message.id).outerjoin(User, User.id == Message.sender_id).where(MessageRecipient.recipient_id == current_user.id).order_by(Message.created_at.desc())).all()
    return [InboxMessageResponse(message_id=m.id, sender_id=m.sender_id, sender_name=(f'{u.first_name} {u.last_name}' if u is not None else 'MEDISCOPE System'), subject=m.subject, body=m.body, created_at=m.created_at, read_at=r.read_at) for m,r,u in rows]

@router.get('/sent', response_model=list[SentMessageResponse])
def sent_messages(db: DbSession, current_user: CurrentUser) -> list[SentMessageResponse]:
    messages = list(db.scalars(select(Message).where(Message.sender_id == current_user.id).order_by(Message.created_at.desc())).all())
    result: list[SentMessageResponse] = []
    for message in messages:
        recipient_ids = list(db.scalars(select(MessageRecipient.recipient_id).where(MessageRecipient.message_id == message.id)).all())
        result.append(SentMessageResponse(id=message.id, recipient_ids=recipient_ids, subject=message.subject, body=message.body, message_type=message.message_type, created_at=message.created_at))
    return result

@router.post('/{message_id}/read', status_code=status.HTTP_204_NO_CONTENT)
def mark_message_read(message_id: UUID, db: DbSession, current_user: CurrentUser) -> None:
    recipient = db.scalar(select(MessageRecipient).where(MessageRecipient.message_id == message_id, MessageRecipient.recipient_id == current_user.id))
    if recipient is None:
        raise HTTPException(status_code=404, detail='Message not found.')
    if recipient.read_at is None:
        recipient.read_at = datetime.now(UTC)
    db.commit()

@router.delete('/{message_id}', status_code=status.HTTP_204_NO_CONTENT)
def remove_from_inbox(message_id: UUID, db: DbSession, current_user: CurrentUser) -> None:
    recipient = db.scalar(select(MessageRecipient).where(MessageRecipient.message_id == message_id, MessageRecipient.recipient_id == current_user.id))
    if recipient is None:
        raise HTTPException(status_code=404, detail='Message not found.')
    db.delete(recipient); db.commit()
