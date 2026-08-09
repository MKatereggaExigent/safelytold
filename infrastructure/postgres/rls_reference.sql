-- Apply a variation of this policy in every tenant-bearing service database.
ALTER TABLE domain_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE domain_records FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON domain_records
USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);

ALTER TABLE outbox_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE outbox_events FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_outbox ON outbox_events
USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
