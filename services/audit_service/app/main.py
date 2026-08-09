from __future__ import annotations

import hmac
import os
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, JSON, String, UniqueConstraint, select, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from safelytold_common.auth import ContextDep
from safelytold_common.db import Base, session, set_tenant
from safelytold_common.hashing import chained_hash
from safelytold_common.privacy import assert_event_safe
from safelytold_common.service import create_app

router = APIRouter(prefix='/v1/audit', tags=['audit'])
GENESIS = '00' * 32


class Entry(Base):
    __tablename__ = 'audit_entries'
    __table_args__ = (UniqueConstraint('tenant_id', 'sequence', name='uq_audit_tenant_sequence'),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    sequence: Mapped[int] = mapped_column(index=True)
    event_type: Mapped[str] = mapped_column(String(120))
    subject_ref: Mapped[str] = mapped_column(String(240))
    actor_ref: Mapped[str] = mapped_column(String(240))
    purpose: Mapped[str] = mapped_column(String(160))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    previous_hash: Mapped[str] = mapped_column(String(64))
    entry_hash: Mapped[str] = mapped_column(String(64), unique=True)
    signature: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class Create(BaseModel):
    event_type: str
    subject_ref: str
    purpose: str
    metadata: dict[str, Any] = Field(default_factory=dict)


def _material(value: Entry | None, *, tenant_id: UUID, sequence: int, event_type: str, subject_ref: str, actor_ref: str, purpose: str, metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        'tenant_id': str(tenant_id),
        'sequence': sequence,
        'event_type': event_type,
        'subject_ref': subject_ref,
        'actor_ref': actor_ref,
        'purpose': purpose,
        'metadata': metadata,
    }


def _signature(entry_hash: str) -> str:
    key = os.getenv('AUDIT_SIGNING_KEY', 'development-only-change-me').encode()
    return hmac.new(key, bytes.fromhex(entry_hash), sha256).hexdigest()


@router.post('/entries')
async def append(body: Create, context: ContextDep, database: AsyncSession = Depends(session)) -> dict[str, Any]:
    assert_event_safe(body.metadata)
    await set_tenant(database, context.tenant_id)
    # Serialise each tenant chain head to prevent two writers creating the same sequence.
    await database.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:tenant, 0))'), {'tenant': str(context.tenant_id)})
    last = await database.scalar(
        select(Entry).where(Entry.tenant_id == context.tenant_id).order_by(Entry.sequence.desc()).limit(1)
    )
    sequence = 1 if last is None else last.sequence + 1
    previous = GENESIS if last is None else last.entry_hash
    material = _material(None, tenant_id=context.tenant_id, sequence=sequence, event_type=body.event_type, subject_ref=body.subject_ref, actor_ref=context.subject_id, purpose=body.purpose, metadata=body.metadata)
    entry_hash = chained_hash(previous, material)
    signature = _signature(entry_hash)
    value = Entry(
        tenant_id=context.tenant_id,
        sequence=sequence,
        event_type=body.event_type,
        subject_ref=body.subject_ref,
        actor_ref=context.subject_id,
        purpose=body.purpose,
        metadata_json=body.metadata,
        previous_hash=previous,
        entry_hash=entry_hash,
        signature=signature,
    )
    database.add(value)
    await database.commit()
    return {'id': str(value.id), 'sequence': sequence, 'entry_hash': entry_hash, 'previous_hash': previous, 'signature': signature}


@router.get('/verify/{tenant_id}')
async def verify(tenant_id: UUID, database: AsyncSession = Depends(session)) -> dict[str, Any]:
    rows = list(await database.scalars(select(Entry).where(Entry.tenant_id == tenant_id).order_by(Entry.sequence)))
    previous = GENESIS
    for expected_sequence, value in enumerate(rows, start=1):
        material = _material(None, tenant_id=value.tenant_id, sequence=value.sequence, event_type=value.event_type, subject_ref=value.subject_ref, actor_ref=value.actor_ref, purpose=value.purpose, metadata=value.metadata_json)
        expected_hash = chained_hash(previous, material)
        if value.sequence != expected_sequence or value.previous_hash != previous or not hmac.compare_digest(value.entry_hash, expected_hash) or not hmac.compare_digest(value.signature, _signature(value.entry_hash)):
            return {'valid': False, 'failed_sequence': value.sequence}
        previous = value.entry_hash
    return {'valid': True, 'entries': len(rows), 'head': previous}


app = create_app('Audit Service', 'Append-only hash chain; separate store in production.', [router])
