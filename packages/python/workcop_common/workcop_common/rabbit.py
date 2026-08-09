from __future__ import annotations

import aio_pika

from .config import settings
from .events import CloudEvent


class Publisher:
    def __init__(self, url: str, exchange: str = 'safelytold.events') -> None:
        self.url = url
        self.name = exchange
        self.connection: aio_pika.abc.AbstractRobustConnection | None = None
        self.exchange: aio_pika.abc.AbstractExchange | None = None

    async def connect(self) -> None:
        self.connection = await aio_pika.connect_robust(self.url)
        channel = await self.connection.channel(publisher_confirms=True)
        self.exchange = await channel.declare_exchange(self.name, aio_pika.ExchangeType.TOPIC, durable=True)

    async def publish(self, event: CloudEvent) -> None:
        if self.exchange is None:
            await self.connect()
        assert self.exchange is not None
        message = aio_pika.Message(
            event.model_dump_json().encode(),
            content_type='application/cloudevents+json',
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            message_id=str(event.id),
            correlation_id=str(event.correlation_id),
        )
        await self.exchange.publish(message, routing_key=event.type)


_publisher: Publisher | None = None


async def publish_event(event: CloudEvent) -> None:
    global _publisher
    if _publisher is None:
        _publisher = Publisher(settings().rabbitmq_url)
    await _publisher.publish(event)
