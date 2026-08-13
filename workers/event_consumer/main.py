import asyncio
import json
import os
from datetime import UTC, datetime, timedelta

import aio_pika
from pydantic import ValidationError
from safelytold_common.config import settings
from safelytold_common.db import session_factory, set_tenant
from safelytold_common.events import CloudEvent
from safelytold_common.generic import Record
from sqlalchemy import select
from temporalio.client import Client
from temporalio.exceptions import WorkflowAlreadyStartedError

from workers.workflow_worker.models import CaseWorkflowInput

TASK_QUEUE = os.getenv('TEMPORAL_TASK_QUEUE', 'safelytold-case-lifecycle')
_temporal: Client | None = None

STATUS_BY_ACTION = {
    'assign': 'triage',
    'acknowledge': 'under_investigation',
    'submit_findings': 'reviewing',
    'approve_decision': 'resolved',
    'close': 'closed',
    'open_appeal': 'reviewing',
}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


async def temporal_client() -> Client:
    global _temporal
    if _temporal is None:
        _temporal = await Client.connect(
            os.getenv('TEMPORAL_ADDRESS', 'temporal:7233'),
            namespace=os.getenv('TEMPORAL_NAMESPACE', 'default'),
        )
    return _temporal


async def _case_record(session, tenant_id: object, report_id: str) -> Record | None:
    return await session.scalar(
        select(Record).where(
            Record.tenant_id == tenant_id,
            Record.kind == 'case',
            Record.payload['report_id'].as_string() == report_id,
        ).limit(1)
    )


async def ensure_case(data: dict, tenant_id: object) -> Record | None:
    report_id = str(data.get('record_id') or '')
    if not report_id:
        return None
    async with session_factory()() as session:
        await set_tenant(session, tenant_id)
        existing = await _case_record(session, tenant_id, report_id)
        if existing is not None:
            return existing
        case = Record(
            tenant_id=tenant_id,
            kind='case',
            status='unverified',
            payload={
                'case_id': report_id,
                'report_id': report_id,
                'mode': data.get('mode'),
                'jurisdiction_code': data.get('jurisdiction_code'),
                'taxonomy_codes': data.get('taxonomy_codes') or [],
                'immediate_risk': bool(data.get('immediate_risk')),
                'protection_required': bool(data.get('protection_required')),
                'severity': data.get('severity') or 'standard',
                'source': 'intake',
                'created_at': data.get('created_at') or _now_iso(),
            },
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)
        return case


async def update_case_status(report_id: str, tenant_id: object, status: str | None) -> None:
    if not status:
        return
    async with session_factory()() as session:
        await set_tenant(session, tenant_id)
        row = await _case_record(session, tenant_id, report_id)
        if row is not None and row.status != status:
            row.status = status
            await session.commit()


async def handle_case_reported(event: CloudEvent) -> None:
    data = event.data or {}
    report_id = str(data.get('record_id') or '')
    case = await ensure_case(data, event.tenant_id)
    if case is None:
        return
    client = await temporal_client()
    try:
        await client.start_workflow(
            'CaseLifecycleWorkflow',
            CaseWorkflowInput(
                tenant_id=str(event.tenant_id),
                case_id=report_id,
                severity=str(data.get('severity') or 'standard'),
                jurisdiction=str(data.get('jurisdiction_code') or ''),
                acknowledgement_due_at=datetime.now(UTC) + timedelta(days=7),
                target_resolution_at=datetime.now(UTC) + timedelta(days=90),
                protection_required=bool(data.get('protection_required')),
            ),
            id=f'case:{report_id}',
            task_queue=TASK_QUEUE,
        )
    except WorkflowAlreadyStartedError:
        pass


async def handle_case_action(event: CloudEvent) -> None:
    data = event.data or {}
    kind = str(data.get('kind') or '')
    report_id = str(data.get('case_id') or '')
    if not report_id:
        return
    action: tuple[str, str] | None = None
    if kind == 'assignment':
        action = ('assign', str(data.get('assignee_role') or 'investigator'))
    elif kind == 'finding':
        action = ('submit_findings', '')
    elif kind == 'decision':
        action = ('approve_decision', '')
    elif kind == 'appeal':
        action = ('open_appeal', '')
    elif kind == 'case':
        inner = str(data.get('action') or '')
        if inner == 'acknowledge':
            action = ('acknowledge', '')
        elif inner == 'close':
            action = ('close', '')
    if action is None:
        return
    client = await temporal_client()
    handle = client.get_workflow_handle(f'case:{report_id}')
    try:
        if action[1]:
            await handle.signal(action[0], action[1])
        else:
            await handle.signal(action[0])
    except Exception as exc:
        print(
            json.dumps(
                {
                    'event_id': str(event.id),
                    'type': event.type,
                    'warning': 'signal skipped',
                    'error': str(exc),
                }
            )
        )
    await update_case_status(report_id, event.tenant_id, STATUS_BY_ACTION.get(action[0]))


async def handle_event(event: CloudEvent) -> None:
    if event.type == 'case.reported.v1':
        await handle_case_reported(event)
    elif event.type == 'case.assignment_changed.v1':
        await handle_case_action(event)


async def main() -> None:
    connection = await aio_pika.connect_robust(settings().rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=20)
        exchange = await channel.declare_exchange(
            'safelytold.events', aio_pika.ExchangeType.TOPIC, durable=True
        )
        queue = await channel.declare_queue(
            'safelytold.case-consumer',
            durable=True,
            arguments={'x-queue-type': 'quorum', 'x-delivery-limit': 5},
        )
        await queue.bind(exchange, routing_key='#')
        async with queue.iterator() as messages:
            async for message in messages:
                async with message.process(requeue=False):
                    try:
                        event = CloudEvent.model_validate_json(message.body)
                        await handle_event(event)
                    except ValidationError:
                        # Production: publish to a restricted quarantine exchange
                        # without raw payload logs.
                        raise


if __name__ == '__main__':
    asyncio.run(main())
