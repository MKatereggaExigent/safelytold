from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import DateTime, JSON, String, UniqueConstraint, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from safelytold_common.auth import ContextDep
from safelytold_common.db import Base, OutboxEvent, TenantMixin, session, set_tenant
from safelytold_common.service import create_app
from safelytold_common.taxonomy import validate_concern_categories

router = APIRouter(prefix='/v1/cases', tags=['cases'])
CASE_TRANSITIONS = {
    'unverified': {'triage'}, 'triage': {'open', 'referred', 'closed'},
    'open': {'investigating', 'on_hold', 'closed'},
    'investigating': {'decision_pending', 'on_hold', 'closed'},
    'on_hold': {'open', 'investigating', 'closed'},
    'decision_pending': {'closed', 'investigating'}, 'referred': {'closed'}, 'closed': set(),
}
ASSIGN_ROLES = {'case_manager', 'investigator', 'reviewer', 'decision_maker'}


class CaseRecord(TenantMixin, Base):
    __tablename__ = 'cases'
    __table_args__ = (UniqueConstraint('tenant_id', 'public_reference', name='uq_case_reference'),)
    public_reference: Mapped[str] = mapped_column(String(32), index=True)
    jurisdiction_code: Mapped[str] = mapped_column(String(12))
    severity_band: Mapped[str] = mapped_column(String(20))
    workflow_id: Mapped[str] = mapped_column(String(80))
    policy_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AllegationRecord(TenantMixin, Base):
    __tablename__ = 'case_allegations'
    case_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    taxonomy_code: Mapped[str] = mapped_column(String(80), index=True)


class ConflictRecord(TenantMixin, Base):
    __tablename__ = 'case_conflict_checks'
    case_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    candidate_subject_id: Mapped[str] = mapped_column(String(160))
    conflicts: Mapped[list[str]] = mapped_column(JSON, default=list)
    decision: Mapped[str] = mapped_column(String(20))
    reviewed_by: Mapped[str] = mapped_column(String(160))


class AssignmentRecord(TenantMixin, Base):
    __tablename__ = 'case_assignments'
    case_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    subject_id: Mapped[str] = mapped_column(String(160))
    role: Mapped[str] = mapped_column(String(40))
    purpose: Mapped[str] = mapped_column(String(240))
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    conflict_check_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))


class CaseCreate(BaseModel):
    jurisdiction_code: str = Field(min_length=2, max_length=12)
    severity_band: str = Field(pattern='^(low|medium|high|critical)$')
    workflow_id: str = Field(min_length=2, max_length=80)
    policy_version_id: UUID


class Transition(BaseModel):
    status: str
    reason: str = Field(min_length=3, max_length=500)


class AllegationCreate(BaseModel):
    taxonomy_code: str = Field(min_length=2, max_length=80)

    @field_validator('taxonomy_code')
    @classmethod
    def validate_taxonomy_code(cls, value: str) -> str:
        return validate_concern_categories([value])[0]


class ConflictCreate(BaseModel):
    candidate_subject_id: str = Field(min_length=1, max_length=160)
    conflicts: list[str] = Field(default_factory=list, max_length=50)
    decision: str = Field(pattern='^(clear|conflicted)$')


class AssignmentCreate(BaseModel):
    subject_id: str = Field(min_length=1, max_length=160)
    role: str
    purpose: str = Field(min_length=3, max_length=240)
    valid_until: datetime
    conflict_check_id: UUID


def require_role(context, allowed: set[str]) -> None:
    if not context.roles.intersection(allowed | {'platform_super_admin'}):
        raise HTTPException(403, 'Insufficient case-management role')


def ensure_transition(current: str, target: str) -> None:
    if target not in CASE_TRANSITIONS.get(current, set()):
        raise HTTPException(409, f'Invalid case transition: {current} -> {target}')


async def owned(database: AsyncSession, model, record_id: UUID, tenant_id: UUID):
    row = await database.get(model, record_id)
    if row is None or row.tenant_id != tenant_id:
        raise HTTPException(404, 'Not found')
    return row


def emit(database: AsyncSession, row: CaseRecord, event_type: str, **payload) -> None:
    database.add(OutboxEvent(tenant_id=row.tenant_id, event_type=event_type,
        subject=f'case/{row.id}', payload={'case_id': str(row.id), **payload}))


