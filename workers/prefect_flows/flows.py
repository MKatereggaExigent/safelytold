from datetime import UTC, datetime
from typing import Any

from prefect import flow, task

from .governance import GovernanceGate, assert_governed


@task(retries=2, retry_delay_seconds=5)
def sanitise_manifest(manifest: list[dict[str, Any]]) -> list[dict[str, Any]]:
    allowed = {'evidence_id', 'sha256', 'media_type', 'created_at', 'redacted_object_key'}
    return [{k: value for k, value in item.items() if k in allowed} for item in manifest]


@task
def build_chronology(manifest: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(manifest, key=lambda x: str(x.get('created_at', '')))
    return {
        'generated_at': datetime.now(UTC).isoformat(),
        'items': ordered,
        'uncertainty': 'requires-investigator-review',
    }


@task
def queue_human_approval(output: dict[str, Any]) -> dict[str, Any]:
    return {'status': 'awaiting_human_review', 'output': output}


@flow(name='governed-evidence-chronology', log_prints=False)
def evidence_chronology_flow(manifest: list[dict[str, Any]]) -> dict[str, Any]:
    gate = GovernanceGate(capability='evidence_chronology')
    assert_governed(gate)
    safe_manifest = sanitise_manifest(manifest)
    chronology = build_chronology(safe_manifest)
    return queue_human_approval(chronology)


@flow(name='retention-and-legal-hold-scan', log_prints=False)
def retention_scan(records: list[dict[str, Any]]) -> dict[str, int]:
    eligible = sum(1 for item in records if not item.get('legal_hold') and item.get('retention_expired'))
    held = sum(1 for item in records if item.get('legal_hold'))
    return {'eligible_for_review': eligible, 'legal_hold': held}
