from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class NotificationTemplate(BaseModel):
    id: UUID
    tenant_id: UUID
    locale: str
    template_code: str
    neutral_subject: str
    neutral_body: str

class NotificationRequest(BaseModel):
    id: UUID
    tenant_id: UUID
    template_code: str
    destination_ref: str
    channel: str
    safe_variables: dict[str, str] = Field(default_factory=dict)
    send_after: datetime | None = None
