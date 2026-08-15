from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from safelytold_common.generic import Create, Record, View, router
from safelytold_common.db import OutboxEvent, session, set_tenant
from safelytold_common.reporter_access import ReporterAccessDep
from safelytold_common.report_receipt import build_privacy_receipt
from safelytold_common.service import create_app
from safelytold_common.taxonomy import CATEGORY_PARENT, validate_concern_categories

REPORTER_TYPES = frozenset({'employee', 'contractor', 'former_employee', 'supplier', 'customer', 'anonymous_witness', 'other'})


def _report_event_meta(payload: dict[str, Any]) -> dict[str, Any]:
    urgent = bool(payload.get('immediate_risk'))
    return {
        'mode': payload.get('mode'),
        'jurisdiction_code': payload.get('jurisdiction_code'),
        'taxonomy_codes': payload.get('taxonomy_codes') or [],
        'immediate_risk': urgent,
        'protection_required': urgent,
        'severity': 'critical' if urgent else 'standard',
        'created_at': payload.get('created_at'),
    }


reporter_router = APIRouter(prefix='/v1/reports', tags=['reporter-intake'])


@reporter_router.post('', response_model=View, status_code=201)
async def create_tenant_report(body: Create, access: ReporterAccessDep, database: AsyncSession = Depends(session)):
    if body.kind != 'report':
        raise HTTPException(422, 'Only reports may be created through reporter intake')
    mode = str(body.payload.get('mode') or '')
    if mode not in access.modes:
        raise HTTPException(403, 'Reporting mode is not enabled for this organisation channel')
    payload = dict(body.payload)
    reporter_type = str(payload.get('reporter_type') or '').strip().lower()
    if reporter_type not in REPORTER_TYPES:
        raise HTTPException(422, 'Choose a valid reporter type')
    try:
        categories = validate_concern_categories(list(payload.get('taxonomy_codes') or []))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    payload['taxonomy_codes'] = categories
    payload['taxonomy_domains'] = sorted({CATEGORY_PARENT[code] for code in categories if code in CATEGORY_PARENT})
    payload['reporting_channel'] = access.channel
    payload['eligibility_class'] = access.eligibility_class
    identity_provided = mode in {'confidential', 'identified'} and bool(payload.get('contact_vaulted'))
    payload['privacy_receipt'] = build_privacy_receipt(
        organisation=access.tenant_name, organisation_slug=access.tenant_slug,
        reporter_type=reporter_type, eligibility_class=access.eligibility_class,
        mode=mode, identity_provided=identity_provided,
    )
    payload.pop('tenant_id', None)
    await set_tenant(database, access.tenant_id)
    value = Record(tenant_id=access.tenant_id, kind='report', payload=payload)
    database.add(value)
    await database.flush()
    event_data = {'record_id': str(value.id), 'kind': value.kind, 'status': value.status, **_report_event_meta(payload)}
    database.add(OutboxEvent(tenant_id=access.tenant_id, event_type='case.reported.v1', subject=f'intake_service/{value.id}', payload=event_data))
    await database.commit()
    await database.refresh(value)
    return value


app = create_app(
    'Intake Service',
    'Private journals and anonymous, verified anonymous, confidential or identified reports.',
    [
        router(
            'intake_service',
            'case.reported.v1',
            create_enabled=False,
            event_payload=_report_event_meta,
        ), reporter_router
    ],
)
