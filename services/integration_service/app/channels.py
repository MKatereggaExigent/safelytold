from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Literal

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from safelytold_common.config import settings

router = APIRouter(prefix='/v1/channels', tags=['reporting-channels'])


class ProviderReport(BaseModel):
    provider_event_id: str = Field(min_length=6, max_length=160)
    channel: Literal['email', 'hotline']
    reporting_mode: Literal['anonymous', 'confidential', 'identified']
    jurisdiction_code: str = Field(default='ZA', min_length=2, max_length=8)
    taxonomy_codes: list[str] = Field(min_length=1, max_length=10)
    narrative: str = Field(min_length=10, max_length=50_000)
    immediate_risk: bool = False
    language: str = Field(default='en', min_length=2, max_length=10)


def valid_signature(raw: bytes, timestamp: str, signature: str, secret: str, now: int | None = None) -> bool:
    try:
        stamp = int(timestamp)
    except ValueError:
        return False
    if abs((now or int(time.time())) - stamp) > 300 or not secret:
        return False
    expected = hmac.new(secret.encode(), timestamp.encode() + b'.' + raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.removeprefix('sha256='))


@router.get('/readiness')
async def channel_readiness():
    cfg = settings()
    return {
        'email': {'ready': bool(cfg.reporting_email_address and cfg.channel_webhook_secret), 'address': cfg.reporting_email_address or None},
        'hotline': {'ready': bool(cfg.toll_free_number and cfg.receiving_provider_name and cfg.channel_webhook_secret), 'number': cfg.toll_free_number or None, 'provider': cfg.receiving_provider_name or None},
        'production_ready': bool(cfg.reporting_email_address and cfg.toll_free_number and cfg.receiving_provider_name and cfg.channel_webhook_secret),
    }


@router.post('/provider-reports', status_code=201)
async def receive_provider_report(
    request: Request,
    x_provider_timestamp: str = Header(),
    x_provider_signature: str = Header(),
):
    cfg = settings()
    raw = await request.body()
    if not valid_signature(raw, x_provider_timestamp, x_provider_signature, cfg.channel_webhook_secret):
        raise HTTPException(401, 'Invalid or expired provider signature')
    try:
        body = ProviderReport.model_validate(json.loads(raw))
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(422, 'Invalid provider report') from exc

    report = {
        'kind': 'report',
        'payload': {
            'mode': body.reporting_mode,
            'jurisdiction_code': body.jurisdiction_code,
            'taxonomy_codes': body.taxonomy_codes,
            'narrative': body.narrative,
            'immediate_risk': body.immediate_risk,
            'source_channel': body.channel,
            'source_reference': hashlib.sha256(body.provider_event_id.encode()).hexdigest(),
            'language': body.language,
        },
    }
    headers = {'x-idempotency-key': body.provider_event_id}
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            intake = await client.post(f"{cfg.intake_service_url.rstrip('/')}/v1/records", json=report, headers=headers)
            intake.raise_for_status()
            case_id = intake.json()['id']
            identity = await client.post(
                f"{cfg.reporter_identity_service_url.rstrip('/')}/v1/reporter/handles",
                json={'case_id': case_id},
                headers=headers,
            )
            identity.raise_for_status()
        except (httpx.HTTPError, KeyError) as exc:
            raise HTTPException(502, 'Case intake unavailable') from exc
    handle = identity.json()
    return {
        'case_id': case_id,
        'public_code': handle['public_code'],
        'recovery_secret': handle['recovery_secret'],
        'channel': body.channel,
    }
