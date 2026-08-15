"""Short-lived, server-issued context for tenant-bound reporter journeys.

This token identifies a reporting channel and tenant, never a reporter. It is
separate from staff OIDC and from the later anonymous-mailbox credential.
"""
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException

from .config import settings

ISSUER = 'safelytold-reporter-access'
AUDIENCE = 'safelytold-intake'


class ReporterAccess:
    def __init__(self, tenant_id: UUID, tenant_slug: str, tenant_name: str, channel: str,
                 modes: frozenset[str], eligibility_class: str) -> None:
        self.tenant_id = tenant_id
        self.tenant_slug = tenant_slug
        self.tenant_name = tenant_name
        self.channel = channel
        self.modes = modes
        self.eligibility_class = eligibility_class


def _secret() -> str:
    value = settings().reporter_jwt_secret
    if not value:
        raise RuntimeError('REPORTER_JWT_SECRET must be configured')
    return value


def create_reporter_access(*, tenant_id: UUID, tenant_slug: str, tenant_name: str,
                           channel: str, modes: list[str], eligibility_class: str,
                           lifetime: timedelta = timedelta(minutes=30)) -> str:
    now = datetime.now(UTC)
    claims: dict[str, Any] = {
        'iss': ISSUER, 'aud': AUDIENCE, 'iat': now, 'exp': now + lifetime,
        'tenant_id': str(tenant_id), 'tenant_slug': tenant_slug,
        'tenant_name': tenant_name, 'channel': channel,
        'modes': modes, 'eligibility_class': eligibility_class,
    }
    return jwt.encode(claims, _secret(), algorithm='HS256')


def decode_reporter_access(token: str) -> ReporterAccess:
    try:
        claims = jwt.decode(token, _secret(), algorithms=['HS256'], audience=AUDIENCE, issuer=ISSUER)
        return ReporterAccess(
            tenant_id=UUID(str(claims['tenant_id'])), tenant_slug=str(claims['tenant_slug']),
            tenant_name=str(claims['tenant_name']), channel=str(claims['channel']),
            modes=frozenset(str(value) for value in claims['modes']),
            eligibility_class=str(claims['eligibility_class']),
        )
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(401, 'Invalid or expired reporting session') from exc


async def get_reporter_access(authorization: Annotated[str | None, Header()] = None) -> ReporterAccess:
    if not authorization or not authorization.lower().startswith('bearer '):
        raise HTTPException(401, 'A tenant reporting session is required')
    return decode_reporter_access(authorization.split(' ', 1)[1])


ReporterAccessDep = Annotated[ReporterAccess, Depends(get_reporter_access)]
