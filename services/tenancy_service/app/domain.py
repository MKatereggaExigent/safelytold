from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class Tenant(BaseModel):
    id: UUID
    slug: str
    display_name: str
    tenancy_tier: str = 'shared_database'
    home_region: str
    status: str = 'active'

class LegalEntity(BaseModel):
    id: UUID
    tenant_id: UUID
    registered_name: str
    country_code: str

class OrganisationalUnit(BaseModel):
    id: UUID
    tenant_id: UUID
    parent_id: UUID | None = None
    name: str
    unit_type: str
    routing_tags: set[str] = Field(default_factory=set)

class DeploymentMetadata(BaseModel):
    tenant_id: UUID
    database_mode: str
    residency_region: str
    customer_managed_key: bool = False
    sovereign: bool = False
