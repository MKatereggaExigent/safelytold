from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

ISOLATION_EXPRESSION = "tenant_id = current_setting('app.tenant_id', true)::uuid"

# domain_records is FORCE-ROW-LEVEL-SECURITY: even the table owner (the service
# role) is subject to the tenant policy, so isolation is enforced by the database,
# not just by application-level WHERE filters.
#
# outbox_events is ENABLE-but-not-FORCE: the shared outbox relay scans rows across
# all tenants without a per-tenant session, so the owner must still be able to
# read every pending row. The payload there is content-free metadata only.
#
# Tables are matched by existence so this is safe to run on any service database,
# before or after migrations, and on every boot (idempotent).
TABLES = (
    ('domain_records', 'tenant_isolation', True),
    ('outbox_events', 'tenant_isolation_outbox', False),
)


async def _table_exists(connection: AsyncConnection, table: str) -> bool:
    result = await connection.scalar(
        text("SELECT to_regclass('public.' || :name) IS NOT NULL"),
        {'name': table},
    )
    return bool(result)


async def _policy_exists(connection: AsyncConnection, table: str, policy: str) -> bool:
    result = await connection.scalar(
        text(
            "SELECT 1 FROM pg_policies "
            "WHERE schemaname = 'public' AND tablename = :table AND policyname = :policy LIMIT 1"
        ),
        {'table': table, 'policy': policy},
    )
    return bool(result)


async def apply_tenant_rls(connection: AsyncConnection) -> None:
    """Enable tenant row-level security on the service database.

    Idempotent and safe to call on every boot; no-ops when the tables do not
    exist yet. Runs inside the caller's transaction/connection.
    """
    for table, policy, force in TABLES:
        if not await _table_exists(connection, table):
            continue
        await connection.execute(text(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY'))
        if force:
            await connection.execute(text(f'ALTER TABLE {table} FORCE ROW LEVEL SECURITY'))
        if not await _policy_exists(connection, table, policy):
            # Names come from the fixed TABLES constant; never from user input.
            await connection.execute(
                text(
                    f'CREATE POLICY {policy} ON {table} '
                    f'USING ({ISOLATION_EXPRESSION}) WITH CHECK ({ISOLATION_EXPRESSION})'
                )
            )
