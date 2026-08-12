from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class MessageCreateRequest(BaseModel):
    recipient_ids: list[UUID] = Field(min_length=1, max_length=100)
    subject: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1, max_length=10000)

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    sender_id: UUID | None
    message_type: str
    subject: str
    body: str
    created_at: datetime

class InboxMessageResponse(BaseModel):
    message_id: UUID
    sender_id: UUID | None
    sender_name: str | None
    subject: str
    body: str
    created_at: datetime
    read_at: datetime | None

class SentMessageResponse(BaseModel):
    id: UUID
    recipient_ids: list[UUID]
    subject: str
    body: str
    message_type: str
    created_at: datetime

class MessageRecipientOption(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    role: str
