from __future__ import annotations

import asyncio
from typing import Annotated, Any
from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException
from jwt import PyJWKClient

from .config import Settings, settings
from .context import RequestContext, request_context

_jwks_clients: dict[str, PyJWKClient] = {}


def _claims(token: str, cfg: Settings) -> dict[str, Any]:
    jwks_url = f"{cfg.jwt_issuer.rstrip('/')}/protocol/openid-connect/certs"
    client = _jwks_clients.setdefault(jwks_url, PyJWKClient(jwks_url, cache_keys=True, lifespan=300))
    signing_key = client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=['RS256', 'ES256'],
        audience=cfg.jwt_audience,
        issuer=cfg.jwt_issuer,
        options={'require': ['exp', 'iat', 'iss', 'sub']},
    )


def _roles(claims: dict[str, Any]) -> frozenset[str]:
    realm = claims.get('realm_access') or {}
    resource = claims.get('resource_access') or {}
    client_roles: list[str] = []
    for value in resource.values():
        if isinstance(value, dict):
            client_roles.extend(value.get('roles') or [])
    return frozenset([*(realm.get('roles') or []), *client_roles])


async def get_context(
    authorization: Annotated[str | None, Header()] = None,
    x_tenant_id: Annotated[str | None, Header()] = None,
    x_purpose: Annotated[str | None, Header()] = None,
    x_dev_subject: Annotated[str | None, Header()] = None,
    x_dev_roles: Annotated[str | None, Header()] = None,
    cfg: Settings = Depends(settings),
) -> RequestContext:
    if cfg.dev_auth_bypass:
        context = RequestContext(
            tenant_id=UUID(x_tenant_id or cfg.dev_tenant_id),
            subject_id=x_dev_subject or 'development-user',
            roles=frozenset((x_dev_roles or 'platform_developer').split(',')),
            purpose=x_purpose or 'development',
        )
        request_context.set(context)
        return context

    if not authorization or not authorization.lower().startswith('bearer '):
        raise HTTPException(401, 'Bearer token required')
    token = authorization.split(' ', 1)[1]
    try:
        claims = await asyncio.to_thread(_claims, token, cfg)
        tenant_value = claims.get('tenant_id') or x_tenant_id
        if not tenant_value:
            raise HTTPException(403, 'Tenant claim required')
        purpose = x_purpose or claims.get('purpose')
        if not purpose:
            raise HTTPException(403, 'Purpose header required')
        context = RequestContext(
            tenant_id=UUID(str(tenant_value)),
            subject_id=str(claims['sub']),
            roles=_roles(claims),
            purpose=str(purpose),
            case_ids=frozenset(UUID(x) for x in claims.get('case_ids', [])),
        )
        request_context.set(context)
        return context
    except HTTPException:
        raise
    except (jwt.PyJWTError, ValueError, KeyError) as exc:
        raise HTTPException(401, 'Invalid access token') from exc


ContextDep = Annotated[RequestContext, Depends(get_context)]
