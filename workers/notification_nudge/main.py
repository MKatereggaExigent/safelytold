import asyncio
import os
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import aio_pika
from sqlalchemy import select

from safelytold_common.config import settings
from safelytold_common.db import session_factory
from safelytold_common.events import CloudEvent
from safelytold_common.messaging import get_provider

from services.notification_service.app.nudge import decide_send, next_attempt_at, post_send_next_check
from services.notification_service.app.notify import send_attempt

MAILBOX_BASE_URL = os.getenv('MAILBOX_BASE_URL', 'http://mailbox-service:8015')
SERVICE_TOKEN = os.getenv('NUDGE_SERVICE_TOKEN') or ''


def _headers(tenant_id: UUID) -> dict[str, str]:
    if SERVICE_TOKEN:
        return {'Authorization': f'Bearer {SERVICE_TOKEN}'}
    return {'x-tenant-id': str(tenant_id)}


NUDGE_TEMPLATE = 'mailbox_nudge_v1'
NUDGE_LOCALE = os.getenv('NUDGE_LOCALE', 'en')
MAX_NUDGES = int(os.getenv('NUDGE_MAX_NUDGES', '3'))
FIRST_DELAY_HOURS = float(os.getenv('NUDGE_FIRST_DELAY_HOURS', '24'))
ESCALATION_HOURS = [float(x) for x in os.getenv('NUDGE_ESCALATION_HOURS', '72,168').split(',')]
QUEUE = 'safelytold.notification-nudge'


def is_reporter_nudge(event: CloudEvent) -> bool:
    """Only platform->reporter messages warrant a nudge; reporter replies do not."""
    return event.type == 'mailbox.message.sent.v1' and event.data.get('sender') == 'platform'


async def fetch_safe_contact(case_id: UUID, tenant_id: UUID) -> dict[str, Any]:
    import httpx

    url = f'{MAILBOX_BASE_URL}/v1/mailbox/threads/{case_id}/safe-contact'
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, headers=_headers(tenant_id))
        response.raise_for_status()
        return response.json()


async def fetch_unread_count(case_id: UUID, tenant_id: UUID) -> int:
    import httpx

    url = f'{MAILBOX_BASE_URL}/v1/mailbox/threads/{case_id}/unread-count'
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, headers=_headers(tenant_id))
        response.raise_for_status()
        return int(response.json().get('unread', 0))


async def create_nudge_request(event: CloudEvent) -> None:
    """Idempotently create a pending nudge request for a platform->reporter message."""
    if not is_reporter_nudge(event):
        return
    case_id = UUID(str(event.data['case_id']))
    try:
        safe_contact = await fetch_safe_contact(case_id, event.tenant_id)
    except Exception as exc:  # noqa: BLE001 - mailbox may not be up yet; retried via event redelivery
        print(f'nudge safe-contact lookup failed: {type(exc).__name__}: {exc}')
        raise
    destination_ref = safe_contact.get('destination_ref')
    channels = set(safe_contact.get('allowed_channels') or [])
    if not destination_ref or 'email' not in channels:
        print('nudge skipped: no permitted email destination in safe-contact preferences')
        return
    now = datetime.now(UTC)
    from services.notification_service.app.main import NotificationRequest, TenantEmailSettings

    async with session_factory()() as database:
        existing = await database.scalar(
            select(NotificationRequest).where(
                NotificationRequest.tenant_id == event.tenant_id,
                NotificationRequest.correlation_id == event.id,
            )
        )
        if existing is not None:
            return
        tenant_settings = await database.get(TenantEmailSettings, event.tenant_id)
        locale = (tenant_settings.default_locale if tenant_settings else None) or NUDGE_LOCALE
        row = NotificationRequest(
            tenant_id=event.tenant_id,
            case_id=case_id,
            correlation_id=event.id,
            template_code=NUDGE_TEMPLATE,
            channel='email',
            locale=locale,
            destination_ref=destination_ref,
            status='pending',
            next_attempt_at=next_attempt_at(0, now, first_delay_hours=FIRST_DELAY_HOURS, escalation_hours=ESCALATION_HOURS),
        )
        database.add(row)
        await database.commit()
        print(f'nudge scheduled {row.id} for case {case_id} at {row.next_attempt_at}')


