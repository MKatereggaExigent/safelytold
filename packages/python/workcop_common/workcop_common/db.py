from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, JSON, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .config import settings


class Base(DeclarativeBase):
    pass


class TenantMixin:
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    status: Mapped[str] = mapped_column(String(40), default='active')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class OutboxEvent(Base):
    __tablename__ = 'outbox_events'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    event_type: Mapped[str] = mapped_column(String(160), index=True)
    subject: Mapped[str] = mapped_column(String(240))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    correlation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(default=0)
    last_error: Mapped[str | None] = mapped_column(Text)


_engine: AsyncEngine | None = None
_sessions: async_sessionmaker[AsyncSession] | None = None


def engine() -> AsyncEngine:
    global _engine, _sessions
    if _engine is None:
        _engine = create_async_engine(settings().database_url, pool_pre_ping=True)
        _sessions = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def session_factory() -> async_sessionmaker[AsyncSession]:
    engine()
    assert _sessions is not None
    return _sessions


async def session() -> AsyncIterator[AsyncSession]:
    async with session_factory()() as value:
        yield value


async def set_tenant(value: AsyncSession, tenant_id: UUID) -> None:
    await value.execute(text("SELECT set_config('app.tenant_id', :tenant_id, true)"), {'tenant_id': str(tenant_id)})
