from __future__ import annotations

import os
import secrets
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import DateTime, JSON, String, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from safelytold_common.auth import get_context_or_none
from safelytold_common.config import Settings, settings
from safelytold_common.db import Base, session
from safelytold_common.hashing import MerkleProofStep, merkle_root, verify_proof
from safelytold_common.service import create_app

from .evm import submit_anchor

router = APIRouter(prefix='/v1/ledger', tags=['blockchain-ledger'])


async def require_anchor_auth(
    authorization: Annotated[str | None, Header()] = None,
    x_anchor_token: Annotated[str | None, Header()] = None,
    x_purpose: Annotated[str | None, Header()] = None,
    cfg: Settings = Depends(settings),
) -> None:
    """Accept a verified staff JWT or the shared worker anchor token."""
    if (
        cfg.blockchain_anchor_token
        and x_anchor_token
        and secrets.compare_digest(x_anchor_token, cfg.blockchain_anchor_token)
    ):
        return
    if await get_context_or_none(authorization=authorization, x_purpose=x_purpose, cfg=cfg) is not None:
        return
    raise HTTPException(401, 'Anchor authorization required')


AnchorsDep = Annotated[None, Depends(require_anchor_auth)]


class Kind(StrEnum):
    AUDIT = 'audit_batch'
    EVIDENCE = 'evidence_manifest'
    DISCLOSURE = 'disclosure_package'
    POLICY = 'policy_version'


class Anchor(Base):
    __tablename__ = 'anchor_records'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_hash: Mapped[str] = mapped_column(String(64), index=True)
    batch_id: Mapped[str] = mapped_column(String(160), index=True)
    kind: Mapped[str] = mapped_column(String(80))
    merkle_root: Mapped[str] = mapped_column(String(64), unique=True)
    leaf_count: Mapped[int]
    chain_id: Mapped[str] = mapped_column(String(80))
    transaction_hash: Mapped[str | None] = mapped_column(String(80))
    mode: Mapped[str] = mapped_column(String(40))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    anchored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class AnchorRequest(BaseModel):
    tenant_hash: str = Field(pattern=r'^[0-9a-f]{64}$')
    batch_id: str = Field(min_length=1, max_length=160)
    kind: Kind
    leaf_hashes: list[str] = Field(min_length=1, max_length=10000)
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator('leaf_hashes')
    @classmethod
    def hashes(cls, value: list[str]) -> list[str]:
        if any(len(item) != 64 or any(char not in '0123456789abcdef' for char in item) for item in value):
            raise ValueError('SHA-256 lowercase hashes only')
        return value


@router.post('/anchors')
async def anchor(body: AnchorRequest, _: AnchorsDep, database: AsyncSession = Depends(session)) -> dict[str, Any]:
    root = merkle_root(body.leaf_hashes)
    old = await database.scalar(select(Anchor).where(Anchor.merkle_root == root))
    if old:
        return {'anchor_id': str(old.id), 'merkle_root': root, 'leaf_count': old.leaf_count, 'mode': old.mode, 'transaction_hash': old.transaction_hash, 'chain_id': old.chain_id}

    mode = os.getenv('BLOCKCHAIN_MODE', 'database')
    chain_id = os.getenv('BLOCKCHAIN_CHAIN_ID', 'unconfigured')
    transaction_hash = None
    metadata = dict(body.metadata)
    if mode == 'evm':
        receipt = await submit_anchor(body.tenant_hash, body.batch_id, root, body.kind.value, len(body.leaf_hashes))
        chain_id = receipt.chain_id
        transaction_hash = receipt.transaction_hash
        metadata['block_number'] = str(receipt.block_number)

    value = Anchor(
        tenant_hash=body.tenant_hash,
        batch_id=body.batch_id,
        kind=body.kind.value,
        merkle_root=root,
        leaf_count=len(body.leaf_hashes),
        chain_id=chain_id,
        transaction_hash=transaction_hash,
        mode=mode,
        metadata_json=metadata,
    )
    database.add(value)
    await database.commit()
    return {'anchor_id': str(value.id), 'merkle_root': root, 'leaf_count': len(body.leaf_hashes), 'mode': mode, 'transaction_hash': transaction_hash, 'chain_id': chain_id}


@router.get('/anchors')
async def list_anchors(_: AnchorsDep, database: AsyncSession = Depends(session), limit: int = 100):
    rows = list(await database.scalars(select(Anchor).order_by(Anchor.anchored_at.desc()).limit(min(max(limit, 1), 500))))
    return [{'anchor_id': str(row.id), 'tenant_hash': row.tenant_hash, 'batch_id': row.batch_id, 'kind': row.kind, 'merkle_root': row.merkle_root, 'leaf_count': row.leaf_count, 'mode': row.mode, 'transaction_hash': row.transaction_hash, 'chain_id': row.chain_id, 'anchored_at': row.anchored_at} for row in rows]


class Proof(BaseModel):
    leaf_hash: str
    root: str
    proof: list[dict[str, Any]]


@router.post('/proofs/verify')
async def proof(body: Proof) -> dict[str, bool]:
    return {'valid': verify_proof(body.leaf_hash, [MerkleProofStep(**item) for item in body.proof], body.root)}


app = create_app('Blockchain Ledger Service', 'Hashes and Merkle roots only; no case or identity data.', [router])
