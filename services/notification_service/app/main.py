from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Boolean, Integer, LargeBinary, String, Text, UniqueConstraint, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from safelytold_common.auth import ContextDep
from safelytold_common.db import Base, session, set_tenant
from safelytold_common.messaging import SendStatus, get_provider
from safelytold_common.service import create_app

from . import templates as template_store
from .admin import admin_router
from .nudge import next_attempt_at, post_send_next_check
from .notify import send_attempt

router = APIRouter(prefix='/v1/notifications', tags=['notifications'])

CHANNELS = {'email'}


class NotificationRequest(Base):
    __tablename__ = 'notification_requests'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    case_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    correlation_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), index=True)
    template_code: Mapped[str] = mapped_column(String(80))
    channel: Mapped[str] = mapped_column(String(20))
    locale: Mapped[str] = mapped_column(String(10))
    destination_ref: Mapped[str] = mapped_column(String(320))
    status: Mapped[str] = mapped_column(String(20), default='pending', index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class NotificationDelivery(Base):
    __tablename__ = 'notification_deliveries'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    status: Mapped[str] = mapped_column(String(20))
    provider: Mapped[str] = mapped_column(String(40))
    provider_message_id: Mapped[str | None] = mapped_column(String(200))
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class TenantEmailSettings(Base):
    """Per-tenant outbound email configuration managed by the superuser console.

    delivery_mode is either ``tenant_smtp`` (the tenant supplied their own
    relay + credentials) or ``datasqan_relay`` (DataSqan's relay sends under the
    tenant's sender identity). SMTP passwords are stored encrypted.
    """

    __tablename__ = 'tenant_email_settings'
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    delivery_mode: Mapped[str] = mapped_column(String(20), default='datasqan_relay')
    smtp_host: Mapped[str | None] = mapped_column(String(255))
    smtp_port: Mapped[int] = mapped_column(Integer, default=587)
    smtp_username: Mapped[str | None] = mapped_column(String(320))
    smtp_password_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    smtp_use_tls: Mapped[bool] = mapped_column(Boolean, default=True)
    from_address: Mapped[str | None] = mapped_column(String(320))
    default_locale: Mapped[str] = mapped_column(String(10), default='en')
    verification_status: Mapped[str] = mapped_column(String(20), default='unverified')
    verification_detail: Mapped[str | None] = mapped_column(Text)
    last_test_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class TenantTemplateOverride(Base):
    __tablename__ = 'tenant_template_overrides'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'template_code', 'locale', name='uq_tenant_template_locale'),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    template_code: Mapped[str] = mapped_column(String(80))
    locale: Mapped[str] = mapped_column(String(10))
    subject: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class NotificationCreate(BaseModel):
    case_id: UUID
    template_code: str = Field(pattern=r'^[a-z0-9_]+$', max_length=80)
    channel: str = Field(default='email', pattern='^email$')
    locale: str = Field(default='en', min_length=2, max_length=10)
    destination_ref: str = Field(min_length=3, max_length=320)
    send_after: datetime | None = None
    correlation_id: UUID | None = None


class NotificationView(BaseModel):
    id: UUID
    tenant_id: UUID
    case_id: UUID
    template_code: str
    channel: str
    locale: str
    destination_ref: str
    status: str
    attempts: int
    next_attempt_at: datetime | None
    last_attempt_at: datetime | None
    last_error: str | None
    created_at: datetime


class DeliveryView(BaseModel):
    id: UUID
    request_id: UUID
    status: str
    provider: str
    provider_message_id: str | None
    error: str | None
    created_at: datetime


class TemplateView(BaseModel):
    code: str
    locales: list[str]


def _view(row: NotificationRequest) -> NotificationView:
    return NotificationView(
        id=row.id,
        tenant_id=row.tenant_id,
        case_id=row.case_id,
        template_code=row.template_code,
        channel=row.channel,
        locale=row.locale,
        destination_ref=row.destination_ref,
        status=row.status,
        attempts=row.attempts,
        next_attempt_at=row.next_attempt_at,
        last_attempt_at=row.last_attempt_at,
        last_error=row.last_error,
        created_at=row.created_at,
    )


async def _load_request(record_id: UUID, context: ContextDep, database: AsyncSession) -> NotificationRequest:
    row = await database.get(NotificationRequest, record_id)
    if row is None or row.tenant_id != context.tenant_id:
        raise HTTPException(404, 'Not found')
    return row


