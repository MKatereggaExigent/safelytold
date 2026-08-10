from __future__ import annotations

from functools import lru_cache

from .base import MessagingProvider, ProviderName
from .log import LogProvider
from .mailcatcher import MailcatcherProvider
from .smtp import SMTPConfig, SMTPProvider


class MessagingConfig:
    def __init__(
        self,
        provider: ProviderName = ProviderName.LOG,
        *,
        smtp_host: str = '',
        smtp_port: int = 587,
        smtp_username: str | None = None,
        smtp_password: str | None = None,
        smtp_from: str = '',
        smtp_use_tls: bool = True,
        smtp_use_ssl: bool = False,
        smtp_require_verified_cert: bool = True,
        mailcatcher_host: str = 'mailcatcher',
        mailcatcher_port: int = 1025,
        mailcatcher_from: str = 'no-reply@dev.invalid',
    ) -> None:
        self.provider = provider
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.smtp_from = smtp_from
        self.smtp_use_tls = smtp_use_tls
        self.smtp_use_ssl = smtp_use_ssl
        self.smtp_require_verified_cert = smtp_require_verified_cert
        self.mailcatcher_host = mailcatcher_host
        self.mailcatcher_port = mailcatcher_port
        self.mailcatcher_from = mailcatcher_from

    @classmethod
    def from_env(cls) -> 'MessagingConfig':
        from os import getenv

        provider = getenv('MESSAGING_PROVIDER', 'log')
        try:
            provider_enum = ProviderName(provider.lower())
        except ValueError:
            provider_enum = ProviderName.LOG
        return cls(
            provider=provider_enum,
            smtp_host=getenv('SMTP_HOST', ''),
            smtp_port=int(getenv('SMTP_PORT', '587')),
            smtp_username=getenv('SMTP_USERNAME') or None,
            smtp_password=getenv('SMTP_PASSWORD') or None,
            smtp_from=getenv('SMTP_FROM', ''),
            smtp_use_tls=getenv('SMTP_USE_TLS', 'true').lower() == 'true',
            smtp_use_ssl=getenv('SMTP_USE_SSL', 'false').lower() == 'true',
            smtp_require_verified_cert=getenv('SMTP_REQUIRE_VERIFIED_CERT', 'true').lower() == 'true',
            mailcatcher_host=getenv('MAILCATCHER_HOST', 'mailcatcher'),
            mailcatcher_port=int(getenv('MAILCATCHER_PORT', '1025')),
            mailcatcher_from=getenv('MAILCATCHER_FROM', 'no-reply@dev.invalid'),
        )


@lru_cache
def get_provider(config: MessagingConfig | None = None) -> MessagingProvider:
    cfg = config or MessagingConfig.from_env()
    if cfg.provider == ProviderName.MAILCATCHER:
        return MailcatcherProvider(cfg.mailcatcher_host, cfg.mailcatcher_port, cfg.mailcatcher_from)
    if cfg.provider == ProviderName.SMTP:
        return SMTPProvider(
            SMTPConfig(
                host=cfg.smtp_host,
                port=cfg.smtp_port,
                username=cfg.smtp_username,
                password=cfg.smtp_password,
                from_address=cfg.smtp_from,
                use_tls=cfg.smtp_use_tls,
                use_ssl=cfg.smtp_use_ssl,
                require_verified_cert=cfg.smtp_require_verified_cert,
            )
        )
    return LogProvider()


def reset_provider_for_tests() -> None:
    get_provider.cache_clear()
