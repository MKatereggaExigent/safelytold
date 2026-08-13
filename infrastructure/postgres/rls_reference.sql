-- Reference for the tenant row-level-security policy now applied automatically
-- by safelytold_common.rls.apply_tenant_rls() on every service boot (and by
-- scripts/apply_rls.py for existing databases). This file documents the DDL.
--
-- IMPORTANT: PostgreSQL superusers bypass row-level security entirely (even with
-- FORCE). The dev stack's `safelytold` role is the image-created superuser, so
-- RLS is only truly enforced in production where the application connects as a
-- non-superuser role. Services set the tenant per transaction via
-- set_config('app.tenant_id', ...), and fail closed when it is unset.
--
-- domain_records is FORCE ROW LEVEL SECURITY: even the table owner (the service
-- role) is subject to the policy, so tenant isolation is enforced by the
-- database rather than only by application-level WHERE filters.
ALTER TABLE domain_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE domain_records FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON domain_records
USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);

-- outbox_events is ENABLE but NOT FORCE: the shared outbox relay scans pending
-- rows across every tenant without a per-tenant session, so the owner must
-- still be able to read all rows. The payload here is content-free metadata.
ALTER TABLE outbox_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_outbox ON outbox_events
USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
