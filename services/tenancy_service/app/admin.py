from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import JSON, DateTime, String, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from safelytold_common.auth import SuperuserDep
from safelytold_common.db import Base, session

router = APIRouter(prefix='/v1/admin', tags=['admin'])


class Tenant(Base):
    __tablename__ = 'tenants'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    tenancy_tier: Mapped[str] = mapped_column(String(40), default='shared_database')
    home_region: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default='active')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class LegalEntity(Base):
    __tablename__ = 'legal_entities'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    registered_name: Mapped[str] = mapped_column(String(240))
    country_code: Mapped[str] = mapped_column(String(2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class OrganisationalUnit(Base):
    __tablename__ = 'organisational_units'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    parent_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    name: Mapped[str] = mapped_column(String(160))
    unit_type: Mapped[str] = mapped_column(String(60), default='department')
    routing_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class TenantCreate(BaseModel):
    id: UUID | None = None
    slug: str = Field(pattern=r'^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$', max_length=64)
    display_name: str = Field(min_length=2, max_length=200)
    tenancy_tier: str = Field(default='shared_database', pattern='^(shared_database|dedicated_database|dedicated_data_plane|customer_environment)$')
    home_region: str = Field(min_length=2, max_length=40)


class TenantView(BaseModel):
    id: UUID
    slug: str
    display_name: str
    tenancy_tier: str
    home_region: str
    status: str
    created_at: datetime


class LegalEntityCreate(BaseModel):
    registered_name: str = Field(min_length=2, max_length=240)
    country_code: str = Field(pattern=r'^[A-Z]{2}$')


class LegalEntityView(BaseModel):
    id: UUID
    tenant_id: UUID
    registered_name: str
    country_code: str


class OrganisationalUnitCreate(BaseModel):
    parent_id: UUID | None = None
    name: str = Field(min_length=2, max_length=160)
    unit_type: str = Field(default='department', max_length=60)
    routing_tags: list[str] = Field(default_factory=list)


class OrganisationalUnitView(BaseModel):
    id: UUID
    tenant_id: UUID
    parent_id: UUID | None
    name: str
    unit_type: str
    routing_tags: list[str]


def _tenant_view(row: Tenant) -> TenantView:
    return TenantView(
        id=row.id, slug=row.slug, display_name=row.display_name,
        tenancy_tier=row.tenancy_tier, home_region=row.home_region,
        status=row.status, created_at=row.created_at,
    )


async def _load_tenant(tenant_id: UUID, database: AsyncSession) -> Tenant:
    row = await database.get(Tenant, tenant_id)
    if row is None:
        raise HTTPException(404, 'Tenant not found')
    return row


@router.post('/tenants', response_model=TenantView, status_code=201)
async def create_tenant(body: TenantCreate, _: SuperuserDep, database: AsyncSession = Depends(session)) -> TenantView:
    existing = await database.scalar(select(Tenant).where(Tenant.slug == body.slug))
    if existing is not None:
        raise HTTPException(409, f'Tenant slug already in use: {body.slug}')
    row = Tenant(
        id=body.id or uuid4(),
        slug=body.slug,
        display_name=body.display_name,
        tenancy_tier=body.tenancy_tier,
        home_region=body.home_region,
    )
    database.add(row)
    await database.commit()
    await database.refresh(row)
    return _tenant_view(row)


@router.get('/tenants', response_model=list[TenantView])
async def list_tenants(_: SuperuserDep, database: AsyncSession = Depends(session)) -> list[TenantView]:
    rows = list(await database.scalars(select(Tenant).order_by(Tenant.created_at.desc()).limit(500)))
    return [_tenant_view(r) for r in rows]


@router.get('/platform-architecture')
async def platform_architecture(_: SuperuserDep) -> dict[str, object]:
    """Return non-public product architecture to verified platform owners."""
    return {
        'title': 'An integrity reporting and case-management operating system—not merely a hotline.',
        'summary': 'SafelyTold covers prevention, reporting, fair case handling, reporter protection, resolution and accountable organisational learning.',
        'lifecycle': [
            {'stage': 'Before wrongdoing', 'capabilities': ['Policy awareness', 'Culture signals', 'Safe reporting channels']},
            {'stage': 'Report', 'capabilities': ['Anonymous', 'Verified anonymous', 'Confidential', 'Identified']},
            {'stage': 'Triage', 'capabilities': ['Conflict detection', 'Severity assessment', 'Jurisdiction', 'Safeguarding']},
            {'stage': 'Case management', 'capabilities': ['Evidence', 'Investigators', 'Deadlines', 'Escalation', 'Procedural fairness']},
            {'stage': 'Reporter protection', 'capabilities': ['Anonymous follow-up', 'Retaliation monitoring', 'Protection measures']},
            {'stage': 'Resolution', 'capabilities': ['Outcome', 'Remediation', 'Appeal and review', 'Audit trail']},
            {'stage': 'Organisation intelligence', 'capabilities': ['Recurring units and roles', 'Systemic patterns', 'Unresolved risks', 'Case-handling performance', 'Board governance']},
        ],
    }


@router.get('/tenants/{tenant_id}', response_model=TenantView)
async def get_tenant(tenant_id: UUID, _: SuperuserDep, database: AsyncSession = Depends(session)) -> TenantView:
    return _tenant_view(await _load_tenant(tenant_id, database))


@router.post('/tenants/{tenant_id}/legal-entities', response_model=LegalEntityView, status_code=201)
async def add_legal_entity(
    tenant_id: UUID, body: LegalEntityCreate, _: SuperuserDep, database: AsyncSession = Depends(session)
) -> LegalEntityView:
    await _load_tenant(tenant_id, database)
    row = LegalEntity(tenant_id=tenant_id, registered_name=body.registered_name, country_code=body.country_code)
    database.add(row)
    await database.commit()
    await database.refresh(row)
    return LegalEntityView(id=row.id, tenant_id=row.tenant_id, registered_name=row.registered_name, country_code=row.country_code)


@router.get('/tenants/{tenant_id}/legal-entities', response_model=list[LegalEntityView])
async def list_legal_entities(
    tenant_id: UUID, _: SuperuserDep, database: AsyncSession = Depends(session)
) -> list[LegalEntityView]:
    await _load_tenant(tenant_id, database)
    rows = list(await database.scalars(select(LegalEntity).where(LegalEntity.tenant_id == tenant_id)))
    return [LegalEntityView(id=r.id, tenant_id=r.tenant_id, registered_name=r.registered_name, country_code=r.country_code) for r in rows]


@router.post('/tenants/{tenant_id}/organisational-units', response_model=OrganisationalUnitView, status_code=201)
async def add_organisational_unit(
    tenant_id: UUID, body: OrganisationalUnitCreate, _: SuperuserDep, database: AsyncSession = Depends(session)
) -> OrganisationalUnitView:
    await _load_tenant(tenant_id, database)
    if body.parent_id is not None:
        parent = await database.get(OrganisationalUnit, body.parent_id)
        if parent is None or parent.tenant_id != tenant_id:
            raise HTTPException(422, 'parent_id must reference an organisational unit of the same tenant')
    row = OrganisationalUnit(
        tenant_id=tenant_id, parent_id=body.parent_id, name=body.name,
        unit_type=body.unit_type, routing_tags=body.routing_tags,
    )
    database.add(row)
    await database.commit()
    await database.refresh(row)
    return OrganisationalUnitView(
        id=row.id, tenant_id=row.tenant_id, parent_id=row.parent_id,
        name=row.name, unit_type=row.unit_type, routing_tags=row.routing_tags,
    )


@router.get('/tenants/{tenant_id}/organisational-units', response_model=list[OrganisationalUnitView])
async def list_organisational_units(
    tenant_id: UUID, _: SuperuserDep, database: AsyncSession = Depends(session)
) -> list[OrganisationalUnitView]:
    await _load_tenant(tenant_id, database)
    rows = list(
        await database.scalars(
            select(OrganisationalUnit).where(OrganisationalUnit.tenant_id == tenant_id).order_by(OrganisationalUnit.name)
        )
    )
    return [
        OrganisationalUnitView(
            id=r.id, tenant_id=r.tenant_id, parent_id=r.parent_id,
            name=r.name, unit_type=r.unit_type, routing_tags=r.routing_tags,
        )
        for r in rows
    ]
