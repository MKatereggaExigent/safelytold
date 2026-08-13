from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import Date, DateTime, Integer, JSON, String, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from safelytold_common.auth import ContextDep
from safelytold_common.db import Base, session, set_tenant
from safelytold_common.service import create_app

router = APIRouter(prefix='/v1/analytics', tags=['analytics'])


class MetricObservation(Base):
    __tablename__ = 'metric_observations'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    metric: Mapped[str] = mapped_column(String(80), index=True)
    period: Mapped[date] = mapped_column(Date, index=True)
    dimensions: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    value: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ObservationCreate(BaseModel):
    metric: str = Field(pattern=r'^[a-z][a-z0-9_.-]{1,79}$')
    period: date
    dimensions: dict[str, str] = Field(default_factory=dict)
    value: int = Field(ge=0)


def thresholded(rows: list[tuple[dict[str, str], int]], threshold: int) -> list[dict[str, Any]]:
    """Aggregate equal dimensions and suppress cohorts below the privacy floor."""
    totals: dict[tuple[tuple[str, str], ...], int] = defaultdict(int)
    for dimensions, value in rows:
        totals[tuple(sorted(dimensions.items()))] += value
    return [
        {'dimensions': dict(key), 'value': value if value >= threshold else None, 'suppressed': value < threshold}
        for key, value in sorted(totals.items())
    ]


@router.post('/observations', status_code=201)
async def record_observation(body: ObservationCreate, context: ContextDep, database: AsyncSession = Depends(session)):
    await set_tenant(database, context.tenant_id)
    row = MetricObservation(tenant_id=context.tenant_id, **body.model_dump())
    database.add(row); await database.commit(); await database.refresh(row)
    return {'id': row.id, **body.model_dump()}


@router.get('/trends')
async def trends(metric: str, start: date, end: date, context: ContextDep, database: AsyncSession = Depends(session), privacy_threshold: int = Query(5, ge=5, le=100)):
    await set_tenant(database, context.tenant_id)
    rows = list(await database.scalars(select(MetricObservation).where(MetricObservation.tenant_id == context.tenant_id, MetricObservation.metric == metric, MetricObservation.period >= start, MetricObservation.period <= end)))
    by_period: dict[date, list[tuple[dict[str, str], int]]] = defaultdict(list)
    for row in rows: by_period[row.period].append((row.dimensions, row.value))
    return {'metric': metric, 'privacy_threshold': privacy_threshold, 'periods': [{'period': period, 'cohorts': thresholded(values, privacy_threshold)} for period, values in sorted(by_period.items())]}


@router.get('/management-report')
async def management_report(start: date, end: date, context: ContextDep, database: AsyncSession = Depends(session), privacy_threshold: int = Query(5, ge=5, le=100)):
    await set_tenant(database, context.tenant_id)
    rows = list(await database.scalars(select(MetricObservation).where(MetricObservation.tenant_id == context.tenant_id, MetricObservation.period >= start, MetricObservation.period <= end)))
    metrics: dict[str, list[tuple[dict[str, str], int]]] = defaultdict(list)
    for row in rows: metrics[row.metric].append((row.dimensions, row.value))
    return {'period_start': start, 'period_end': end, 'generated_at': datetime.now(UTC), 'privacy_threshold': privacy_threshold, 'metrics': {name: thresholded(values, privacy_threshold) for name, values in sorted(metrics.items())}, 'contains_narratives': False}


app = create_app('Analytics Service', 'Cohort-thresholded de-identified trends and management reports.', [router])
