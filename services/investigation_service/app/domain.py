from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class InvestigationPlan(BaseModel):
    id: UUID
    case_id: UUID
    issue_ids: list[UUID]
    scope: str
    evidence_sources: list[str]
    witness_refs: list[str]
    milestones: list[dict[str, Any]]

class Interview(BaseModel):
    id: UUID
    case_id: UUID
    participant_ref: str
    interpreter_ref: str | None = None
    support_person_ref: str | None = None
    recording_consent: bool = False
    notes_ref: str
    confirmation_status: str

class Finding(BaseModel):
    id: UUID
    allegation_id: UUID
    category: str = Field(pattern='^(substantiated|unsubstantiated|inconclusive|referred)$')
    rationale_ref: str
    evidence_ids: list[UUID]
    contrary_evidence_ids: list[UUID]
    limitations: list[str]
    reviewer_approval_id: UUID | None = None

class Decision(BaseModel):
    id: UUID
    case_id: UUID
    decision_maker_ref: str
    finding_ids: list[UUID]
    decision_ref: str
    approved_at: datetime | None = None

class Remedy(BaseModel):
    id: UUID
    case_id: UUID
    category: str
    owner_ref: str
    due_at: datetime
    completion_evidence_ref: str | None = None

class Appeal(BaseModel):
    id: UUID
    case_id: UUID
    grounds_ref: str
    reviewer_ref: str
    additional_evidence_ids: list[UUID] = Field(default_factory=list)
    status: str = 'open'
