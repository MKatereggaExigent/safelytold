from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from safelytold_common.auth import SuperuserDep
from safelytold_common.db import session, set_tenant
from safelytold_common.messaging import NeutralMessage, SendStatus

from . import templates as template_store
from .crypto import encrypt_credential
from .notify import get_provider_for_tenant, render_neutral

admin_router = APIRouter(prefix='/v1/admin', tags=['admin'])

DELIVERY_MODES = ('tenant_smtp', 'datasqan_relay')


class EmailSettingsBody(BaseModel):
    delivery_mode: Literal['tenant_smtp', 'datasqan_relay'] = 'datasqan_relay'
    smtp_host: str | None = Field(default=None, max_length=255)
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = Field(default=None, max_length=320)
    smtp_password: str | None = Field(default=None, max_length=256)
    smtp_use_tls: bool = True
    from_address: EmailStr | None = None
    default_locale: str = Field(default='en', min_length=2, max_length=10)


class EmailSettingsView(BaseModel):
    tenant_id: UUID
    delivery_mode: str
    smtp_host: str | None
    smtp_port: int
    smtp_username: str | None
    smtp_use_tls: bool
    from_address: str | None
    default_locale: str
    has_credentials: bool
    verification_status: str
    verification_detail: str | None
    last_test_sent_at: datetime | None


class TestSendBody(BaseModel):
    recipient: EmailStr | None = None


class TemplateOverrideBody(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=2000)


class TemplateOverrideView(BaseModel):
    id: UUID
    tenant_id: UUID
    template_code: str
    locale: str
    subject: str
    body: str


def _settings_view(row) -> EmailSettingsView:
    return EmailSettingsView(
        tenant_id=row.tenant_id,
        delivery_mode=row.delivery_mode,
        smtp_host=row.smtp_host,
        smtp_port=row.smtp_port,
        smtp_username=row.smtp_username,
        smtp_use_tls=row.smtp_use_tls,
        from_address=row.from_address,
        default_locale=row.default_locale,
        has_credentials=bool(row.smtp_password_encrypted),
        verification_status=row.verification_status,
        verification_detail=row.verification_detail,
        last_test_sent_at=row.last_test_sent_at,
    )


@admin_router.get('/email-settings/{tenant_id}', response_model=EmailSettingsView)
async def get_email_settings(tenant_id: UUID, _: SuperuserDep, database: AsyncSession = Depends(session)) -> EmailSettingsView:
    from .main import TenantEmailSettings

    await set_tenant(database, tenant_id)
    row = await database.get(TenantEmailSettings, tenant_id)
    if row is None:
        return EmailSettingsView(
            tenant_id=tenant_id, delivery_mode='datasqan_relay', smtp_port=587,
            smtp_host=None, smtp_username=None, smtp_use_tls=True,
            from_address=None, default_locale='en', has_credentials=False,
            verification_status='unverified', verification_detail=None,
            last_test_sent_at=None,
        )
    return _settings_view(row)


@admin_router.put('/email-settings/{tenant_id}', response_model=EmailSettingsView)
async def upsert_email_settings(
    tenant_id: UUID, body: EmailSettingsBody, _: SuperuserDep, database: AsyncSession = Depends(session)
) -> EmailSettingsView:
    from .main import TenantEmailSettings

    if body.delivery_mode == 'tenant_smtp' and not body.smtp_host:
        raise HTTPException(422, 'smtp_host is required for tenant_smtp delivery')
    if body.delivery_mode == 'datasqan_relay' and not body.from_address:
        raise HTTPException(422, 'from_address is required for datasqan_relay delivery')
    await set_tenant(database, tenant_id)
    row = await database.get(TenantEmailSettings, tenant_id)
    if row is None:
        row = TenantEmailSettings(tenant_id=tenant_id)
        database.add(row)
    row.delivery_mode = body.delivery_mode
    row.smtp_host = body.smtp_host
    row.smtp_port = body.smtp_port
    row.smtp_username = body.smtp_username
    if body.smtp_password is not None:
        row.smtp_password_encrypted = encrypt_credential(body.smtp_password)
    row.smtp_use_tls = body.smtp_use_tls
    row.from_address = body.from_address
    row.default_locale = body.default_locale
    await database.commit()
    await database.refresh(row)
    return _settings_view(row)


