from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, JSON, LargeBinary, String, func, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from safelytold_common.auth import ContextDep
from safelytold_common.db import Base, OutboxEvent, session, set_tenant
from safelytold_common.reporter_auth import ReporterDep
from safelytold_common.service import create_app

from .crypto import decrypt_body, encrypt_body

router = APIRouter(prefix='/v1/mailbox', tags=['mailbox'])


class MailboxMessage(Base):
    __tablename__ = 'mailbox_messages'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), index=True)
    case_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    sender: Mapped[str] = mapped_column(String(32))
    body_encrypted: Mapped[bytes] = mapped_column(LargeBinary)
    attachment_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    read_by: Mapped[str | None] = mapped_column(String(80))


class ConflictChallenge(Base):
    __tablename__ = 'mailbox_conflict_challenges'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), index=True)
    case_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    challenged_assignment_id: Mapped[str | None] = mapped_column(String(80))
    reason_category: Mapped[str] = mapped_column(String(80))
    details: Mapped[str] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(String(40), default='open')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class RetaliationConcern(Base):
    __tablename__ = 'mailbox_retaliation_concerns'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), index=True)
    case_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    risk_band: Mapped[str] = mapped_column(String(40), default='medium')
    details: Mapped[str] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(String(40), default='new')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class SafeContactPreference(Base):
    __tablename__ = 'mailbox_safe_contact_preferences'
    case_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), index=True)
    allowed_channels: Mapped[list[str]] = mapped_column(JSON, default=list)
    prohibited_times: Mapped[list[str]] = mapped_column(JSON, default=list)
    neutral_message_only: Mapped[bool] = mapped_column(default=False)
    destination_ref_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class MessageSend(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    attachment_ids: list[UUID] = Field(default_factory=list)


class MessageView(BaseModel):
    id: UUID
    case_id: UUID
    sender: str
    body: str
    attachment_ids: list[str]
    created_at: datetime
    read_at: datetime | None


class ChallengeCreate(BaseModel):
    challenged_assignment_id: str | None = Field(default=None, max_length=80)
    reason_category: str = Field(min_length=1, max_length=80)
    details: str = Field(min_length=1, max_length=2000)


class ChallengeView(BaseModel):
    id: UUID
    case_id: UUID
    challenged_assignment_id: str | None
    reason_category: str
    details: str
    status: str
    created_at: datetime


class ConcernCreate(BaseModel):
    risk_band: str = Field(default='medium', max_length=40)
    details: str = Field(min_length=1, max_length=2000)


class ConcernView(BaseModel):
    id: UUID
    case_id: UUID
    risk_band: str
    details: str
    status: str
    created_at: datetime


class SafeContactUpdate(BaseModel):
    allowed_channels: list[str] = Field(default_factory=list)
    prohibited_times: list[str] = Field(default_factory=list)
    neutral_message_only: bool = False
    destination_ref: str | None = Field(default=None, max_length=320)


def _view(row: MailboxMessage, body_text: str) -> MessageView:
    return MessageView(
        id=row.id,
        case_id=row.case_id,
        sender=row.sender,
        body=body_text,
        attachment_ids=row.attachment_ids or [],
        created_at=row.created_at,
        read_at=row.read_at,
    )


async def _message_rows(database: AsyncSession, case_id: UUID, sender: str | None = None) -> list[MailboxMessage]:
    query = (
        select(MailboxMessage)
        .where(MailboxMessage.case_id == case_id)
        .order_by(MailboxMessage.created_at.asc(), MailboxMessage.id.asc())
    )
    if sender is not None:
        query = query.where(MailboxMessage.sender == sender)
    return list(await database.scalars(query))


@router.get('/cases/{case_id}/messages', response_model=list[MessageView])
async def list_my_messages(case_id: UUID, reporter: ReporterDep, database: AsyncSession = Depends(session)) -> list[MessageView]:
    if reporter.case_id != case_id:
        raise HTTPException(403, 'Forbidden')
    rows = await _message_rows(database, case_id)
    return [_view(r, decrypt_body(r.body_encrypted).decode('utf-8')) for r in rows]


@router.post('/cases/{case_id}/messages', response_model=MessageView, status_code=201)
async def send_my_message(
    case_id: UUID, body: MessageSend, reporter: ReporterDep, database: AsyncSession = Depends(session)
) -> MessageView:
    if reporter.case_id != case_id:
        raise HTTPException(403, 'Forbidden')
    row = MailboxMessage(
        case_id=case_id,
        tenant_id=reporter.tenant_id,
        sender='reporter',
        body_encrypted=encrypt_body(body.body.encode('utf-8')),
        attachment_ids=[str(a) for a in body.attachment_ids],
    )
    database.add(row)
    await database.flush()
    if row.tenant_id is not None:
        database.add(
            OutboxEvent(
                tenant_id=row.tenant_id,
                event_type='mailbox.message.sent.v1',
                subject=f'mailbox/{row.id}',
                payload={'case_id': str(case_id), 'message_id': str(row.id), 'sender': 'reporter'},
            )
        )
    await database.commit()
    await database.refresh(row)
    return _view(row, body.body)


@router.post('/cases/{case_id}/conflict-challenges', response_model=ChallengeView, status_code=201)
async def challenge_assignment(
    case_id: UUID, body: ChallengeCreate, reporter: ReporterDep, database: AsyncSession = Depends(session)
) -> ChallengeView:
    if reporter.case_id != case_id:
        raise HTTPException(403, 'Forbidden')
    row = ConflictChallenge(
        case_id=case_id,
        tenant_id=reporter.tenant_id,
        challenged_assignment_id=body.challenged_assignment_id,
        reason_category=body.reason_category,
        details=body.details,
    )
    database.add(row)
    await database.commit()
    await database.refresh(row)
    return ChallengeView(
        id=row.id, case_id=row.case_id, challenged_assignment_id=row.challenged_assignment_id,
        reason_category=row.reason_category, details=row.details, status=row.status, created_at=row.created_at,
    )


@router.post('/cases/{case_id}/retaliation-concerns', response_model=ConcernView, status_code=201)
async def report_retaliation_concern(
    case_id: UUID, body: ConcernCreate, reporter: ReporterDep, database: AsyncSession = Depends(session)
) -> ConcernView:
    if reporter.case_id != case_id:
        raise HTTPException(403, 'Forbidden')
    row = RetaliationConcern(case_id=case_id, tenant_id=reporter.tenant_id, risk_band=body.risk_band, details=body.details)
    database.add(row)
    await database.flush()
    if row.tenant_id is not None:
        database.add(
            OutboxEvent(
                tenant_id=row.tenant_id,
                event_type='retaliation.concern_reported.v1',
                subject=f'mailbox/{row.id}',
                payload={
                    'case_id': str(case_id),
                    'concern_id': str(row.id),
                    'risk_band': body.risk_band,
                    'protection_review_required': body.risk_band in {'high', 'critical'},
                },
            )
        )
    await database.commit()
    await database.refresh(row)
    return ConcernView(
        id=row.id, case_id=row.case_id, risk_band=row.risk_band, details=row.details,
        status=row.status, created_at=row.created_at,
    )


@router.get('/cases/{case_id}/safe-contact', response_model=SafeContactUpdate)
async def get_safe_contact(case_id: UUID, reporter: ReporterDep, database: AsyncSession = Depends(session)) -> SafeContactUpdate:
    if reporter.case_id != case_id:
        raise HTTPException(403, 'Forbidden')
    pref = await database.get(SafeContactPreference, case_id)
    if pref is None:
        return SafeContactUpdate()
    return SafeContactUpdate(
        allowed_channels=pref.allowed_channels or [],
        prohibited_times=pref.prohibited_times or [],
        neutral_message_only=pref.neutral_message_only,
        destination_ref=decrypt_body(pref.destination_ref_encrypted).decode('utf-8') if pref.destination_ref_encrypted else None,
    )


@router.put('/cases/{case_id}/safe-contact', response_model=SafeContactUpdate)
async def update_safe_contact(
    case_id: UUID, body: SafeContactUpdate, reporter: ReporterDep, database: AsyncSession = Depends(session)
) -> SafeContactUpdate:
    if reporter.case_id != case_id:
        raise HTTPException(403, 'Forbidden')
    pref = await database.get(SafeContactPreference, case_id)
    if pref is None:
        pref = SafeContactPreference(case_id=case_id, tenant_id=reporter.tenant_id)
        database.add(pref)
    pref.allowed_channels = body.allowed_channels
    pref.prohibited_times = body.prohibited_times
    pref.neutral_message_only = body.neutral_message_only
    pref.destination_ref_encrypted = encrypt_body(body.destination_ref.encode('utf-8')) if body.destination_ref else None
    pref.updated_at = datetime.now(UTC)
    await database.commit()
    return body


@router.get('/threads/{case_id}/messages', response_model=list[MessageView])
async def list_staff_thread(
    case_id: UUID, context: ContextDep, database: AsyncSession = Depends(session)
) -> list[MessageView]:
    await set_tenant(database, context.tenant_id)
    rows = await _message_rows(database, case_id)
    for row in rows:
        if row.sender == 'reporter' and row.read_at is None:
            row.read_at = datetime.now(UTC)
            row.read_by = context.subject_id or 'staff'
    await database.commit()
    return [_view(r, decrypt_body(r.body_encrypted).decode('utf-8')) for r in rows]


@router.get('/threads/{case_id}/unread-count')
async def unread_reporter_count(case_id: UUID, context: ContextDep, database: AsyncSession = Depends(session)) -> dict[str, int]:
    """Count platform->reporter messages the reporter has not read (pull-only nudge stop)."""
    await set_tenant(database, context.tenant_id)
    query = (
        select(func.count())
        .select_from(MailboxMessage)
        .where(MailboxMessage.case_id == case_id)
        .where(MailboxMessage.sender == 'platform')
        .where(MailboxMessage.read_at.is_(None))
    )
    return {'unread': (await database.scalar(query)) or 0}


@router.get('/threads/{case_id}/safe-contact', response_model=SafeContactUpdate)
async def staff_safe_contact(case_id: UUID, context: ContextDep, database: AsyncSession = Depends(session)) -> SafeContactUpdate:
    """Safe-contact snapshot for the notification nudge worker (no case content)."""
    await set_tenant(database, context.tenant_id)
    pref = await database.get(SafeContactPreference, case_id)
    if pref is None:
        return SafeContactUpdate()
    return SafeContactUpdate(
        allowed_channels=pref.allowed_channels or [],
        prohibited_times=pref.prohibited_times or [],
        neutral_message_only=pref.neutral_message_only,
        destination_ref=decrypt_body(pref.destination_ref_encrypted).decode('utf-8') if pref.destination_ref_encrypted else None,
    )


@router.post('/threads/{case_id}/messages', response_model=MessageView, status_code=201)
async def staff_reply(
    case_id: UUID, body: MessageSend, context: ContextDep, database: AsyncSession = Depends(session)
) -> MessageView:
    await set_tenant(database, context.tenant_id)
    row = MailboxMessage(
        case_id=case_id,
        tenant_id=context.tenant_id,
        sender='platform',
        body_encrypted=encrypt_body(body.body.encode('utf-8')),
        attachment_ids=[str(a) for a in body.attachment_ids],
    )
    database.add(row)
    await database.flush()
    database.add(
        OutboxEvent(
            tenant_id=context.tenant_id,
            event_type='mailbox.message.sent.v1',
            subject=f'mailbox/{row.id}',
            payload={'case_id': str(case_id), 'message_id': str(row.id), 'sender': 'platform'},
        )
    )
    await database.commit()
    await database.refresh(row)
    return _view(row, body.body)


@router.get('/concerns', response_model=list[ConcernView])
async def list_all_concerns(context: ContextDep, database: AsyncSession = Depends(session)) -> list[ConcernView]:
    await set_tenant(database, context.tenant_id)
    rows = list(
        await database.scalars(
            select(RetaliationConcern)
            .where(RetaliationConcern.tenant_id == context.tenant_id)
            .order_by(RetaliationConcern.created_at.desc())
            .limit(500)
        )
    )
    return [
        ConcernView(id=r.id, case_id=r.case_id, risk_band=r.risk_band, details=r.details, status=r.status, created_at=r.created_at)
        for r in rows
    ]


@router.get('/threads/{case_id}/concerns', response_model=list[ConcernView])
async def list_concerns(case_id: UUID, context: ContextDep, database: AsyncSession = Depends(session)) -> list[ConcernView]:
    await set_tenant(database, context.tenant_id)
    rows = list(
        await database.scalars(
            select(RetaliationConcern)
            .where(RetaliationConcern.case_id == case_id)
            .order_by(RetaliationConcern.created_at.desc())
        )
    )
    return [
        ConcernView(id=r.id, case_id=r.case_id, risk_band=r.risk_band, details=r.details, status=r.status, created_at=r.created_at)
        for r in rows
    ]


@router.get('/threads/{case_id}/challenges', response_model=list[ChallengeView])
async def list_challenges(case_id: UUID, context: ContextDep, database: AsyncSession = Depends(session)) -> list[ChallengeView]:
    await set_tenant(database, context.tenant_id)
    rows = list(
        await database.scalars(
            select(ConflictChallenge)
            .where(ConflictChallenge.case_id == case_id)
            .order_by(ConflictChallenge.created_at.desc())
        )
    )
    return [
        ChallengeView(
            id=r.id, case_id=r.case_id, challenged_assignment_id=r.challenged_assignment_id,
            reason_category=r.reason_category, details=r.details, status=r.status, created_at=r.created_at,
        )
        for r in rows
    ]


app = create_app(
    'Mailbox Service',
    'Encrypted pseudonymous threads, safe contact, conflict challenges and retaliation concerns.',
    [router],
)