async def _send_now(row: NotificationRequest, database: AsyncSession, provider: Any = None) -> NotificationDelivery:
    """Render the neutral template and send through the configured provider."""
    try:
        delivery = await send_attempt(row, database, provider)
    except (KeyError, ValueError) as exc:
        row.status = 'failed'
        row.last_error = str(exc)
        await database.commit()
        raise HTTPException(422, str(exc)) from exc
    now = datetime.now(UTC)
    if delivery.status == SendStatus.SENT.value:
        row.status = 'sent'
        row.last_error = None
        row.next_attempt_at = post_send_next_check(now, row.attempts)
    else:
        row.status = 'failed'
        row.last_error = delivery.error
        row.next_attempt_at = next_attempt_at(row.attempts, now) if row.attempts == 0 else row.next_attempt_at
    await database.commit()
    await database.refresh(delivery)
    return delivery


@router.get('/templates', response_model=list[TemplateView])
async def list_templates(context: ContextDep) -> list[TemplateView]:
    return [TemplateView(code=code, locales=template_store.list_locales()) for code in template_store.list_templates()]


@router.post('', response_model=NotificationView, status_code=201)
async def create_notification(
    body: NotificationCreate, context: ContextDep, database: AsyncSession = Depends(session)
) -> NotificationView:
    if body.channel not in CHANNELS:
        raise HTTPException(422, f'Unsupported channel: {body.channel}')
    try:
        template_store.render_subject(body.template_code, body.locale)
    except KeyError as exc:
        raise HTTPException(422, f'Unknown template code: {body.template_code}') from exc
    await set_tenant(database, context.tenant_id)
    if body.correlation_id is not None:
        existing = await database.scalar(
            select(NotificationRequest).where(
                NotificationRequest.tenant_id == context.tenant_id,
                NotificationRequest.correlation_id == body.correlation_id,
            )
        )
        if existing is not None:
            return _view(existing)
    row = NotificationRequest(
        tenant_id=context.tenant_id,
        case_id=body.case_id,
        correlation_id=body.correlation_id,
        template_code=body.template_code,
        channel=body.channel,
        locale=body.locale,
        destination_ref=body.destination_ref,
        status='pending',
        next_attempt_at=body.send_after or datetime.now(UTC),
    )
    database.add(row)
    await database.commit()
    await database.refresh(row)
    return _view(row)


@router.get('', response_model=list[NotificationView])
async def list_notifications(
    context: ContextDep,
    database: AsyncSession = Depends(session),
    case_id: UUID | None = None,
    status: str | None = None,
) -> list[NotificationView]:
    await set_tenant(database, context.tenant_id)
    query = select(NotificationRequest).where(NotificationRequest.tenant_id == context.tenant_id)
    if case_id is not None:
        query = query.where(NotificationRequest.case_id == case_id)
    if status is not None:
        query = query.where(NotificationRequest.status == status)
    query = query.order_by(NotificationRequest.created_at.desc()).limit(500)
    return [_view(row) for row in await database.scalars(query)]


@router.get('/{request_id}', response_model=NotificationView)
async def get_notification(
    request_id: UUID, context: ContextDep, database: AsyncSession = Depends(session)
) -> NotificationView:
    return _view(await _load_request(request_id, context, database))


@router.get('/{request_id}/deliveries', response_model=list[DeliveryView])
async def list_deliveries(
    request_id: UUID, context: ContextDep, database: AsyncSession = Depends(session)
) -> list[DeliveryView]:
    await _load_request(request_id, context, database)
    rows = list(
        await database.scalars(
            select(NotificationDelivery).where(NotificationDelivery.request_id == request_id).order_by(NotificationDelivery.created_at)
        )
    )
    return [
        DeliveryView(
            id=r.id, request_id=r.request_id, status=r.status, provider=r.provider,
            provider_message_id=r.provider_message_id, error=r.error, created_at=r.created_at,
        )
        for r in rows
    ]


@router.post('/{request_id}/send', response_model=DeliveryView)
async def send_notification_now(
    request_id: UUID, context: ContextDep, database: AsyncSession = Depends(session)
) -> DeliveryView:
    await set_tenant(database, context.tenant_id)
    row = await _load_request(request_id, context, database)
    return await _send_now(row, database)


app = create_app(
    'Notification Service',
    'Neutral, zero-case-content notifications over pluggable messaging providers.',
    [router, admin_router],
)
