from __future__ import annotations

import logging

from .base import MessagingProvider, NeutralMessage, ProviderName, SendResult, SendStatus

logger = logging.getLogger('safelytold.messaging')


class LogProvider(MessagingProvider):
    """Development/no-relay transport that only records metadata, never bodies.

    Use when no SMTP/Mailpit relay is available (unit tests, CI, local demo).
    """

    name = ProviderName.LOG

    def __init__(self, sent: list[NeutralMessage] | None = None) -> None:
        self.sent: list[NeutralMessage] = sent if sent is not None else []

    async def send(self, message: NeutralMessage) -> SendResult:
        self.sent.append(message)
        logger.info(
            'neutral notification [%s] to=%s locale=%s subject_len=%d body_len=%d',
            message.template_code,
            message.destination_ref,
            message.locale,
            len(message.subject),
            len(message.body),
        )
        return SendResult(status=SendStatus.SENT)

    async def check(self) -> SendResult:
        return SendResult(status=SendStatus.SENT)
