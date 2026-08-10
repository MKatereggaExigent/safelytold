from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID


class ProviderName(StrEnum):
    LOG = 'log'
    MAILCATCHER = 'mailcatcher'
    SMTP = 'smtp'


class SendStatus(StrEnum):
    QUEUED = 'queued'
    SENT = 'sent'
    FAILED = 'failed'


@dataclass(slots=True)
class NeutralMessage:
    """A zero-case-content notification destined for a reporter or staff member.

    subject and body must contain no case content, identifiers or PII. The
    neutrality contract is enforced by the template layer before send.
    """

    destination_ref: str
    subject: str
    body: str
    template_code: str
    locale: str
    correlation_id: UUID
    tenant_id: UUID | None = None
    reply_to: str | None = None


@dataclass(slots=True)
class SendResult:
    status: SendStatus
    provider_message_id: str | None = None
    error: str | None = None
    raw: dict[str, object] = field(default_factory=dict)


class MessagingProvider:
    name: ProviderName

    async def send(self, message: NeutralMessage) -> SendResult:
        raise NotImplementedError

    async def check(self) -> SendResult:
        raise NotImplementedError
