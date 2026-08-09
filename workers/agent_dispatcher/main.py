from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import aio_pika
from prefect.client.orchestration import get_client

from safelytold_common.config import settings
from safelytold_common.events import CloudEvent

# Events contain only opaque identifiers and operational metadata. A deployment or flow
# fetches authorised redacted derivatives using workload identity and purpose-bound access.
ROUTES: dict[str, str] = {
    'case.reported.v1': 'triage-copilot/triage-copilot',
    'evidence.sanitised.v1': 'evidence-chronology-agent/evidence-chronology-agent',
    'case.closed.v1': 'privacy-safe-pattern-agent/privacy-safe-pattern-agent',
}


async def dispatch(event: CloudEvent) -> dict[str, Any]:
    deployment = ROUTES.get(event.type)
    if deployment is None:
        return {'status': 'ignored', 'event_type': event.type}
    parameters = {
        'payload': {
            'event_id': str(event.id),
            'tenant_id': str(event.tenant_id),
            'subject': event.subject,
            'source_refs': [event.subject],
            'contains_raw_evidence': False,
            'contains_identity': False,
        }
    }
    async with get_client() as client:
        deployment_record = await client.read_deployment_by_name(deployment)
        flow_run = await client.create_flow_run_from_deployment(
            deployment_id=deployment_record.id,
            parameters=parameters,
            idempotency_key=str(event.id),
        )
    return {'status': 'started', 'flow_run_id': str(flow_run.id)}


async def main() -> None:
    connection = await aio_pika.connect_robust(settings().rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)
        exchange = await channel.declare_exchange('safelytold.events', aio_pika.ExchangeType.TOPIC, durable=True)
        queue = await channel.declare_queue(
            'safelytold.agent-dispatcher',
            durable=True,
            arguments={'x-queue-type': 'quorum', 'x-delivery-limit': 5},
        )
        for routing_key in ROUTES:
            await queue.bind(exchange, routing_key=routing_key)
        async with queue.iterator() as messages:
            async for message in messages:
                async with message.process(requeue=False):
                    event = CloudEvent.model_validate_json(message.body)
                    await dispatch(event)


if __name__ == '__main__':
    asyncio.run(main())
