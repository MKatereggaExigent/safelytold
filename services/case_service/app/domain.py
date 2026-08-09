from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class Case(BaseModel):
    id: UUID
    tenant_id: UUID
    public_reference: str
    status: str = 'unverified'
    jurisdiction_code: str
    severity_band: str
    workflow_id: str
    policy_version_id: UUID

class Allegation(BaseModel):
    id: UUID
    case_id: UUID
    taxonomy_code: str
    status: str = 'under_assessment'
    standard_of_proof: str | None = None

class CaseParty(BaseModel):
    id: UUID
    case_id: UUID
    party_ref: str
    role: str
    visibility: str = 'restricted'

class RelationshipEdge(BaseModel):
    case_id: UUID
    source_party_ref: str
    relation: str
    target_party_ref: str
    valid_at: datetime

class Assignment(BaseModel):
    id: UUID
    case_id: UUID
    subject_id: str
    role: str
    purpose: str
    valid_until: datetime
    conflict_check_id: UUID

class ConflictCheck(BaseModel):
    id: UUID
    case_id: UUID
    candidate_subject_id: str
    conflicts: list[str]
    decision: str
    reviewed_by: str | None = None

class Recusal(BaseModel):
    id: UUID
    case_id: UUID
    subject_id: str
    reason: str
    effective_at: datetime
