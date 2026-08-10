from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from safelytold_common.messaging import (
    MessagingConfig,
    MessagingProvider,
    NeutralMessage,
    ProviderName,
    SMTPConfig,
    SMTPProvider,
    SendStatus,
    get_provider,
)

from . import templates as template_store
from .crypto import decrypt_credential

if TYPE_CHECKING:
    from .main import NotificationDelivery, NotificationRequest


def render_neutral(template_code: str, locale: str) -> tuple[str, str]:
    """Render a neutral template (subject, body). Raises on unknown code or unsafe text."""
    return (
        template_store.render_subject(template_code, locale),
        template_store.render_body(template_code, locale),
    )


async def render_for(tenant_id: UUID | None, template_code: str, locale: str, database: AsyncSession) -> tuple[str, str]:
    """Render a template honouring an optional per-tenant neutral override.

    A tenant override, when present, must pass the same neutrality contract as
    the global templates. Falls back to the global store otherwise.
    """
    if tenant_id is not None:
        from .main import TenantTemplateOverride

        override = await database.scalar(
            select(TenantTemplateOverride).where(
                TenantTemplateOverride.tenant_id == tenant_id,
                TenantTemplateOverride.template_code == template_code,
                TenantTemplateOverride.locale == locale,
            )
        )
        if override is not None:
            template_store.assert_neutral(override.subject, override.body)
            return override.subject, override.body
    return render_neutral(template_code, locale)


async def get_provider_for_tenant(tenant_id: UUID, database: AsyncSession) -> MessagingProvider:
    """Resolve the outbound provider for a tenant, falling back to the global
    environment configuration when the tenant has not configured one.

    ``tenant_smtp`` uses the tenant's own relay + credentials.
    ``datasqan_relay`` reuses DataSqan's configured relay but sends under the
    tenant's sender identity.
    """
    from .main import TenantEmailSettings

    row = await database.get(TenantEmailSettings, tenant_id)
    if row is None:
        return get_provider()
    if row.delivery_mode == 'tenant_smtp' and row.smtp_host:
        return SMTPProvider(
            SMTPConfig(
                host=row.smtp_host,
                port=row.smtp_port,
                username=row.smtp_username,
                password=decrypt_credential(row.smtp_password_encrypted) if row.smtp_password_encrypted else None,
                from_address=row.from_address or 'no-reply@invalid.local',
                use_tls=row.smtp_use_tls,
            )
        )
    if row.delivery_mode == 'datasqan_relay' and row.from_address:
        global_cfg = MessagingConfig.from_env()
        if global_cfg.provider == ProviderName.SMTP:
            return SMTPProvider(
                SMTPConfig(
                    host=global_cfg.smtp_host,
                    port=global_cfg.smtp_port,
                    username=global_cfg.smtp_username,
                    password=global_cfg.smtp_password,
                    from_address=row.from_address,
                    use_tls=global_cfg.smtp_use_tls,
                    use_ssl=global_cfg.smtp_use_ssl,
                    require_verified_cert=global_cfg.smtp_require_verified_cert,
                )
            )
    return get_provider()


async def send_attempt(
    row: 'NotificationRequest', database: AsyncSession, provider: MessagingProvider | None = None
) -> 'NotificationDelivery':
    """Render and send a request through the provider; persist the delivery row.

    Returns the persisted delivery. Raises ValueError when the template is
    unknown or non-neutral so callers can mark the request failed.
    """
    from .main import NotificationDelivery

    subject, body = await render_for(row.tenant_id, row.template_code, row.locale, database)
    active_provider = provider or await get_provider_for_tenant(row.tenant_id, database)
    message = NeutralMessage(
        destination_ref=row.destination_ref,
        subject=subject,
        body=body,
        template_code=row.template_code,
        locale=row.locale,
        correlation_id=row.id,
        tenant_id=row.tenant_id,
    )
    result = await active_provider.send(message)
    delivery = NotificationDelivery(
        id=uuid4(),
        request_id=row.id,
        status=result.status.value,
        provider=active_provider.name.value,
        provider_message_id=result.provider_message_id,
        error=result.error,
    )
    database.add(delivery)
    row.last_attempt_at = datetime.now(UTC)
    if result.status == SendStatus.SENT:
        row.attempts += 1
        row.status = 'sent'
        row.last_error = None
    else:
        row.status = 'failed'
        row.last_error = result.error
    await database.flush()
    return delivery
