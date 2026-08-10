from __future__ import annotations

from .base import MessagingProvider, ProviderName
from .smtp import SMTPConfig, SMTPProvider


class MailcatcherProvider(SMTPProvider):
    """Local dev-only relay (Mailpit/Mailcatcher) on 1025, no TLS, no auth.

    Never used in production: certificate-less by design and clearly named.
    """

    name = ProviderName.MAILCATCHER

    def __init__(self, host: str = 'mailcatcher', port: int = 1025, from_address: str = 'no-reply@dev.invalid') -> None:
        super().__init__(
            SMTPConfig(
                host=host,
                port=port,
                from_address=from_address,
                use_tls=False,
                use_ssl=False,
                require_verified_cert=False,
            )
        )
