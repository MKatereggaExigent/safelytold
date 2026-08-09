from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class MailboxMessage(BaseModel):
    id: UUID
    case_id: UUID
    sender_realm: str
    encrypted_body_ref: str
    attachment_ids: list[UUID] = Field(default_factory=list)
    created_at: datetime
    read_at: datetime | None = None

class ConflictChallenge(BaseModel):
    id: UUID
    case_id: UUID
    challenged_assignment_id: UUID
    reason_category: str
    encrypted_details_ref: str
    status: str = 'submitted'

class RetaliationConcern(BaseModel):
    id: UUID
    case_id: UUID
    risk_band: str
    encrypted_details_ref: str
    protection_review_required: bool = True

class SafeContactPreference(BaseModel):
    case_id: UUID
    allowed_channels: list[str]
    prohibited_times: list[str]
    neutral_message_only: bool = True