async def nudge_due_once(batch_size: int = 50) -> int:
    """Send due, permitted nudges; stop early when the reporter already read the thread."""
    from services.notification_service.app.main import NotificationRequest

    now = datetime.now(UTC)
    sent = 0
    async with session_factory()() as database:
        rows = list(
            await database.scalars(
                select(NotificationRequest)
                .where(NotificationRequest.status.in_(['pending', 'sent', 'failed']))
                .where(NotificationRequest.next_attempt_at.is_not(None))
                .where(NotificationRequest.next_attempt_at <= now)
                .order_by(NotificationRequest.next_attempt_at)
                .limit(batch_size)
            )
        )
        for row in rows:
            try:
                unread = await fetch_unread_count(row.case_id, row.tenant_id)
            except Exception as exc:  # noqa: BLE001
                row.last_error = f'unread lookup failed: {type(exc).__name__}: {exc}'
                continue
            if unread == 0:
                row.status = 'delivered'
                row.next_attempt_at = None
                continue
            try:
                safe_contact = await fetch_safe_contact(row.case_id, row.tenant_id)
            except Exception as exc:  # noqa: BLE001
                row.last_error = f'safe-contact lookup failed: {type(exc).__name__}: {exc}'
                continue
            decision = decide_send(
                now=now,
                last_attempt_at=row.last_attempt_at,
                attempts=row.attempts,
                max_nudges=MAX_NUDGES,
                allowed_channels=safe_contact.get('allowed_channels') or [],
                prohibited_times=safe_contact.get('prohibited_times') or [],
                neutral_message_only=safe_contact.get('neutral_message_only', True),
            )
            if not decision.due:
                if decision.reason.startswith('maximum'):
                    row.status = 'delivered'
                    row.next_attempt_at = None
                continue
            try:
                await send_attempt(row, database)
            except (KeyError, ValueError) as exc:
                row.status = 'failed'
                row.last_error = str(exc)
                row.next_attempt_at = None
                continue
            except Exception as exc:  # noqa: BLE001 - transient provider errors are retried
                row.status = 'failed'
                row.last_error = f'send failed: {type(exc).__name__}: {exc}'
                row.next_attempt_at = next_attempt_at(
                    row.attempts, now, first_delay_hours=FIRST_DELAY_HOURS, escalation_hours=ESCALATION_HOURS
                )
                continue
            if row.status == 'failed':
                row.next_attempt_at = next_attempt_at(
                    row.attempts, now, first_delay_hours=FIRST_DELAY_HOURS, escalation_hours=ESCALATION_HOURS
                )
                continue
            now_after = datetime.now(UTC)
            if row.attempts >= MAX_NUDGES:
                row.status = 'delivered'
                row.next_attempt_at = None
            else:
                row.status = 'sent'
                row.next_attempt_at = post_send_next_check(
                    now_after, row.attempts, max_nudges=MAX_NUDGES,
                    first_delay_hours=FIRST_DELAY_HOURS, escalation_hours=ESCALATION_HOURS,
                )
            sent += 1
        await database.commit()
    return sent


async def consume_events() -> None:
    connection = await aio_pika.connect_robust(settings().rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)
        exchange = await channel.declare_exchange('safelytold.events', aio_pika.ExchangeType.TOPIC, durable=True)
        queue = await channel.declare_queue(
            QUEUE,
            durable=True,
            arguments={'x-queue-type': 'quorum', 'x-delivery-limit': 10},
        )
        await queue.bind(exchange, routing_key='mailbox.message.sent.v1')
        async with queue.iterator() as messages:
            async for message in messages:
                async with message.process(requeue=False):
                    event = CloudEvent.model_validate_json(message.body)
                    await create_nudge_request(event)


async def scheduler_loop() -> None:
    while True:
        try:
            count = await nudge_due_once()
        except Exception as exc:  # noqa: BLE001
            print(f'nudge scheduler error: {type(exc).__name__}: {exc}')
            count = 0
        await asyncio.sleep(15 if count == 0 else 5)


async def main() -> None:
    get_provider()
    await asyncio.gather(consume_events(), scheduler_loop())


if __name__ == '__main__':
    asyncio.run(main())
