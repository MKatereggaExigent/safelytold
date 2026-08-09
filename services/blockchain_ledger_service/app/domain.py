from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class IntegrityAnchorRecord(BaseModel):
    id: UUID
    tenant_commitment: str
    batch_commitment: str
    root_kind: str
    merkle_root: str
    leaf_count: int
    chain_id: str
    transaction_hash: str | None = None
    anchored_at: datetime | None = None

class VerificationBundle(BaseModel):
    leaf_hash: str
    proof: list[dict[str, Any]]
    root: str
    contract_address: str
    chain_id: str
    transaction_hash: str
