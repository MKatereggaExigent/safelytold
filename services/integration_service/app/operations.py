from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import JSON, DateTime, String, UniqueConstraint, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from safelytold_common.auth import ContextDep
from safelytold_common.db import Base, OutboxEvent, session, set_tenant
from safelytold_common.reporting_modes import REPORTING_MODES

Area = Literal['awareness', 'training', 'qa', 'continuity', 'coverage', 'hotline', 'reporting']

router = APIRouter(prefix='/v1/operations', tags=['operations'])


class OperationalRecord(Base):
    __tablename__ = 'operational_records'
    __table_args__ = (UniqueConstraint('tenant_id', 'area', 'idempotency_key', name='uq_operational_idempotency'),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    area: Mapped[str] = mapped_column(String(30), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(160))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


INITIAL = {
    'awareness': 'draft', 'training': 'assigned', 'qa': 'open', 'continuity': 'planned',
    'coverage': 'planned', 'hotline': 'received', 'reporting': 'scheduled',
}
TRANSITIONS = {
    'awareness': {'draft': {'approved'}, 'approved': {'published'}, 'published': {'retired'}},
    'training': {'assigned': {'in_progress', 'passed', 'failed'}, 'in_progress': {'passed', 'failed'}, 'failed': {'in_progress'}},
    'qa': {'open': {'approved', 'blocked'}, 'blocked': {'open'}, 'approved': set()},
    'continuity': {'planned': {'passed', 'failed'}, 'failed': {'planned'}, 'passed': set()},
    'coverage': {'planned': {'active', 'cancelled'}, 'active': {'completed', 'cancelled'}, 'completed': set(), 'cancelled': set()},
    'hotline': {'received': {'submitted', 'escalated'}, 'submitted': {'closed', 'escalated'}, 'escalated': {'closed'}, 'closed': set()},
    'reporting': {'scheduled': {'generated'}, 'generated': {'approved'}, 'approved': {'distributed'}, 'distributed': set()},
}


class RecordCreate(BaseModel):
    area: Area
    payload: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='after')
    def validate_payload(self):
        validate_payload(self.area, INITIAL[self.area], self.payload)
        return self


class Transition(BaseModel):
    status: str = Field(min_length=2, max_length=30)
    evidence: dict[str, Any] = Field(default_factory=dict)


class RecordView(BaseModel):
    id: UUID
    area: str
    status: str
    payload: dict[str, Any]
    created_at: datetime
    updated_at: datetime


def validate_payload(area: str, status: str, payload: dict[str, Any]) -> None:
    forbidden = {'caller_id', 'phone_number', 'recording_url', 'narrative', 'reporter_name'}
    if area == 'hotline':
        leaked = forbidden.intersection(payload)
        if leaked:
            raise ValueError(f'hotline operational record cannot contain reporter data: {sorted(leaked)}')
        required = {'provider_call_id', 'reporting_mode', 'language', 'started_at'}
        if missing := required.difference(payload):
            raise ValueError(f'missing hotline fields: {sorted(missing)}')
        if payload['reporting_mode'] not in REPORTING_MODES:
            raise ValueError('invalid reporting_mode')
        if status in {'submitted', 'escalated', 'closed'} and not payload.get('case_id'):
            raise ValueError('submitted hotline calls require case_id from normal intake')
    if area == 'training' and status == 'passed':
        if float(payload.get('score', 0)) < 80 or not payload.get('critical_questions_passed'):
            raise ValueError('training requires score >= 80 and all critical questions passed')
    if area == 'qa' and status == 'approved' and int(payload.get('critical_defects', 0)) != 0:
        raise ValueError('QA cannot be approved with critical defects')
    if area == 'continuity' and status == 'passed':
        required = ('actual_rto_minutes', 'actual_rpo_minutes', 'target_rto_minutes', 'target_rpo_minutes')
        if any(key not in payload for key in required) or not payload.get('restore_verified'):
            raise ValueError('passed drill requires measured RTO/RPO and verified restore')
        if payload['actual_rto_minutes'] > payload['target_rto_minutes'] or payload['actual_rpo_minutes'] > payload['target_rpo_minutes']:
            raise ValueError('drill exceeded RTO/RPO targets')
    if area == 'coverage' and status == 'active':
        if not payload.get('primary_subject') or not payload.get('secondary_subject'):
            raise ValueError('active coverage requires primary and secondary responders')
        if payload['primary_subject'] == payload['secondary_subject']:
            raise ValueError('primary and secondary responders must differ')
    if area == 'awareness' and status == 'published' and not payload.get('approved_by'):
        raise ValueError('published awareness material requires approval')
    if area == 'reporting' and status in {'generated', 'approved', 'distributed'}:
        if not payload.get('period_start') or not payload.get('period_end'):
            raise ValueError('generated report requires a reporting period')


