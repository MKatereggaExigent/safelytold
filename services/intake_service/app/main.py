from typing import Any

from safelytold_common.generic import router
from safelytold_common.service import create_app


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


app = create_app(
    'Intake Service',
    'Private journals and anonymous, confidential or identified reports.',
    [
        router(
            'intake_service',
            'case.reported.v1',
            public_kinds={'report'},
            event_payload=_report_event_meta,
        )
    ],
)
