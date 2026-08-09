from datetime import UTC, datetime
from typing import Any

from temporalio import activity


@activity.defn
async def record_audit_event(payload: dict[str, Any]) -> dict[str, str]:
    # Production adapter calls Audit Service with workload identity and idempotency key.
    return {'recorded_at': datetime.now(UTC).isoformat(), 'event': str(payload.get('event_type'))}


@activity.defn
async def request_conflict_check(payload: dict[str, Any]) -> dict[str, Any]:
    # Production adapter calls Policy Service and organisation conflict graph.
    return {'decision': 'allow', 'conflicts': [], 'subject': payload.get('candidate_id')}


@activity.defn
async def send_privacy_safe_notification(payload: dict[str, Any]) -> dict[str, str]:
    # Never include allegation text, identity, attachments or evidence in notification payloads.
    return {'status': 'queued', 'template': str(payload.get('template'))}


@activity.defn
async def create_protection_plan(payload: dict[str, Any]) -> dict[str, str]:
    return {'status': 'active', 'case_id': str(payload.get('case_id'))}


@activity.defn
async def schedule_retaliation_check(payload: dict[str, Any]) -> dict[str, str]:
    return {'status': 'scheduled', 'case_id': str(payload.get('case_id'))}


@activity.defn
async def anchor_case_milestone(payload: dict[str, Any]) -> dict[str, str]:
    # Calls Blockchain Ledger Service with hashes/Merkle root only.
    return {'status': 'accepted', 'batch_id': str(payload.get('batch_id'))}
