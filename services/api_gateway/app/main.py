"""safelytold API Gateway.

Single entry point (default port 9085) for the whole backend. It is a thin
reverse proxy that maps ``/gateway/{service}/...`` to each bounded-context
service and exposes a small gateway-native surface (service map, aggregate
health). All security is enforced downstream by the services themselves.

The service route table can be overridden with individual ``*_SERVICE_URL``
environment variables (for example ``EVIDENCE_SERVICE_URL``) or wholesale with
the ``GATEWAY_SERVICE_URLS`` JSON variable. Defaults assume the Docker Compose
network where every service advertises its internal hostname.
"""

from __future__ import annotations

import json
import os

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from safelytold_common.service import create_app

router = APIRouter(prefix='/v1', tags=['gateway'])

# Service slug -> upstream base URL. The frontend reaches every bounded context
# through this gateway, so only the gateway port is exposed to clients.
DEFAULT_ROUTES: dict[str, str] = {
    'tenancy': 'http://tenancy-service:8010',
    'identity': 'http://identity-service:8011',
    'reporter-identity': 'http://reporter-identity-service:8012',
    'policy': 'http://policy-service:8013',
    'intake': 'http://intake-service:8014',
    'mailbox': 'http://mailbox-service:8015',
    'case': 'http://case-service:8016',
    'investigation': 'http://investigation-service:8017',
    'evidence': 'http://evidence-service:8018',
    'protection': 'http://protection-service:8019',
    'support': 'http://support-service:8020',
    'analytics': 'http://analytics-service:8021',
    'integration': 'http://integration-service:8022',
    'notification': 'http://notification-service:8023',
    'privacy': 'http://privacy-service:8024',
    'audit': 'http://audit-service:8025',
    'security': 'http://security-monitor-service:8026',
    'ai': 'http://ai-gateway:8027',
    'ledger': 'http://blockchain-ledger-service:8028',
}

# Allow per-service override via *_SERVICE_URL env vars and a JSON blob.
_OVERRIDES: dict[str, str] = {
    k.removesuffix('_SERVICE_URL').lower(): v
    for k, v in os.environ.items()
    if k.endswith('_SERVICE_URL')
}
_JSON_OVERRIDES: dict[str, str] = {}
if os.environ.get('GATEWAY_SERVICE_URLS'):
    try:
        parsed = json.loads(os.environ['GATEWAY_SERVICE_URLS'])
        _JSON_OVERRIDES = {str(k).lower(): str(v) for k, v in parsed.items()}
    except (ValueError, TypeError):
        pass

SERVICE_ROUTES: dict[str, str] = {**DEFAULT_ROUTES, **_OVERRIDES, **_JSON_OVERRIDES}

# Headers that must never be forwarded upstream (hop-by-hop or host-specific).
HOP_BY_HOP = {
    'host',
    'content-length',
    'connection',
    'keep-alive',
    'proxy-authenticate',
    'proxy-authorization',
    'te',
    'trailer',
    'transfer-encoding',
    'upgrade',
}


@router.get('/services')
async def service_map() -> dict[str, str]:
    return dict(sorted(SERVICE_ROUTES.items()))


@router.get('/health/aggregate')
async def aggregate() -> dict:
    return {'services': await _gather_health(SERVICE_ROUTES)}


async def _gather_health(routes: dict[str, str]) -> dict[str, dict]:
    import asyncio

    async with httpx.AsyncClient(timeout=2) as client:
        async def one(name: str, base: str) -> tuple[str, dict]:
            try:
                return name, (await client.get(base.rstrip('/') + '/health')).json()
            except Exception as exc:  # noqa: BLE001 - a failing upstream is reported, never fatal
                return name, {'status': 'unavailable', 'error_type': type(exc).__name__}

        return dict(await asyncio.gather(*(one(n, u) for n, u in routes.items())))


@router.api_route('/gateway/{service}/{path:path}', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD'])
async def proxy(service: str, path: str, request: Request) -> Response:
    base = SERVICE_ROUTES.get(service)
    if base is None:
        raise HTTPException(404, f"Unknown upstream service '{service}'")
    if not path:
        raise HTTPException(404, 'Upstream path required')

    url = f"{base.rstrip('/')}/{path}"
    if request.url.query:
        url = f'{url}?{request.url.query}'

    body = await request.body()
    headers = {
        k: v for k, v in request.headers.items() if k.lower() not in HOP_BY_HOP
    }
    headers.pop('x-forwarded-proto', None)
    headers.pop('x-forwarded-for', None)

    timeout = httpx.Timeout(600, connect=10)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            upstream = await client.request(request.method, url, headers=headers, content=body)
        except httpx.HTTPError as exc:
            raise HTTPException(502, f'Upstream unavailable ({type(exc).__name__})') from exc

    response_headers = {}
    for key in ('content-type', 'content-disposition', 'location', 'etag', 'cache-control', 'pragma', 'x-content-type-options'):
        value = upstream.headers.get(key)
        if value:
            response_headers[key] = value
    return Response(content=upstream.content, status_code=upstream.status_code, headers=response_headers)


def _cors_origins() -> list[str]:
    raw = os.environ.get('CORS_ORIGINS', '*')
    return [o.strip() for o in raw.split(',') if o.strip()]


app = create_app(
    'safelytold API Gateway',
    'Single backend entry point; routes /gateway/{service} to each bounded context. Domains stay authoritative.',
    [router],
)

# Browser clients are served from a different origin (frontend proxy on :9000),
# so the gateway must answer CORS preflights and add the allow headers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
    expose_headers=['content-type', 'content-disposition', 'etag', 'location'],
)
