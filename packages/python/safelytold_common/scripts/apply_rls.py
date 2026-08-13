"""One-time ops script: apply tenant RLS to every postgres-core service database.

Use on existing stacks (or after migrations in production) where the service
boot-time hook is not enough. Idempotent: safe to re-run. No-ops on databases
whose tables do not exist yet.

Note: RLS is bypassed for superuser connections. The dev stack connects as the
image-created superuser, so enforcement only fully matters in production, where
the application must use a non-superuser role (see infrastructure/postgres/
rls_reference.sql).

Example:
    $env:POSTGRES_PASSWORD='...' ; python -m scripts.apply_rls
"""

from __future__ import annotations

import asyncio
import os

from safelytold_common.rls import apply_tenant_rls
from sqlalchemy.ext.asyncio import create_async_engine

SERVICE_DATABASES = [
    'gateway', 'tenancy', 'identity', 'policy', 'intake', 'mailbox', 'case',
    'investigation', 'evidence', 'protection', 'support', 'analytics',
    'integration', 'notification', 'privacy', 'security_monitor',
    'ai_gateway', 'platform_api',
]


async def _apply(host: str, port: str, user: str, password: str, database: str) -> None:
    engine = create_async_engine(
        f'postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}',
        pool_pre_ping=True,
    )
    try:
        async with engine.begin() as connection:
            await apply_tenant_rls(connection)
    finally:
        await engine.dispose()
    print(f'RLS ok: {database}')


async def main() -> None:
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    user = os.getenv('POSTGRES_USER', 'safelytold')
    password = os.getenv('POSTGRES_PASSWORD', 'safelytold_dev_only')
    for database in SERVICE_DATABASES:
        await _apply(host, port, user, password, database)


if __name__ == '__main__':
    asyncio.run(main())
