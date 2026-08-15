from datetime import date

import pytest
from pydantic import ValidationError

from services.tenancy_service.app.sales import CORE_PRIVACY_CONTROLS, PLAN_BY_CODE, PLANS, SubscriptionUpsert


def test_pricing_matches_approved_annual_catalogue() -> None:
    expected = {
        'essential': (4500, 54000, 10000),
        'business': (7500, 90000, 15000),
        'professional': (12500, 150000, 25000),
        'enterprise': (22500, 270000, 50000),
        'enterprise_plus': (35000, 420000, 75000),
        'enterprise_isolated': (50000, 600000, 100000),
        'sovereign_private_cloud': (60000, None, 150000),
    }
    assert {plan['code']: (plan['monthly_equivalent'], plan['annual_price'], plan['setup_fee']) for plan in PLANS} == expected


def test_every_plan_inherits_non_negotiable_privacy_controls() -> None:
    assert 'Anonymous reporting' in CORE_PRIVACY_CONTROLS
    assert 'Secure anonymous mailbox' in CORE_PRIVACY_CONTROLS
    assert all(CORE_PRIVACY_CONTROLS for _ in PLANS)


def test_subscription_rejects_month_to_month_contract() -> None:
    with pytest.raises(ValidationError, match='annual contract'):
        SubscriptionUpsert(
            plan_code='essential', status='active', employee_count=20,
            contract_start=date(2026, 1, 1), contract_end=date(2026, 6, 30),
            annual_price_ex_vat=PLAN_BY_CODE['essential']['annual_price'],
            setup_fee_ex_vat=10000, isolation_tier='shared_database',
        )


def test_isolated_plan_requires_dedicated_data_plane() -> None:
    with pytest.raises(ValidationError, match='dedicated_data_plane'):
        SubscriptionUpsert(
            plan_code='enterprise_isolated', status='active', employee_count=2000,
            contract_start=date(2026, 1, 1), contract_end=date(2027, 1, 1),
            annual_price_ex_vat=600000, setup_fee_ex_vat=100000,
            isolation_tier='shared_database',
        )
