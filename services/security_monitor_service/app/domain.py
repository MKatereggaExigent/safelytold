from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class SecurityAlert(BaseModel):
    id: UUID
    tenant_id: UUID | None = None
    alert_type: str
    severity: str
    resource_ref: str
    detected_at: datetime
    privacy_safe_context: dict[str, Any] = Field(default_factory=dict)

class AccessAnomaly(BaseModel):
    alert_id: UUID
    subject_ref: str
    case_commitment: str
    purpose: str
    anomaly_reasons: list[str]

class IncidentTrigger(BaseModel):
    alert_id: UUID
    runbook: str
    duty_roles: list[str]
    containment_actions: list[str]
