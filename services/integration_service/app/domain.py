from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class Connector(BaseModel):
    id: UUID
    tenant_id: UUID
    connector_type: str = Field(pattern='^(oidc|saml|scim|hris|messaging|voice|eap|regulator|webhook|siem)$')
    region: str
    secret_reference: str
    enabled: bool = False

class Delivery(BaseModel):
    id: UUID
    connector_id: UUID
    event_type: str
    destination_ref: str
    idempotency_key: str
    status: str
    attempts: int = 0

class ExternalInvestigatorInvitation(BaseModel):
    id: UUID
    case_id: UUID
    identity_ref: str
    scope: list[str]
    expires_at: datetime
