from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class AuditAccessGrant(BaseModel):
    id: UUID
    tenant_id: UUID
    subject_ref: str
    resource_commitment: str
    purpose: str
    approved_by: list[str]
    starts_at: datetime
    ends_at: datetime

class AuditBatch(BaseModel):
    id: UUID
    tenant_commitment: str
    sequence_start: int
    sequence_end: int
    leaf_hashes: list[str]
    merkle_root: str
    anchor_id: UUID | None = None
