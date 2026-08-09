"""Case ORM model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .reporter_handle import ReporterHandle


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"))

    mode: Mapped[str] = mapped_column(String(32))
    jurisdiction_code: Mapped[str] = mapped_column(String(16))
    taxonomy_codes: Mapped[list[str]] = mapped_column(ARRAY(String(64)))
    immediate_risk: Mapped[bool] = mapped_column(Boolean, default=False)

    questionnaire: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    sealed_narrative: Mapped[str] = mapped_column(Text)
    narrative_length: Mapped[int] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    reporter_handle: Mapped["ReporterHandle"] = relationship("ReporterHandle", back_populates="case", uselist=False)
