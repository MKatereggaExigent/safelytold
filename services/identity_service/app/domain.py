from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class StaffIdentity(BaseModel):
    id: UUID
    tenant_id: UUID
    external_subject: str
    status: str
    roles: set[str] = Field(default_factory=set)
    organisational_unit_ids: set[UUID] = Field(default_factory=set)

class ScopedInvitation(BaseModel):
    id: UUID
    tenant_id: UUID
    invitee_email_commitment: str
    case_id: UUID
    role: str
    expires_at: datetime

class AccessGrant(BaseModel):
    id: UUID
    tenant_id: UUID
    subject_id: str
    resource_id: UUID
    actions: set[str]
    purpose: str
    approved_by: list[str]
    valid_from: datetime
    valid_until: datetime
