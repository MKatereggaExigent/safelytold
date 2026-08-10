from __future__ import annotations

import asyncio
import smtplib
import ssl
from email.message import EmailMessage

from .base import MessagingProvider, NeutralMessage, ProviderName, SendResult, SendStatus


class SMTPConfig:
    def __init__(
        self,
        host: str,
        port: int,
        *,
        username: str | None = None,
        password: str | None = None,
        from_address: str,
        use_tls: bool = True,
        use_ssl: bool = False,
        require_verified_cert: bool = True,
        timeout: float = 30.0,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_address = from_address
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.require_verified_cert = require_verified_cert
        self.timeout = timeout


class SMTPProvider(MessagingProvider):
    """TLS-ready SMTP transport for neutral notifications.

    STARTTLS is used unless use_ssl requests an implicit-TLS port (465).
    Certificate verification is on by default; set require_verified_cert=False
    only for dev-only relays, never for production delivery.
    """

    name = ProviderName.SMTP

    def __init__(self, config: SMTPConfig) -> None:
        self.config = config

    def _connect(self) -> smtplib.SMTP:
        if self.config.use_ssl:
            context = ssl.create_default_context()
            client: smtplib.SMTP = smtplib.SMTP_SSL(
                self.config.host, self.config.port, timeout=self.config.timeout, context=context
            )
        else:
            client = smtplib.SMTP(self.config.host, self.config.port, timeout=self.config.timeout)
            client.ehlo()
            if self.config.use_tls:
                if self.config.require_verified_cert:
                    context = ssl.create_default_context()
                else:
                    context = ssl._create_unverified_context()
                client.starttls(context=context)
                client.ehlo()
        if self.config.username and self.config.password:
            client.login(self.config.username, self.config.password)
        return client

    def _send_sync(self, message: NeutralMessage) -> SendResult:
        try:
            client = self._connect()
            try:
                email = EmailMessage()
                email['From'] = self.config.from_address
                email['To'] = message.destination_ref
                if message.reply_to:
                    email['Reply-To'] = message.reply_to
                email['Subject'] = message.subject
                email.set_content(message.body)
                client.send_message(email)
            finally:
                client.quit()
            return SendResult(status=SendStatus.SENT)
        except Exception as exc:  # noqa: BLE001 - surfaced for retry handling
            return SendResult(status=SendStatus.FAILED, error=f'{type(exc).__name__}: {exc}')

    async def send(self, message: NeutralMessage) -> SendResult:
        return await asyncio.to_thread(self._send_sync, message)

    async def check(self) -> SendResult:
        def probe() -> SendResult:
            try:
                client = self._connect()
                client.quit()
                return SendResult(status=SendStatus.SENT)
            except Exception as exc:  # noqa: BLE001
                return SendResult(status=SendStatus.FAILED, error=f'{type(exc).__name__}: {exc}')

        return await asyncio.to_thread(probe)
