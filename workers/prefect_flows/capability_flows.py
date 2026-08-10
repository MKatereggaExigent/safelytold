from __future__ import annotations

import os
from typing import Any

import httpx
from prefect import flow, task

from .governance import GovernanceGate, assert_governed

GATEWAY_INTERNAL_URL = os.getenv('GATEWAY_INTERNAL_URL', 'http://ai-gateway:8027').rstrip('/')


@task
def require_redacted(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get('contains_raw_evidence') or payload.get('contains_identity'):
        raise ValueError('Only redacted, approved working data may enter AI flows')
    return payload


@task
def ai_gateway_draft(capability: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = {
        'tenant_id': payload.get('tenant_id'),
        'case_id': payload.get('case_id'),
        'capability': capability,
        'purpose': payload.get('purpose') or f'{capability} advisory draft',
        'redacted_input': payload['redacted_input'],
        'source_refs': payload.get('source_refs', []),
    }
    with httpx.Client(timeout=120) as client:
        response = client.post(f'{GATEWAY_INTERNAL_URL}/v1/ai/runs', json=body)
    if response.status_code >= 400:
        detail = response.text[:500]
        raise RuntimeError(f'AI Gateway run failed ({response.status_code}): {detail}')
    data = response.json()
    return {
        'capability': capability,
        'draft': data['output'],
        'source_refs': payload.get('source_refs', []),
        'uncertainty': data.get('uncertainty', 'medium'),
        'requires_human_approval': True,
        'run_id': data.get('run_id'),
    }


@task
def human_review_queue(result: dict[str, Any]) -> dict[str, Any]:
    return {'status': 'awaiting_human_review', 'result': result}


def _run(capability: str, payload: dict[str, Any]) -> dict[str, Any]:
    assert_governed(GovernanceGate(capability=capability))
    safe = require_redacted(payload)
    draft = ai_gateway_draft(capability, safe)
    return human_review_queue(draft)


@flow(name='reporter-writing-assistant')
def reporter_writing(payload: dict[str, Any]) -> dict[str, Any]:
    return _run('reporter_writing', payload)


@flow(name='anonymity-risk-scan')
def anonymity_scan(payload: dict[str, Any]) -> dict[str, Any]:
    return _run('anonymity_scan', payload)


@flow(name='triage-copilot')
def triage_copilot(payload: dict[str, Any]) -> dict[str, Any]:
    return _run('triage_copilot', payload)


@flow(name='evidence-chronology-agent')
def evidence_chronology(payload: dict[str, Any]) -> dict[str, Any]:
    return _run('evidence_chronology', payload)


@flow(name='policy-retrieval-agent')
def policy_retrieval(payload: dict[str, Any]) -> dict[str, Any]:
    return _run('policy_retrieval', payload)


@flow(name='investigation-summary-agent')
def investigation_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return _run('investigation_summary', payload)


@flow(name='translation-agent')
def translation(payload: dict[str, Any]) -> dict[str, Any]:
    return _run('translation', payload)


@flow(name='privacy-safe-pattern-agent')
def pattern_analytics(payload: dict[str, Any]) -> dict[str, Any]:
    if int(payload.get('cohort_size', 0)) < int(payload.get('minimum_cohort_size', 10)):
        return {'status': 'suppressed', 'reason': 'minimum_cohort_not_met'}
    return _run('pattern_analytics', payload)


@flow(name='sla-remediation-agent')
def sla_remediation(payload: dict[str, Any]) -> dict[str, Any]:
    return _run('sla_remediation', payload)
