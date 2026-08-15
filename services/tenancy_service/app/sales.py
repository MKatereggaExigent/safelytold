from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import Date, DateTime, Integer, JSON, String, UniqueConstraint, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from safelytold_common.auth import SuperuserDep
from safelytold_common.db import Base, session

from .admin import Tenant

router = APIRouter(prefix='/v1/sales', tags=['sales-and-subscriptions'])

SALES_CONTACT = {'email': 'sales@datasqan.com', 'phone': '+27686159700'}

CORE_PRIVACY_CONTROLS = [
    'Anonymous reporting', 'Encrypted report transport and storage',
    'Secure anonymous mailbox', 'Sealed evidence originals',
    'Identity separation', 'IP non-retention at application ingress',
    'Human-reviewed decisions', 'Append-only audit history',
]

PLANS = [
    {'code': 'essential', 'name': 'SafelyTold Essential', 'employee_min': 1, 'employee_max': 49,
     'monthly_equivalent': 4500, 'annual_price': 54000, 'setup_fee': 10000, 'price_from': False},
    {'code': 'business', 'name': 'SafelyTold Business', 'employee_min': 50, 'employee_max': 249,
     'monthly_equivalent': 7500, 'annual_price': 90000, 'setup_fee': 15000, 'price_from': False},
    {'code': 'professional', 'name': 'SafelyTold Professional', 'employee_min': 250, 'employee_max': 999,
     'monthly_equivalent': 12500, 'annual_price': 150000, 'setup_fee': 25000, 'price_from': False},
    {'code': 'enterprise', 'name': 'SafelyTold Enterprise', 'employee_min': 1000, 'employee_max': 4999,
     'monthly_equivalent': 22500, 'annual_price': 270000, 'setup_fee': 50000, 'price_from': False},
    {'code': 'enterprise_plus', 'name': 'SafelyTold Enterprise+', 'employee_min': 5000, 'employee_max': None,
     'monthly_equivalent': 35000, 'annual_price': 420000, 'setup_fee': 75000, 'price_from': True},
    {'code': 'enterprise_isolated', 'name': 'Enterprise Isolated', 'employee_min': None, 'employee_max': None,
     'monthly_equivalent': 50000, 'annual_price': 600000, 'setup_fee': 100000, 'price_from': True,
     'required_isolation': 'dedicated_data_plane'},
    {'code': 'sovereign_private_cloud', 'name': 'Sovereign / Private Cloud', 'employee_min': None, 'employee_max': None,
     'monthly_equivalent': 60000, 'monthly_max': 100000, 'annual_price': None, 'setup_fee': 150000,
     'price_from': True, 'custom_annual': True, 'required_isolation': 'customer_environment'},
]
PLAN_BY_CODE = {plan['code']: plan for plan in PLANS}

ENTERPRISE_CAPABILITIES = [
    'Dedicated databases', 'Dedicated encryption keys', 'Enterprise SSO and SCIM',
    'Customer-managed keys', 'Private connectivity', 'Custom retention',
    'Isolated compute', 'Disaster-recovery commitments', 'Advanced SLA',
    'Sovereign deployment',
]


class TenantSubscription(Base):
    __tablename__ = 'tenant_subscriptions'
    __table_args__ = (UniqueConstraint('tenant_id', name='uq_subscription_tenant'),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    plan_code: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(30), default='pending')
    employee_count: Mapped[int] = mapped_column(Integer)
    contract_start: Mapped[date] = mapped_column(Date)
    contract_end: Mapped[date] = mapped_column(Date)
    annual_price_ex_vat: Mapped[int | None] = mapped_column(Integer)
    setup_fee_ex_vat: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default='ZAR')
    isolation_tier: Mapped[str] = mapped_column(String(50), default='shared_database')
    purchased_capabilities: Mapped[list[str]] = mapped_column(JSON, default=list)
    sales_reference: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class SubscriptionUpsert(BaseModel):
    plan_code: str
    status: str = Field(pattern='^(pending|active|suspended|expired|cancelled)$')
    employee_count: int = Field(ge=1)
    contract_start: date
    contract_end: date
    annual_price_ex_vat: int | None = Field(default=None, ge=0)
    setup_fee_ex_vat: int = Field(ge=0)
    isolation_tier: str = Field(pattern='^(shared_database|dedicated_database|dedicated_data_plane|customer_environment)$')
    purchased_capabilities: list[str] = Field(default_factory=list, max_length=50)
    sales_reference: str | None = Field(default=None, max_length=120)

    @model_validator(mode='after')
    def validate_contract(self):
        plan = PLAN_BY_CODE.get(self.plan_code)
        if plan is None:
            raise ValueError('Unknown SafelyTold plan')
        if (self.contract_end - self.contract_start).days < 365:
            raise ValueError('SafelyTold subscriptions require an annual contract of at least 365 days')
        required = plan.get('required_isolation')
        if required and self.isolation_tier != required:
            raise ValueError(f'{plan["name"]} requires isolation tier {required}')
        return self


def public_plan(plan: dict) -> dict:
    return {
        **plan, 'currency': 'ZAR', 'vat_included': False, 'billing_term': 'annual',
        'core_privacy_controls': CORE_PRIVACY_CONTROLS,
        'enterprise_capabilities': ENTERPRISE_CAPABILITIES if plan['code'] in {'enterprise', 'enterprise_plus', 'enterprise_isolated', 'sovereign_private_cloud'} else [],
    }


def subscription_view(value: TenantSubscription) -> dict:
    return {
        'id': str(value.id), 'tenant_id': str(value.tenant_id), 'plan_code': value.plan_code,
        'status': value.status, 'employee_count': value.employee_count,
        'contract_start': value.contract_start, 'contract_end': value.contract_end,
        'annual_price_ex_vat': value.annual_price_ex_vat, 'setup_fee_ex_vat': value.setup_fee_ex_vat,
        'currency': value.currency, 'isolation_tier': value.isolation_tier,
        'core_privacy_controls': CORE_PRIVACY_CONTROLS,
        'purchased_capabilities': value.purchased_capabilities, 'sales_reference': value.sales_reference,
    }


@router.get('/plans')
async def list_public_plans() -> dict:
    return {'plans': [public_plan(plan) for plan in PLANS], 'sales_contact': SALES_CONTACT}


@router.put('/admin/tenants/{tenant_id}/subscription')
async def upsert_subscription(tenant_id: UUID, body: SubscriptionUpsert, _: SuperuserDep,
                              database: AsyncSession = Depends(session)) -> dict:
    tenant = await database.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(404, 'Tenant not found')
    value = await database.scalar(select(TenantSubscription).where(TenantSubscription.tenant_id == tenant_id))
    if value is None:
        value = TenantSubscription(tenant_id=tenant_id)
        database.add(value)
    for key, item in body.model_dump().items():
        setattr(value, key, item)
    tenant.tenancy_tier = body.isolation_tier
    await database.commit()
    await database.refresh(value)
    return subscription_view(value)


@router.get('/admin/tenants/{tenant_id}/subscription')
async def get_subscription(tenant_id: UUID, _: SuperuserDep,
                           database: AsyncSession = Depends(session)) -> dict:
    value = await database.scalar(select(TenantSubscription).where(TenantSubscription.tenant_id == tenant_id))
    if value is None:
        raise HTTPException(404, 'Subscription not found')
    return subscription_view(value)
