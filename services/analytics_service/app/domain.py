from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class AggregateQuery(BaseModel):
    tenant_id: UUID
    dimensions: list[str]
    metrics: list[str]
    period_start: datetime
    period_end: datetime
    minimum_cohort_size: int = 10

class AggregateResult(BaseModel):
    query_id: UUID
    suppressed_cells: int
    values: list[dict[str, Any]]
    privacy_method: str

class BoardReport(BaseModel):
    id: UUID
    tenant_id: UUID
    reporting_period: str
    metrics_ref: str
    systemic_risks: list[str]
    remediation_statuses: list[str]
    approved_by: list[str]
