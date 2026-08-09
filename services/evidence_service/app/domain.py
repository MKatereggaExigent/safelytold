from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class EvidenceDerivative(BaseModel):
    id: UUID
    source_evidence_id: UUID
    copy_kind: str
    sha256: str
    transformation_manifest_ref: str
    approved_by: str | None = None

class Redaction(BaseModel):
    id: UUID
    derivative_id: UUID
    redaction_reasons: list[str]
    redaction_map_ref: str
    irreversible_export: bool = False

class DisclosurePackage(BaseModel):
    id: UUID
    case_id: UUID
    purpose: str
    recipient_commitment: str
    evidence_ids: list[UUID]
    manifest_sha256: str
    merkle_root: str | None = None
    expires_at: datetime

class LegalHold(BaseModel):
    id: UUID
    case_id: UUID
    scope: list[str]
    authority_ref: str
    starts_at: datetime
    released_at: datetime | None = None