@router.post('', status_code=201)
async def create_case(body: CaseCreate, context: ContextDep, database: AsyncSession = Depends(session)):
    require_role(context, {'case_manager'})
    await set_tenant(database, context.tenant_id)
    reference = f'ST-{datetime.now(UTC):%Y%m%d}-{uuid4().hex[:8].upper()}'
    row = CaseRecord(tenant_id=context.tenant_id, public_reference=reference, status='unverified', **body.model_dump())
    database.add(row); await database.flush(); emit(database, row, 'case.created.v1', status=row.status)
    await database.commit(); await database.refresh(row)
    return row


@router.get('')
async def list_cases(context: ContextDep, database: AsyncSession = Depends(session), status: str | None = None, limit: int = Query(100, ge=1, le=500)):
    await set_tenant(database, context.tenant_id)
    query = select(CaseRecord).where(CaseRecord.tenant_id == context.tenant_id)
    if status: query = query.where(CaseRecord.status == status)
    return list(await database.scalars(query.order_by(CaseRecord.created_at.desc()).limit(limit)))


@router.get('/{case_id}')
async def get_case(case_id: UUID, context: ContextDep, database: AsyncSession = Depends(session)):
    await set_tenant(database, context.tenant_id)
    return await owned(database, CaseRecord, case_id, context.tenant_id)


@router.post('/{case_id}/transitions')
async def transition(case_id: UUID, body: Transition, context: ContextDep, database: AsyncSession = Depends(session)):
    require_role(context, {'case_manager', 'decision_maker'})
    await set_tenant(database, context.tenant_id); row = await owned(database, CaseRecord, case_id, context.tenant_id)
    ensure_transition(row.status, body.status); previous = row.status; row.status = body.status
    if body.status == 'closed': row.closed_at = datetime.now(UTC)
    emit(database, row, 'case.status_changed.v1', previous_status=previous, status=row.status, reason=body.reason, actor=context.subject_id)
    await database.commit(); return row


@router.post('/{case_id}/allegations', status_code=201)
async def add_allegation(case_id: UUID, body: AllegationCreate, context: ContextDep, database: AsyncSession = Depends(session)):
    require_role(context, {'case_manager', 'investigator'}); await set_tenant(database, context.tenant_id)
    case = await owned(database, CaseRecord, case_id, context.tenant_id)
    if case.status == 'closed': raise HTTPException(409, 'Closed cases cannot be changed')
    row = AllegationRecord(tenant_id=context.tenant_id, case_id=case_id, taxonomy_code=body.taxonomy_code, status='under_assessment')
    database.add(row); await database.flush(); emit(database, case, 'case.allegation_added.v1', allegation_id=str(row.id), taxonomy_code=row.taxonomy_code)
    await database.commit(); await database.refresh(row); return row


@router.post('/{case_id}/conflict-checks', status_code=201)
async def conflict_check(case_id: UUID, body: ConflictCreate, context: ContextDep, database: AsyncSession = Depends(session)):
    require_role(context, {'case_manager', 'reviewer'}); await set_tenant(database, context.tenant_id)
    await owned(database, CaseRecord, case_id, context.tenant_id)
    if body.decision == 'clear' and body.conflicts: raise HTTPException(422, 'A clear decision cannot contain conflicts')
    row = ConflictRecord(tenant_id=context.tenant_id, case_id=case_id, reviewed_by=context.subject_id, **body.model_dump())
    database.add(row); await database.commit(); await database.refresh(row); return row


@router.post('/{case_id}/assignments', status_code=201)
async def assign(case_id: UUID, body: AssignmentCreate, context: ContextDep, database: AsyncSession = Depends(session)):
    require_role(context, {'case_manager'}); await set_tenant(database, context.tenant_id)
    case = await owned(database, CaseRecord, case_id, context.tenant_id)
    check = await owned(database, ConflictRecord, body.conflict_check_id, context.tenant_id)
    if check.case_id != case_id or check.candidate_subject_id != body.subject_id or check.decision != 'clear':
        raise HTTPException(409, 'Assignment requires a matching clear conflict check')
    if body.role not in ASSIGN_ROLES or body.valid_until <= datetime.now(UTC): raise HTTPException(422, 'Invalid role or expiry')
    row = AssignmentRecord(tenant_id=context.tenant_id, case_id=case_id, **body.model_dump())
    database.add(row); await database.flush(); emit(database, case, 'case.assignment_changed.v1', assignment_id=str(row.id), assignee_role=row.role)
    await database.commit(); await database.refresh(row); return row


app = create_app('Case Service', 'Tenant-isolated case triage, allegations, conflict checks, assignments and lifecycle.', [router])