@admin_router.post('/email-settings/{tenant_id}/test', response_model=EmailSettingsView)
async def test_email_settings(
    tenant_id: UUID, body: TestSendBody, superuser: SuperuserDep, database: AsyncSession = Depends(session)
) -> EmailSettingsView:
    """Send a neutral connectivity test through the tenant's configured provider."""
    from .main import TenantEmailSettings

    await set_tenant(database, tenant_id)
    row = await database.get(TenantEmailSettings, tenant_id)
    if row is None:
        raise HTTPException(404, 'No email settings configured for this tenant')
    recipient = (body.recipient or superuser.email or '').strip()
    if not recipient:
        raise HTTPException(422, 'No recipient available; provide one or log in with a verified email')
    subject, body_text = render_neutral('mailbox_nudge_v1', row.default_locale)
    provider = await get_provider_for_tenant(tenant_id, database)
    result = await provider.send(
        NeutralMessage(
            destination_ref=recipient,
            subject=f'{subject} - outbound test',
            body=body_text + '\n\nThis is a connectivity test from the SafelyTold platform.',
            template_code='mailbox_nudge_v1',
            locale=row.default_locale,
            correlation_id=UUID('00000000-0000-0000-0000-000000000000'),
            tenant_id=tenant_id,
        )
    )
    row.last_test_sent_at = datetime.now(UTC)
    if result.status == SendStatus.SENT:
        row.verification_status = 'verified'
        row.verification_detail = None
    else:
        row.verification_status = 'failed'
        row.verification_detail = result.error or 'Sending failed'
    await database.commit()
    await database.refresh(row)
    return _settings_view(row)


@admin_router.get('/templates/{tenant_id}', response_model=list[TemplateOverrideView])
async def list_template_overrides(tenant_id: UUID, _: SuperuserDep, database: AsyncSession = Depends(session)) -> list[TemplateOverrideView]:
    from .main import TenantTemplateOverride

    await set_tenant(database, tenant_id)
    rows = list(
        await database.scalars(
            select(TenantTemplateOverride)
            .where(TenantTemplateOverride.tenant_id == tenant_id)
            .order_by(TenantTemplateOverride.template_code, TenantTemplateOverride.locale)
        )
    )
    return [
        TemplateOverrideView(
            id=r.id, tenant_id=r.tenant_id, template_code=r.template_code, locale=r.locale, subject=r.subject, body=r.body
        )
        for r in rows
    ]


@admin_router.put('/templates/{tenant_id}/{template_code}/{locale}', response_model=TemplateOverrideView)
async def upsert_template_override(
    tenant_id: UUID,
    template_code: str,
    locale: str,
    body: TemplateOverrideBody,
    _: SuperuserDep,
    database: AsyncSession = Depends(session),
) -> TemplateOverrideView:
    from .main import TenantTemplateOverride

    if template_code not in template_store.list_templates():
        raise HTTPException(422, f'Unknown template code: {template_code}')
    if locale not in template_store.list_locales():
        raise HTTPException(422, f'Unknown locale: {locale}')
    try:
        template_store.assert_neutral(body.subject, body.body)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    await set_tenant(database, tenant_id)
    override = await database.scalar(
        select(TenantTemplateOverride).where(
            TenantTemplateOverride.tenant_id == tenant_id,
            TenantTemplateOverride.template_code == template_code,
            TenantTemplateOverride.locale == locale,
        )
    )
    if override is None:
        override = TenantTemplateOverride(
            tenant_id=tenant_id, template_code=template_code, locale=locale, subject=body.subject, body=body.body
        )
        database.add(override)
    else:
        override.subject = body.subject
        override.body = body.body
    await database.commit()
    await database.refresh(override)
    return TemplateOverrideView(
        id=override.id,
        tenant_id=override.tenant_id,
        template_code=override.template_code,
        locale=override.locale,
        subject=override.subject,
        body=override.body,
    )


@admin_router.delete('/templates/{tenant_id}/{template_code}/{locale}', status_code=204)
async def delete_template_override(
    tenant_id: UUID,
    template_code: str,
    locale: str,
    _: SuperuserDep,
    database: AsyncSession = Depends(session),
) -> None:
    from .main import TenantTemplateOverride

    await set_tenant(database, tenant_id)
    override = await database.scalar(
        select(TenantTemplateOverride).where(
            TenantTemplateOverride.tenant_id == tenant_id,
            TenantTemplateOverride.template_code == template_code,
            TenantTemplateOverride.locale == locale,
        )
    )
    if override is not None:
        await database.delete(override)
        await database.commit()
