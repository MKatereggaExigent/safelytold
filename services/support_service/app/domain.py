from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class SupporterInvitation(BaseModel):
    id: UUID
    case_id: UUID
    supporter_type: str
    recipient_commitment: str
    permissions: set[str]
    consent_receipt_id: UUID
    expires_at: datetime

class ReferralDirectoryEntry(BaseModel):
    id: UUID
    jurisdiction_code: str
    category: str
    provider_name: str
    contact_route: str
    disclaimer: str

class SupportReferral(BaseModel):
    id: UUID
    case_id: UUID
    directory_entry_id: UUID
    consent_status: str
    created_at: datetime
