'use client';

import { useState } from 'react';
import { Alert, Badge, Button, DataTable, EmptyState, Field, Input, PageHeader, Panel, Select, StatusPill, Textarea } from '@safelytold/ui/components';
import { createRecord } from '@safelytold/ui/api';
import { useSession } from '@safelytold/ui/context';
import { useToast } from '@safelytold/ui/context';
import { formatDate, useRecords } from '@safelytold/ui/hooks';
import { STAFF_ROLES } from '../../lib/staff';

const INTEGRATION_KINDS = ['hris_sync', 'sso_scim', 'notification_adapter', 'eap_referral', 'webhook'];

export default function AdminPage() {
  const { session } = useSession();
  const { push } = useToast();
  const { records: policies, loading: policiesLoading, refresh: refreshPolicies } = useRecords('policy');
  const { records: organisations } = useRecords('tenancy');
  const { records: integrations, refresh: refreshIntegrations } = useRecords('integration');

  const [policyName, setPolicyName] = useState('');
  const [policyVersion, setPolicyVersion] = useState('1.0.0');
  const [policyRules, setPolicyRules] = useState('');
  const [integrationKind, setIntegrationKind] = useState(INTEGRATION_KINDS[0]);
  const [integrationTarget, setIntegrationTarget] = useState('');
  const [saving, setSaving] = useState(false);

  async function createPolicyPack() {
    if (!policyName.trim() || !policyRules.trim()) {
      push('Provide a name and the policy rules', 'warn');
      return;
    }
    setSaving(true);
    try {
      await createRecord('policy', 'policy_pack', {
        name: policyName.trim(),
        version: policyVersion.trim(),
        rules: policyRules.trim().split('\n').map((l) => l.trim()).filter(Boolean),
        status: 'draft',
        created_at: new Date().toISOString(),
      }, session);
      push('Policy pack saved as draft', 'ok');
      setPolicyName('');
      setPolicyRules('');
      refreshPolicies();
    } catch (err) {
      push(err instanceof Error ? err.message : 'Could not save policy pack', 'danger');
    } finally {
      setSaving(false);
    }
  }

  async function createIntegration() {
    if (!integrationTarget.trim()) {
      push('Provide the integration target', 'warn');
      return;
    }
    setSaving(true);
    try {
      await createRecord('integration', integrationKind, {
        target: integrationTarget.trim(),
        status: 'configured',
        created_at: new Date().toISOString(),
      }, session);
      push('Integration registered', 'ok');
      setIntegrationTarget('');
      refreshIntegrations();
    } catch (err) {
      push(err instanceof Error ? err.message : 'Could not register integration', 'danger');
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="shell">
      <PageHeader
        eyebrow="Administration"
        title="Tenant configuration"
        subtitle="Subscription administration is separate from case authority — configuring the platform never grants case access."
      />

      <Alert tone="info" title="Separation of duties">
        <p>
          A tenant owner can configure policies and integrations but cannot read cases. Raw case access requires a
          separate assignment, purpose and conflict check.
        </p>
      </Alert>

      <div className="split">
        <Panel title="Policy packs">
          <Field label="Pack name" required>
            <Input value={policyName} onChange={(e) => setPolicyName(e.target.value)} autoComplete="off" />
          </Field>
          <Field label="Version">
            <Select value={policyVersion} onChange={(e) => setPolicyVersion(e.target.value)}>
              {['0.9.0', '1.0.0', '1.1.0', '2.0.0'].map((v) => <option key={v} value={v}>{v}</option>)}
            </Select>
          </Field>
          <Field label="Rules (one per line)" required hint="e.g. ‘dual approval required for identity reveal’">
            <Textarea rows={5} value={policyRules} onChange={(e) => setPolicyRules(e.target.value)} />
          </Field>
          <Button onClick={createPolicyPack} loading={saving}>Save policy pack</Button>
        </Panel>

        <Panel title="Integrations">
          <Field label="Kind">
            <Select value={integrationKind} onChange={(e) => setIntegrationKind(e.target.value)}>
              {INTEGRATION_KINDS.map((k) => <option key={k} value={k}>{k.replace(/_/g, ' ')}</option>)}
            </Select>
          </Field>
          <Field label="Target">
            <Input value={integrationTarget} onChange={(e) => setIntegrationTarget(e.target.value)} placeholder="Endpoint or provider reference" autoComplete="off" />
          </Field>
          <Button onClick={createIntegration} loading={saving}>Register integration</Button>
          <p className="muted" style={{ marginTop: 10 }}>
            Integration payloads carry references, never raw allegation content.
          </p>
        </Panel>
      </div>

      <div className="stack" style={{ marginTop: 20 }}>
        <Panel title="Policy packs" subtitle={policiesLoading ? 'Loading…' : undefined} padded={false}>
          <DataTable
            keyField="id"
            loading={policiesLoading}
            empty={<EmptyState title="No policy packs" description="Saved packs appear here." />}
            columns={[
              { key: 'name', label: 'Name', render: (r) => <strong>{(r.payload as Record<string, unknown>).name as string}</strong> },
              { key: 'version', label: 'Version', render: (r) => <Badge tone="accent">v{(r.payload as Record<string, unknown>).version as string}</Badge> },
              { key: 'rules', label: 'Rules', render: (r) => <span className="muted">{((r.payload as Record<string, unknown>).rules as string[] | undefined)?.length ?? 0} rules</span> },
              { key: 'status', label: 'Status', render: (r) => <StatusPill status={r.status} /> },
              { key: 'created_at', label: 'Saved', render: (r) => <span className="muted">{formatDate((r.payload as Record<string, unknown>).created_at as string)}</span> },
            ]}
            rows={policies}
          />
        </Panel>

        <div className="split">
          <Panel title="Organisations" padded={false}>
            <DataTable
              keyField="id"
              empty={<EmptyState title="No organisations" description="Tenancy records appear here." />}
              columns={[
                { key: 'id', label: 'Ref', render: (r) => <span className="mono">{r.id.slice(0, 8)}</span> },
                { key: 'kind', label: 'Kind', render: (r) => <Badge tone="neutral">{r.kind}</Badge> },
                { key: 'status', label: 'Status', render: (r) => <StatusPill status={r.status} /> },
              ]}
              rows={organisations}
            />
          </Panel>
          <Panel title="Integrations" padded={false}>
            <DataTable
              keyField="id"
              empty={<EmptyState title="No integrations" description="Registered integrations appear here." />}
              columns={[
                { key: 'kind', label: 'Kind', render: (r) => <Badge tone="info">{r.kind.replace(/_/g, ' ')}</Badge> },
                { key: 'target', label: 'Target', render: (r) => <span className="muted">{(r.payload as Record<string, unknown>).target as string}</span> },
                { key: 'status', label: 'Status', render: (r) => <StatusPill status={r.status} /> },
              ]}
              rows={integrations}
            />
          </Panel>
        </div>

        <Panel title="Role matrix" subtitle="RBAC for coarse duties; assignment, purpose and conflict rules still apply">
          <div className="row" style={{ flexWrap: 'wrap', gap: 8 }}>
            {STAFF_ROLES.map((r) => (
              <Badge key={r.value} tone="neutral">{r.label}</Badge>
            ))}
          </div>
        </Panel>
      </div>
    </main>
  );
}