def transition_allowed(area: str, current: str, target: str) -> bool:
    return target in TRANSITIONS.get(area, {}).get(current, set())


def _view(row: OperationalRecord) -> RecordView:
    return RecordView(id=row.id, area=row.area, status=row.status, payload=row.payload, created_at=row.created_at, updated_at=row.updated_at)


@router.post('', response_model=RecordView, status_code=201)
async def create_record(body: RecordCreate, context: ContextDep, database: AsyncSession = Depends(session), x_idempotency_key: str = Header(min_length=8, max_length=160)):
    await set_tenant(database, context.tenant_id)
    existing = await database.scalar(select(OperationalRecord).where(OperationalRecord.tenant_id == context.tenant_id, OperationalRecord.area == body.area, OperationalRecord.idempotency_key == x_idempotency_key))
    if existing: return _view(existing)
    row = OperationalRecord(tenant_id=context.tenant_id, area=body.area, status=INITIAL[body.area], idempotency_key=x_idempotency_key, payload=body.payload, created_by=context.subject_id)
    database.add(row)
    database.add(OutboxEvent(tenant_id=context.tenant_id, event_type='operations.record.changed.v1', subject=f'operations/{row.id}', payload={'record_id': str(row.id), 'area': body.area, 'previous_status': 'none', 'status': row.status}))
    await database.commit(); await database.refresh(row)
    return _view(row)


@router.post('/{record_id}/transition', response_model=RecordView)
async def transition_record(record_id: UUID, body: Transition, context: ContextDep, database: AsyncSession = Depends(session)):
    await set_tenant(database, context.tenant_id)
    row = await database.get(OperationalRecord, record_id)
    if row is None or row.tenant_id != context.tenant_id: raise HTTPException(404, 'Not found')
    if not transition_allowed(row.area, row.status, body.status): raise HTTPException(409, f'invalid transition {row.status} -> {body.status}')
    merged = {**row.payload, **body.evidence}
    try: validate_payload(row.area, body.status, merged)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    previous, row.status, row.payload = row.status, body.status, merged
    database.add(OutboxEvent(tenant_id=context.tenant_id, event_type='operations.record.changed.v1', subject=f'operations/{row.id}', payload={'record_id': str(row.id), 'area': row.area, 'previous_status': previous, 'status': body.status}))
    await database.commit(); await database.refresh(row)
    return _view(row)


@router.get('', response_model=list[RecordView])
async def list_records(context: ContextDep, database: AsyncSession = Depends(session), area: Area | None = None, status: str | None = None, limit: int = Query(100, ge=1, le=500)):
    await set_tenant(database, context.tenant_id)
    query = select(OperationalRecord).where(OperationalRecord.tenant_id == context.tenant_id)
    if area: query = query.where(OperationalRecord.area == area)
    if status: query = query.where(OperationalRecord.status == status)
    rows = await database.scalars(query.order_by(OperationalRecord.created_at.desc()).limit(limit))
    return [_view(row) for row in rows]


@router.get('/coverage/status')
async def coverage_status(context: ContextDep, database: AsyncSession = Depends(session)):
    await set_tenant(database, context.tenant_id)
    active = list(await database.scalars(select(OperationalRecord).where(OperationalRecord.tenant_id == context.tenant_id, OperationalRecord.area == 'coverage', OperationalRecord.status == 'active')))
    return {'covered': bool(active), 'active_shifts': len(active), 'launch_ready': bool(active)}
