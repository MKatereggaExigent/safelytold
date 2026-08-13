from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, JSON, String, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from safelytold_common.auth import ContextDep
from safelytold_common.db import Base, OutboxEvent, TenantMixin, session, set_tenant
from safelytold_common.service import create_app

router = APIRouter(prefix='/v1/investigations', tags=['investigations'])


class Investigation(TenantMixin, Base):
    __tablename__ = 'investigations'
    case_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    scope: Mapped[str] = mapped_column(String(1000))
    issue_ids: Mapped[list[str]] = mapped_column(JSON)
    evidence_sources: Mapped[list[str]] = mapped_column(JSON)
    milestones: Mapped[list[dict]] = mapped_column(JSON)


class Finding(TenantMixin, Base):
    __tablename__ = 'investigation_findings'
    investigation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    allegation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    category: Mapped[str] = mapped_column(String(24))
    rationale_ref: Mapped[str] = mapped_column(String(500))
    evidence_ids: Mapped[list[str]] = mapped_column(JSON)
    contrary_evidence_ids: Mapped[list[str]] = mapped_column(JSON)
    limitations: Mapped[list[str]] = mapped_column(JSON)
    reviewer_approval_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))


class Appeal(TenantMixin, Base):
    __tablename__ = 'investigation_appeals'
    investigation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    grounds_ref: Mapped[str] = mapped_column(String(500))
    reviewer_ref: Mapped[str] = mapped_column(String(160))
    additional_evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PlanCreate(BaseModel):
    case_id: UUID; issue_ids: list[UUID] = Field(min_length=1); scope: str = Field(min_length=10, max_length=1000)
    evidence_sources: list[str] = Field(default_factory=list); milestones: list[dict] = Field(default_factory=list)


class FindingCreate(BaseModel):
    allegation_id: UUID; category: str = Field(pattern='^(substantiated|unsubstantiated|inconclusive|referred)$')
    rationale_ref: str = Field(min_length=3, max_length=500); evidence_ids: list[UUID] = Field(default_factory=list)
    contrary_evidence_ids: list[UUID] = Field(default_factory=list); limitations: list[str] = Field(default_factory=list)


class Review(BaseModel): reviewer_approval_id: UUID
class AppealCreate(BaseModel):
    grounds_ref: str = Field(min_length=3, max_length=500); reviewer_ref: str = Field(min_length=1, max_length=160)
    additional_evidence_ids: list[UUID] = Field(default_factory=list)
class AppealDecision(BaseModel): status: str = Field(pattern='^(upheld|varied|dismissed)$')


def role(context, allowed: set[str]):
    if not context.roles.intersection(allowed | {'platform_super_admin'}): raise HTTPException(403, 'Insufficient investigation role')


async def owned(db, model, row_id, tenant_id):
    row = await db.get(model, row_id)
    if row is None or row.tenant_id != tenant_id: raise HTTPException(404, 'Not found')
    return row


def event(db, row, event_type, **payload):
    db.add(OutboxEvent(tenant_id=row.tenant_id, event_type=event_type, subject=f'investigation/{row.id}', payload={'investigation_id': str(row.id), 'case_id': str(row.case_id) if hasattr(row, 'case_id') else None, **payload}))


@router.post('', status_code=201)
async def plan(body: PlanCreate, context: ContextDep, database: AsyncSession = Depends(session)):
    role(context, {'investigator', 'case_manager'}); await set_tenant(database, context.tenant_id)
    row = Investigation(tenant_id=context.tenant_id, status='planned', case_id=body.case_id, scope=body.scope,
        issue_ids=[str(x) for x in body.issue_ids], evidence_sources=body.evidence_sources, milestones=body.milestones)
    database.add(row); await database.flush(); event(database, row, 'investigation.planned.v1')
    await database.commit(); await database.refresh(row); return row


@router.get('/case/{case_id}')
async def for_case(case_id: UUID, context: ContextDep, database: AsyncSession = Depends(session)):
    await set_tenant(database, context.tenant_id)
    return list(await database.scalars(select(Investigation).where(Investigation.tenant_id == context.tenant_id, Investigation.case_id == case_id)))


@router.post('/{investigation_id}/findings', status_code=201)
async def finding(investigation_id: UUID, body: FindingCreate, context: ContextDep, database: AsyncSession = Depends(session)):
    role(context, {'investigator'}); await set_tenant(database, context.tenant_id)
    investigation = await owned(database, Investigation, investigation_id, context.tenant_id)
    if investigation.status in {'closed', 'appealed'}: raise HTTPException(409, 'Investigation no longer accepts findings')
    row = Finding(tenant_id=context.tenant_id, investigation_id=investigation_id, status='draft', allegation_id=body.allegation_id,
        category=body.category, rationale_ref=body.rationale_ref, evidence_ids=[str(x) for x in body.evidence_ids],
        contrary_evidence_ids=[str(x) for x in body.contrary_evidence_ids], limitations=body.limitations)
    database.add(row); await database.commit(); await database.refresh(row); return row


@router.post('/{investigation_id}/findings/{finding_id}/review')
async def review(investigation_id: UUID, finding_id: UUID, body: Review, context: ContextDep, database: AsyncSession = Depends(session)):
    role(context, {'reviewer'}); await set_tenant(database, context.tenant_id)
    investigation = await owned(database, Investigation, investigation_id, context.tenant_id)
    row = await owned(database, Finding, finding_id, context.tenant_id)
    if row.investigation_id != investigation_id: raise HTTPException(404, 'Not found')
    row.reviewer_approval_id = body.reviewer_approval_id; row.status = 'approved'
    event(database, investigation, 'investigation.finding_approved.v1', finding_id=str(row.id), finding_status=row.category)
    await database.commit(); return row


@router.post('/{investigation_id}/appeals', status_code=201)
async def appeal(investigation_id: UUID, body: AppealCreate, context: ContextDep, database: AsyncSession = Depends(session)):
    role(context, {'case_manager', 'reviewer'}); await set_tenant(database, context.tenant_id)
    investigation = await owned(database, Investigation, investigation_id, context.tenant_id)
    approved = list(await database.scalars(select(Finding).where(Finding.tenant_id == context.tenant_id, Finding.investigation_id == investigation_id, Finding.status == 'approved')))
    if not approved: raise HTTPException(409, 'An appeal requires at least one approved finding')
    row = Appeal(tenant_id=context.tenant_id, investigation_id=investigation_id, status='open', grounds_ref=body.grounds_ref,
        reviewer_ref=body.reviewer_ref, additional_evidence_ids=[str(x) for x in body.additional_evidence_ids])
    investigation.status = 'appealed'; database.add(row); await database.commit(); await database.refresh(row); return row


@router.post('/{investigation_id}/appeals/{appeal_id}/decision')
async def decide_appeal(investigation_id: UUID, appeal_id: UUID, body: AppealDecision, context: ContextDep, database: AsyncSession = Depends(session)):
    role(context, {'reviewer', 'decision_maker'}); await set_tenant(database, context.tenant_id)
    investigation = await owned(database, Investigation, investigation_id, context.tenant_id)
    row = await owned(database, Appeal, appeal_id, context.tenant_id)
    if row.investigation_id != investigation_id or row.status != 'open': raise HTTPException(409, 'Appeal is not open for decision')
    row.status = body.status; row.decided_at = datetime.now(UTC); investigation.status = 'closed'
    event(database, investigation, 'investigation.appeal_decided.v1', appeal_id=str(row.id), appeal_decision=row.status)
    await database.commit(); return row


app = create_app('Investigation Service', 'Investigation plans, evidence-balanced findings, independent review and appeals.', [router])
