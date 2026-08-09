from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class ConsentReceipt(BaseModel):
    id: UUID
    tenant_id: UUID
    subject_ref: str
    purpose: str
    notice_version: str
    decision: str
    recorded_at: datetime

class DataSubjectRequest(BaseModel):
    id: UUID
    tenant_id: UUID
    request_type: str
    requester_ref: str
    identity_verification_ref: str
    scope: list[str]
    due_at: datetime
    restrictions: list[str] = Field(default_factory=list)

class RetentionRule(BaseModel):
    id: UUID
    jurisdiction_code: str
    record_class: str
    review_after_days: int
    legal_hold_override: bool = True

class BreachCase(BaseModel):
    id: UUID
    tenant_id: UUID
    incident_id: UUID
    jurisdictions: list[str]
    affected_data_classes: list[str]
    notification_decisions: list[dict[str, Any]]
