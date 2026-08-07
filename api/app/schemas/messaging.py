"""Pydantic schemas for MEDISCOPE internal messaging."""
from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class MessageCreateRequest(BaseModel):
    recipient_ids: list[UUID] = Field(min_length=1, max_length=100)
    subject: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1, max_length=10000)


class MessageResponse(BaseModel):
    id: UUID
    sender_id: UUID | None
    message_type: str
    subject: str
    body: str
    created_at: datetime
    model_config = {"from_attributes": True}


class InboxMessageResponse(BaseModel):
    message_id: UUID
    sender_id: UUID | None
    subject: str
    body: str
    created_at: datetime
    read_at: datetime | None
