from __future__ import annotations

import json
from uuid import UUID

from safelytold_common.config import settings
from safelytold_common.db import session_factory
from sqlalchemy import select

from .admin import Tenant


async def seed_tenants_from_env() -> None:
    """Provision tenants declared in SEED_TENANTS (config/env seed).

    Idempotent: skips slugs that already exist. The declared id is the stable
    tenant_id used by Keycloak claims and row-level security.
    """
    cfg = settings()
    raw = (cfg.seed_tenants or '').strip()
    if not raw or raw == '[]':
        return
    try:
        rows = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError('SEED_TENANTS must be valid JSON: a list of tenant objects') from exc
    if not isinstance(rows, list):
        raise RuntimeError('SEED_TENANTS must be a JSON list of tenant objects')

    async with session_factory()() as database:
        for row in rows:
            slug = row.get('slug')
            tenant_id = row.get('id')
            if not slug or not tenant_id:
                raise RuntimeError(f'SEED_TENANTS entry missing slug or id: {row!r}')
            try:
                tenant_id = UUID(str(tenant_id))
            except ValueError as exc:
                raise RuntimeError(f'SEED_TENANTS entry has invalid id: {tenant_id!r}') from exc
            existing = await database.scalar(select(Tenant).where(Tenant.slug == slug))
            if existing is not None:
                continue
            database.add(
                Tenant(
                    id=tenant_id,
                    slug=slug,
                    display_name=row['display_name'],
                    home_region=row['home_region'],
                    tenancy_tier=row.get('tenancy_tier', 'shared_database'),
                )
            )
        await database.commit()
