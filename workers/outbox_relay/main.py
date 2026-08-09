import asyncio
from datetime import UTC, datetime

from sqlalchemy import select

from safelytold_common.db import OutboxEvent, session_factory
from safelytold_common.events import CloudEvent
from safelytold_common.rabbit import publish_event


async def relay_once(batch_size: int = 100) -> int:
    """Publish outbox rows and mark them only after broker confirmation."""
    published = 0
    async with session_factory()() as session:
        rows = list(
            await session.scalars(
                select(OutboxEvent)
                .where(OutboxEvent.published_at.is_(None))
                .order_by(OutboxEvent.created_at)
                .with_for_update(skip_locked=True)
                .limit(batch_size)
            )
        )
        for row in rows:
            try:
                event = CloudEvent(
                    source='urn:safelytold:outbox-relay',
                    type=row.event_type,
                    subject=row.subject,
                    tenant_id=row.tenant_id,
                    correlation_id=row.correlation_id,
                    data=row.payload,
                )
                await publish_event(event)
                row.published_at = datetime.now(UTC)
                row.last_error = None
                published += 1
            except Exception as exc:
                row.attempts += 1
                row.last_error = str(exc)[:1000]
        await session.commit()
    return published


async def main() -> None:
    while True:
        count = await relay_once()
        await asyncio.sleep(0.25 if count else 2.0)


if __name__ == '__main__':
    asyncio.run(main())
