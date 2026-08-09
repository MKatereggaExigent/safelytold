"""Reporter-realm authentication.

Anonymous/confidential reporters hold a short-lived HS256 JWT issued by the
reporter-identity service after they prove possession of the recovery secret.
The token is bound to the pseudonymous handle and the case it belongs to, so a
reporter can only ever reach their own mailbox. The same module both issues and
verifies these tokens; both sides must be configured with the same
``REPORTER_JWT_SECRET``.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException

REPORTER_ISSUER = 'safelytold-reporter'
REPORTER_AUDIENCE = 'safelytold-reporter'
REPORTER_SESSION_TTL = timedelta(minutes=30)


def _secret() -> str:
    value = os.getenv('REPORTER_JWT_SECRET', '').strip()
    if not value:
        raise RuntimeError('REPORTER_JWT_SECRET must be configured for reporter authentication')
    return value


class ReporterContext:
    def __init__(self, case_id: UUID, handle_id: str, public_code: str, tenant_id: UUID | None) -> None:
        self.case_id = case_id
        self.handle_id = handle_id
        self.public_code = public_code
        self.tenant_id = tenant_id


def create_reporter_token(
    case_id: UUID,
    public_code: str,
    handle_id: str,
    tenant_id: UUID | None,
    secret: str | None = None,
    ttl: timedelta = REPORTER_SESSION_TTL,
) -> str:
    now = datetime.now(UTC)
    claims: dict[str, Any] = {
        'sub': handle_id,
        'public_code': public_code,
        'case_id': str(case_id),
        'iss': REPORTER_ISSUER,
        'aud': REPORTER_AUDIENCE,
        'iat': now,
        'exp': now + ttl,
    }
    if tenant_id is not None:
        claims['tenant_id'] = str(tenant_id)
    return jwt.encode(claims, secret or _secret(), algorithm='HS256')


def decode_reporter_token(token: str) -> ReporterContext:
    try:
        claims = jwt.decode(
            token,
            _secret(),
            algorithms=['HS256'],
            audience=REPORTER_AUDIENCE,
            issuer=REPORTER_ISSUER,
            options={'require': ['exp', 'iat', 'iss', 'sub', 'case_id']},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(401, 'Invalid or expired reporter session') from exc
    tenant_value = claims.get('tenant_id')
    return ReporterContext(
        case_id=UUID(str(claims['case_id'])),
        handle_id=str(claims['sub']),
        public_code=str(claims.get('public_code', '')),
        tenant_id=UUID(str(tenant_value)) if tenant_value else None,
    )


async def get_reporter(authorization: Annotated[str | None, Header()] = None) -> ReporterContext:
    if not authorization or not authorization.lower().startswith('bearer '):
        raise HTTPException(401, 'Reporter bearer token required')
    return decode_reporter_token(authorization.split(' ', 1)[1])


ReporterDep = Annotated[ReporterContext, Depends(get_reporter)]
