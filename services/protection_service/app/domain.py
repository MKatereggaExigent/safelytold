from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class ProtectionPlan(BaseModel):
    id: UUID
    case_id: UUID
    requested_measures: list[str]
    approved_measures: list[str]
    owner_ref: str
    next_review_at: datetime
    status: str = 'active'

class RetaliationBaseline(BaseModel):
    case_id: UUID
    employment_events: list[str]
    access_consents: list[str]
    captured_at: datetime

class RetaliationCheckIn(BaseModel):
    id: UUID
    case_id: UUID
    due_at: datetime
    completed_at: datetime | None = None
    risk_band: str | None = None
    escalation_id: UUID | None = None
