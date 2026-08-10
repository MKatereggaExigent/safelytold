from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from typing import Any

import httpx
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
    # Submit content-free hashes and a Merkle root to the Blockchain Ledger
    # Service. Never place case text, identities or evidence on the chain.
    ledger_url = os.environ.get('BLOCKCHAIN_LEDGER_URL', 'http://blockchain-ledger-service:8028').rstrip('/')
    token = os.environ.get('BLOCKCHAIN_ANCHOR_TOKEN', '')
    batch_id = str(payload.get('batch_id') or '')
    tenant = payload.get('tenant_id') or batch_id or 'safelytold'
    kind = 'disclosure_package' if batch_id.startswith('disclosure:') else 'evidence_manifest'
    leaf = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode('utf-8')).hexdigest()
    body = {
        'tenant_hash': hashlib.sha256(str(tenant).encode('utf-8')).hexdigest(),
        'batch_id': batch_id,
        'kind': kind,
        'leaf_hashes': [leaf],
        'metadata': {'source': 'case-lifecycle-worker'},
    }
    headers = {'x-anchor-token': token} if token else {}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(f'{ledger_url}/v1/ledger/anchors', json=body, headers=headers)
        response.raise_for_status()
        result = response.json()
    return {
        'status': 'accepted',
        'batch_id': batch_id,
        'mode': str(result.get('mode', '')),
        'merkle_root': str(result.get('merkle_root', '')),
        'transaction_hash': str(result.get('transaction_hash') or ''),
    }
