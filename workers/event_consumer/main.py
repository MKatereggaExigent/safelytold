import asyncio
import json
from collections.abc import Awaitable, Callable

import aio_pika
from pydantic import ValidationError

from safelytold_common.config import settings
from safelytold_common.events import CloudEvent

Handler = Callable[[CloudEvent], Awaitable[None]]


async def handle_reference(event: CloudEvent) -> None:
    # Replace with idempotent domain handling keyed by event.id.
    print(json.dumps({'event_id': str(event.id), 'type': event.type, 'subject': event.subject}))


async def main(handler: Handler = handle_reference) -> None:
    connection = await aio_pika.connect_robust(settings().rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=20)
        exchange = await channel.declare_exchange('safelytold.events', aio_pika.ExchangeType.TOPIC, durable=True)
        queue = await channel.declare_queue(
            'safelytold.reference-consumer',
            durable=True,
            arguments={'x-queue-type': 'quorum', 'x-delivery-limit': 5},
        )
        await queue.bind(exchange, routing_key='#')
        async with queue.iterator() as messages:
            async for message in messages:
                async with message.process(requeue=False):
                    try:
                        event = CloudEvent.model_validate_json(message.body)
                        await handler(event)
                    except ValidationError:
                        # Production: publish to a restricted quarantine exchange without raw payload logs.
                        raise


if __name__ == '__main__':
    asyncio.run(main())
