from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class AIRunRecord(BaseModel):
    id: UUID
    tenant_id: UUID
    case_id: UUID | None = None
    capability: str
    model_provider: str
    model_id: str
    prompt_version: str
    source_refs: list[str]
    input_commitment: str
    output_ref: str
    uncertainty: str
    status: str

class AIEvaluation(BaseModel):
    id: UUID
    run_id: UUID
    dimensions: dict[str, float]
    privacy_leak_detected: bool
    prohibited_recommendation_detected: bool

class AIApproval(BaseModel):
    id: UUID
    run_id: UUID
    reviewer_ref: str
    disposition: str
    rationale: str
    reviewed_at: datetime
