from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import HTTPException

from safelytold_common import reporter_access

ROOT = Path(__file__).resolve().parents[1]


def test_reporter_access_is_server_signed_and_tenant_bound(monkeypatch) -> None:
    monkeypatch.setattr(reporter_access, '_secret', lambda: 'test-secret-with-sufficient-entropy')
    tenant_id = uuid4()
    token = reporter_access.create_reporter_access(
        tenant_id=tenant_id,
        tenant_slug='cticc',
        tenant_name='CTICC',
        channel='open',
        modes=['anonymous', 'confidential', 'identified'],
        eligibility_class='open_unverified',
    )
    context = reporter_access.decode_reporter_access(token)
    assert context.tenant_id == tenant_id
    assert context.tenant_slug == 'cticc'
    assert context.channel == 'open'
    assert context.eligibility_class == 'open_unverified'


def test_expired_reporter_access_is_rejected(monkeypatch) -> None:
    monkeypatch.setattr(reporter_access, '_secret', lambda: 'test-secret-with-sufficient-entropy')
    token = reporter_access.create_reporter_access(
        tenant_id=uuid4(), tenant_slug='cticc', tenant_name='CTICC', channel='open',
        modes=['anonymous'], eligibility_class='open_unverified', lifetime=timedelta(seconds=-1),
    )
    with pytest.raises(HTTPException, match='Invalid or expired reporting session'):
        reporter_access.decode_reporter_access(token)


def test_legacy_public_intake_bypass_is_disabled() -> None:
    source = (ROOT / 'services/intake_service/app/main.py').read_text(encoding='utf-8')
    assert "public_kinds={'report'}" not in source
    assert 'create_enabled=False' in source
    assert 'ReporterAccessDep' in source
    assert "payload.pop('tenant_id', None)" in source


def test_reporter_ui_requires_resolved_organisation_context() -> None:
    source = (ROOT / 'apps/reporter-web/app/report/page.tsx').read_text(encoding='utf-8')
    assert 'resolveReportingContext' in source
    assert 'createTenantReport' in source
    assert 'createTenantReporterHandle' in source
    assert 'You are reporting to' in source


def test_verified_anonymous_requires_unlinkable_credential_policy() -> None:
    source = (ROOT / 'services/tenancy_service/app/reporting.py').read_text(encoding='utf-8')
    assert "'verified_anonymous'" in source
    assert "{'privacy-pass', 'anonymous-credential'}" in source
    assert 'requires a privacy-preserving eligibility credential' in source
