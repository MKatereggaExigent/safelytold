from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import JSON, Boolean, String, UniqueConstraint, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4

from safelytold_common.auth import SuperuserDep
from safelytold_common.db import Base, session
from safelytold_common.reporter_access import create_reporter_access

from .admin import Tenant

router = APIRouter(prefix='/v1/reporting', tags=['public-reporting'])


class ReportingChannel(Base):
    __tablename__ = 'reporting_channels'
    __table_args__ = (UniqueConstraint('tenant_id', 'slug', name='uq_reporting_channel_tenant_slug'),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    slug: Mapped[str] = mapped_column(String(64))
    display_name: Mapped[str] = mapped_column(String(160))
    audience: Mapped[str] = mapped_column(String(40), default='general-public')
    eligibility_requirement: Mapped[str] = mapped_column(String(40), default='none')
    allowed_modes: Mapped[list[str]] = mapped_column(JSON, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class ChannelPolicy(BaseModel):
    slug: str = Field(pattern='^(open|workforce|contractor|supplier|former-employee|referral)$')
    display_name: str = Field(min_length=2, max_length=160)
    audience: str = Field(pattern='^(general-public|workforce|contractors|suppliers|former-employees|invited)$')
    eligibility_requirement: str = Field(pattern='^(none|privacy-pass|anonymous-credential|invitation|access-code|sso-confidential)$')
    allowed_modes: list[str] = Field(min_length=1)
    enabled: bool = True


def _channel_view(value: ReportingChannel) -> dict:
    return {
        'id': str(value.id), 'tenant_id': str(value.tenant_id), 'slug': value.slug,
        'display_name': value.display_name, 'audience': value.audience,
        'eligibility_requirement': value.eligibility_requirement,
        'allowed_modes': value.allowed_modes, 'enabled': value.enabled,
    }


@router.put('/admin/tenants/{tenant_id}/channels/{channel_slug}')
async def configure_channel(tenant_id: UUID, channel_slug: str, body: ChannelPolicy,
                            _: SuperuserDep, database: AsyncSession = Depends(session)) -> dict:
    tenant = await database.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(404, 'Tenant not found')
    if body.slug != channel_slug:
        raise HTTPException(422, 'Channel slug must match the URL')
    allowed = {'anonymous', 'verified_anonymous', 'confidential', 'identified'}
    if not set(body.allowed_modes).issubset(allowed):
        raise HTTPException(422, 'Unsupported reporting mode')
    if 'verified_anonymous' in body.allowed_modes and body.eligibility_requirement not in {'privacy-pass', 'anonymous-credential'}:
        raise HTTPException(422, 'Verified anonymous mode requires an unlinkable eligibility credential')
    value = await database.scalar(select(ReportingChannel).where(
        ReportingChannel.tenant_id == tenant_id, ReportingChannel.slug == channel_slug,
    ))
    if value is None:
        value = ReportingChannel(tenant_id=tenant_id, slug=channel_slug)
        database.add(value)
    value.display_name = body.display_name
    value.audience = body.audience
    value.eligibility_requirement = body.eligibility_requirement
    value.allowed_modes = body.allowed_modes
    value.enabled = body.enabled
    await database.commit()
    await database.refresh(value)
    return _channel_view(value)


@router.get('/admin/tenants/{tenant_id}/channels')
async def list_channels(tenant_id: UUID, _: SuperuserDep, database: AsyncSession = Depends(session)) -> list[dict]:
    rows = list(await database.scalars(select(ReportingChannel).where(ReportingChannel.tenant_id == tenant_id)))
    return [_channel_view(value) for value in rows]


class ReportingEntry(BaseModel):
    organisation: str = Field(min_length=2, max_length=64)
    channel: str = Field(default='open', pattern='^(open|workforce|contractor|supplier|former-employee|referral)$')


@router.post('/resolve')
async def resolve_reporting_entry(body: ReportingEntry, database: AsyncSession = Depends(session)) -> dict:
    slug = body.organisation.strip().lower()
    tenant = await database.scalar(select(Tenant).where(Tenant.slug == slug))
    if tenant is None:
        # Organisation codes are printed and typed by people. Accept omission of
        # display hyphens while continuing to bind the report to the canonical,
        # server-owned tenant slug.
        compact_slug = slug.replace('-', '')
        tenant = await database.scalar(
            select(Tenant).where(func.replace(Tenant.slug, '-', '') == compact_slug)
        )
    if tenant is None or tenant.status != 'active':
        raise HTTPException(404, 'Reporting organisation not found or not active')
    policy = await database.scalar(select(ReportingChannel).where(
        ReportingChannel.tenant_id == tenant.id, ReportingChannel.slug == body.channel,
    ))
    if policy is None:
        if body.channel != 'open':
            raise HTTPException(404, 'Reporting channel not found')
        modes = ['anonymous', 'confidential', 'identified']
        eligibility_requirement = 'none'
        channel_name = 'Open reporting'
    else:
        if not policy.enabled:
            raise HTTPException(404, 'Reporting channel is not active')
        modes = policy.allowed_modes
        eligibility_requirement = policy.eligibility_requirement
        channel_name = policy.display_name
    if eligibility_requirement != 'none':
        raise HTTPException(403, 'This reporting channel requires a privacy-preserving eligibility credential')
    expires_at = datetime.now(UTC) + timedelta(minutes=30)
    token = create_reporter_access(
        tenant_id=tenant.id, tenant_slug=tenant.slug, tenant_name=tenant.display_name,
        channel=body.channel, modes=modes, eligibility_class='open_unverified',
    )
    return {
        'organisation': {'slug': tenant.slug, 'display_name': tenant.display_name},
        'channel': body.channel, 'channel_name': channel_name, 'eligibility_class': 'open_unverified',
        'allowed_modes': modes, 'reporting_session': token, 'expires_at': expires_at.isoformat(),
    }
