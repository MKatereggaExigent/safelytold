from __future__ import annotations

import hashlib
from enum import StrEnum
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import BigInteger, Boolean, JSON, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from safelytold_common.auth import ContextDep
from safelytold_common.db import Base, OutboxEvent, TenantMixin, session, set_tenant
from safelytold_common.service import create_app

from .scanner import scan_bytes
from .storage import store_sealed

router = APIRouter(prefix='/v1/evidence', tags=['evidence'])


class Kind(StrEnum):
    SEALED = 'sealed_original'
    WORKING = 'working_copy'
    REDACTED = 'redacted_copy'


class Evidence(TenantMixin, Base):
    __tablename__ = 'evidence_objects'
    case_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    original_filename: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(120))
    copy_kind: Mapped[str] = mapped_column(String(40), default=Kind.SEALED.value)
    object_key: Mapped[str] = mapped_column(String(500), unique=True)
    legal_hold: Mapped[bool] = mapped_column(Boolean, default=False)
    scan_result: Mapped[dict] = mapped_column(JSON, default=dict)


class Receipt(BaseModel):
    evidence_id: UUID
    sha256: str
    size_bytes: int
    copy_kind: Kind
    object_key: str
    scan_status: str


@router.post('/{case_id}/upload', response_model=Receipt)
async def upload(
    case_id: UUID,
    file: UploadFile,
    context: ContextDep,
    database: AsyncSession = Depends(session),
) -> Receipt:
    await set_tenant(database, context.tenant_id)
    data = await file.read(10 * 1024 * 1024 + 1)
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, 'Development upload limit exceeded')
    scan = await scan_bytes(data)
    if scan['status'] == 'malware_detected':
        raise HTTPException(422, 'File rejected by malware scanner')
    digest = hashlib.sha256(data).hexdigest()
    evidence_id = uuid4()
    key = f'tenant/{context.tenant_id}/case/{case_id}/sealed/{evidence_id}'
    await store_sealed(key, data, file.content_type or 'application/octet-stream', digest)
    database.add(
        Evidence(
            id=evidence_id,
            tenant_id=context.tenant_id,
            case_id=case_id,
            sha256=digest,
            size_bytes=len(data),
            original_filename=file.filename or 'unnamed',
            media_type=file.content_type or 'application/octet-stream',
            object_key=key,
            scan_result=scan,
        )
    )
    database.add(
        OutboxEvent(
            tenant_id=context.tenant_id,
            event_type='evidence.received.v1',
            subject=f'evidence/{evidence_id}',
            payload={
                'evidence_id': str(evidence_id),
                'case_id': str(case_id),
                'sha256': digest,
                'size_bytes': len(data),
            },
        )
    )
    await database.commit()
    return Receipt(
        evidence_id=evidence_id,
        sha256=digest,
        size_bytes=len(data),
        copy_kind=Kind.SEALED,
        object_key=key,
        scan_status=scan['status'],
    )


@router.post('/{evidence_id}/legal-hold')
async def hold(
    evidence_id: UUID,
    context: ContextDep,
    database: AsyncSession = Depends(session),
) -> dict[str, str]:
    await set_tenant(database, context.tenant_id)
    value = await database.get(Evidence, evidence_id)
    if value is None or value.tenant_id != context.tenant_id:
        raise HTTPException(404, 'Not found')
    value.legal_hold = True
    await database.commit()
    return {'evidence_id': str(evidence_id), 'legal_hold': 'active'}


app = create_app('Evidence Service', 'Sealed original plus derivative copies; never overwrite originals.', [router])
