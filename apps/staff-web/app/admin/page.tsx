'use client';

import { useEffect, useState } from 'react';
import {
  Alert,
  Badge,
  Button,
  DataTable,
  EmptyState,
  Field,
  Input,
  PageHeader,
  Panel,
  Segmented,
  Select,
  StatusPill,
  Textarea,
} from '@safelytold/ui/components';
import { createRecord } from '@safelytold/ui/api';
import { useSession } from '@safelytold/ui/context';
import { useToast } from '@safelytold/ui/context';
import { formatDate, useRecords } from '@safelytold/ui/hooks';
import { STAFF_ROLES } from '../../lib/staff';
import {
  createTenant,
  createLegalEntity,
  createOrganisationalUnit,
  getEmailSettings,
  isSuperuser,
  listTenants,
  listLegalEntities,
  listOrganisationalUnits,
  listTemplateOverrides,
  saveEmailSettings,
  saveTemplateOverride,
  testEmailSettings,
  type EmailSettingsView,
  type LegalEntityView,
  type OrganisationalUnitView,
  type TemplateOverrideView,
  type TenantView,
} from '../../lib/admin';

const INTEGRATION_KINDS = ['hris_sync', 'sso_scim', 'notification_adapter', 'eap_referral', 'webhook'];
const LOCALES = ['en', 'af', 'zu'];
const TEMPLATE_CODES = ['mailbox_nudge_v1'];

type DeliveryMode = 'tenant_smtp' | 'datasqan_relay';

export default function AdminPage() {
  const { session } = useSession();
  const { push } = useToast();
  const { records: policies, loading: policiesLoading, refresh: refreshPolicies } = useRecords('policy');
  const { records: organisations } = useRecords('tenancy');
  const { records: integrations, refresh: refreshIntegrations } = useRecords('integration');

  const superuser = isSuperuser(session);

  const [tenants, setTenants] = useState<TenantView[]>([]);
  const [legalEntities, setLegalEntities] = useState<LegalEntityView[]>([]);
  const [ou, setOu] = useState<OrganisationalUnitView[]>([]);
  const [settings, setSettings] = useState<EmailSettingsView | null>(null);
  const [overrides, setOverrides] = useState<TemplateOverrideView[]>([]);

  const [tenantName, setTenantName] = useState('');
  const [tenantSlug, setTenantSlug] = useState('');
  const [tenantRegion, setTenantRegion] = useState('eu-west-1');
  const [selectedTenantId, setSelectedTenantId] = useState('');

  const [deliveryMode, setDeliveryMode] = useState<DeliveryMode>('datasqan_relay');
  const [smtpHost, setSmtpHost] = useState('');
  const [smtpPort, setSmtpPort] = useState('587');
  const [smtpUsername, setSmtpUsername] = useState('');
  const [smtpPassword, setSmtpPassword] = useState('');
  const [fromAddress, setFromAddress] = useState('');
  const [defaultLocale, setDefaultLocale] = useState('en');

  const [overrideTenantId, setOverrideTenantId] = useState('');
  const [overrideTemplate, setOverrideTemplate] = useState(TEMPLATE_CODES[0]);
  const [overrideLocale, setOverrideLocale] = useState('en');
  const [overrideSubject, setOverrideSubject] = useState('');
  const [overrideBody, setOverrideBody] = useState('');

  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);

  async function loadTenants() {
    try {
      setTenants(await listTenants(session));
    } catch (err) {
      push(err instanceof Error ? err.message : 'Could not load tenants', 'danger');
    }
  }

  useEffect(() => {
    if (superuser) void loadTenants();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [superuser]);

  async function selectTenant(tenantId: string) {
    setSelectedTenantId(tenantId);
    setSettings(null);
    if (!tenantId) return;
    try {
      const [s, les, ous, ovs] = await Promise.all([
        getEmailSettings(tenantId, session),
        listLegalEntities(tenantId, session),
        listOrganisationalUnits(tenantId, session),
        listTemplateOverrides(tenantId, session),
      ]);
      setSettings(s);
      setLegalEntities(les);
      setOu(ous);
      setOverrides(ovs);
      setDeliveryMode(s.delivery_mode);
      setSmtpHost(s.smtp_host ?? '');
      setSmtpPort(String(s.smtp_port));
      setSmtpUsername(s.smtp_username ?? '');
      setFromAddress(s.from_address ?? '');
      setDefaultLocale(s.default_locale);
    } catch (err) {
      push(err instanceof Error ? err.message : 'Could not load tenant configuration', 'danger');
    }
  }

  async function createTenantFlow() {
    if (!tenantName.trim() || !tenantSlug.trim()) {
      push('Provide a tenant name and slug', 'warn');
      return;
    }
    setSaving(true);
    try {
      const t = await createTenant(
        { slug: tenantSlug.trim(), display_name: tenantName.trim(), home_region: tenantRegion },
        session,
      );
      push(`Tenant ${t.display_name} created`, 'ok');
      setTenantName('');
      setTenantSlug('');
      await loadTenants();
      await selectTenant(t.id);
    } catch (err) {
      push(err instanceof Error ? err.message : 'Could not create tenant', 'danger');
    } finally {
      setSaving(false);
    }
  }

  async function saveSettings() {
    if (!selectedTenantId) {
      push('Select a tenant first', 'warn');
      return;
    }
    setSaving(true);
    try {
      const updated = await saveEmailSettings(
        selectedTenantId,
        {
          delivery_mode: deliveryMode,
          smtp_host: deliveryMode === 'tenant_smtp' ? smtpHost : null,
          smtp_port: Number(smtpPort) || 587,
          smtp_username: deliveryMode === 'tenant_smtp' ? smtpUsername : null,
          smtp_password: smtpPassword || null,
          smtp_use_tls: true,
          from_address: fromAddress || null,
          default_locale: defaultLocale,
        },
        session,
      );
      setSettings(updated);
      setSmtpPassword('');
      push('Outbound email settings saved', 'ok');
    } catch (err) {
      push(err instanceof Error ? err.message : 'Could not save email settings', 'danger');
    } finally {
      setSaving(false);
    }
  }

  async function runTestSend() {
    if (!selectedTenantId) {
      push('Select a tenant first', 'warn');
      return;
    }
    setTesting(true);
    try {
      const updated = await testEmailSettings(selectedTenantId, session);
      setSettings(updated);
      if (updated.verification_status === 'verified') {
        push('Test email sent successfully', 'ok');
      } else {
        push(`Test send failed: ${updated.verification_detail ?? 'unknown'}`, 'danger');
      }
    } catch (err) {
      push(err instanceof Error ? err.message : 'Test send could not be run', 'danger');
    } finally {
      setTesting(false);
    }
  }

  async function saveOverride() {
    if (!overrideTenantId) {
      push('Select a tenant for the override', 'warn');
      return;
    }
    setSaving(true);
    try {
      await saveTemplateOverride(overrideTenantId, overrideTemplate, overrideLocale, {
        subject: overrideSubject.trim(),
        body: overrideBody.trim(),
      }, session);
      setOverrideSubject('');
      setOverrideBody('');
      setOverrides(await listTemplateOverrides(overrideTenantId, session));
      push('Neutral template override saved', 'ok');
    } catch (err) {
      push(err instanceof Error ? err.message : 'Could not save template override', 'danger');
    } finally {
      setSaving(false);
    }
  }

  const [policyName, setPolicyName] = useState('');
  const [policyVersion, setPolicyVersion] = useState('1.0.0');
  const [policyRules, setPolicyRules] = useState('');
  const [integrationKind, setIntegrationKind] = useState(INTEGRATION_KINDS[0]);
  const [integrationTarget, setIntegrationTarget] = useState('');

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
        title="Platform administration"
        subtitle="Subscription administration is separate from case authority — configuring the platform never grants case access."
      />

      {!superuser ? (
        <Alert tone="danger" title="Platform super-admin required">
          <p>
            This console is restricted to <code>platform_super_admin</code> users with a verified email in the
            platform allowlist (and, for real logins, a second factor configured in Keycloak).
          </p>
        </Alert>
      ) : (
        <>
          {session.isDev === true && (
            <Alert tone="info" title="Development bypass">
              <p>Development bypass is active; superuser privileges are assumed for this session.</p>
            </Alert>
          )}

          <Alert tone="info" title="Separation of duties">
            <p>
              A tenant owner can configure policies and integrations but cannot read cases. Raw case access requires a
              separate assignment, purpose and conflict check.
            </p>
          </Alert>

          <div className="split">
            <Panel title="Onboard a tenant">
              <Field label="Organisation name" required>
                <Input value={tenantName} onChange={(e) => setTenantName(e.target.value)} autoComplete="off" placeholder="Example Corp (Pty) Ltd" />
              </Field>
              <Field label="Slug" required hint="Lowercase, hyphens. Used to reference the tenant.">
                <Input value={tenantSlug} onChange={(e) => setTenantSlug(e.target.value)} autoComplete="off" placeholder="example-corp" />
              </Field>
              <Field label="Home region">
                <Select value={tenantRegion} onChange={(e) => setTenantRegion(e.target.value)}>
                  {['eu-west-1', 'us-east-1', 'af-south-1', 'ap-southeast-1'].map((r) => <option key={r} value={r}>{r}</option>)}
                </Select>
              </Field>
              <Button onClick={createTenantFlow} loading={saving}>Create tenant</Button>
            </Panel>

            <Panel title="Tenants">
              <DataTable
                keyField="id"
                loading={false}
                empty={<EmptyState title="No tenants" description="Onboarded corporations appear here." />}
                columns={[
                  { key: 'slug', label: 'Slug', render: (r) => <strong>{r.slug}</strong> },
                  { key: 'display_name', label: 'Organisation', render: (r) => r.display_name },
                  { key: 'home_region', label: 'Region', render: (r) => <Badge tone="neutral">{r.home_region}</Badge> },
                  { key: 'status', label: 'Status', render: (r) => <StatusPill status={r.status} /> },
                  { key: 'created_at', label: 'Created', render: (r) => <span className="muted">{formatDate(r.created_at)}</span> },
                ]}
                rows={tenants}
              />
            </Panel>
          </div>

          <Panel title="Outbound email" subtitle="Configure how notification nudges are delivered for a tenant">
            <Field label="Tenant">
              <Select value={selectedTenantId} onChange={(e) => void selectTenant(e.target.value)}>
                <option value="">Select a tenant…</option>
                {tenants.map((t) => <option key={t.id} value={t.id}>{t.display_name} ({t.slug})</option>)}
              </Select>
            </Field>

            {settings && (
              <>
                <div className="row" style={{ gap: 12, marginBottom: 16, alignItems: 'center', flexWrap: 'wrap' }}>
                  <StatusPill status={settings.verification_status} label={`Verification: ${settings.verification_status}`} />
                  {settings.has_credentials && <Badge tone="ok">SMTP credentials stored</Badge>}
                  {settings.verification_detail && <span className="muted">{settings.verification_detail}</span>}
                </div>

                <Segmented<DeliveryMode>
                  ariaLabel="Delivery mode"
                  value={deliveryMode}
                  onChange={setDeliveryMode}
                  options={[
                    { value: 'tenant_smtp', label: 'A · Tenant SMTP' },
                    { value: 'datasqan_relay', label: 'B · DataSqan relay' },
                  ]}
                />
                <p className="muted" style={{ marginTop: 8, marginBottom: 16 }}>
                  {deliveryMode === 'tenant_smtp'
                    ? 'The tenant supplies their own relay + credentials; DataSqan sends from their infrastructure.'
                    : 'DataSqan relays through the platform relay, sending under the tenant\'s sender identity.'}
                </p>

                <div className="split">
                  <div className="stack">
                    {deliveryMode === 'tenant_smtp' && (
                      <>
                        <Field label="SMTP host">
                          <Input value={smtpHost} onChange={(e) => setSmtpHost(e.target.value)} placeholder="smtp.corp.com" autoComplete="off" />
                        </Field>
                        <div className="split">
                          <Field label="Port">
                            <Input value={smtpPort} onChange={(e) => setSmtpPort(e.target.value)} autoComplete="off" />
                          </Field>
                          <Field label="Username">
                            <Input value={smtpUsername} onChange={(e) => setSmtpUsername(e.target.value)} autoComplete="off" />
                          </Field>
                        </div>
                        <Field label="Password" hint="Left blank to keep the stored value.">
                          <Input value={smtpPassword} onChange={(e) => setSmtpPassword(e.target.value)} type="password" autoComplete="new-password" />
                        </Field>
                      </>
                    )}
                    <Field label="Sender address (From)" hint="Used as the envelope From for this tenant's notifications.">
                      <Input value={fromAddress} onChange={(e) => setFromAddress(e.target.value)} placeholder="no-reply@example.com" autoComplete="off" />
                    </Field>
                    <Field label="Default locale">
                      <Select value={defaultLocale} onChange={(e) => setDefaultLocale(e.target.value)}>
                        {LOCALES.map((l) => <option key={l} value={l}>{l}</option>)}
                      </Select>
                    </Field>
                  </div>
                  <div className="stack">
                    <div className="row" style={{ gap: 10 }}>
                      <Button onClick={saveSettings} loading={saving}>Save settings</Button>
                      <Button variant="secondary" onClick={runTestSend} loading={testing}>Send test email</Button>
                    </div>
                  </div>
                </div>
              </>
            )}
          </Panel>

          <div className="split">
            <Panel title="Neutral template overrides" subtitle="Optional per-tenant neutral wording; never case content">
              <Field label="Tenant">
                <Select value={overrideTenantId} onChange={(e) => setOverrideTenantId(e.target.value)}>
                  <option value="">Select a tenant…</option>
                  {tenants.map((t) => <option key={t.id} value={t.id}>{t.display_name} ({t.slug})</option>)}
                </Select>
              </Field>
              <div className="split">
                <Field label="Template">
                  <Select value={overrideTemplate} onChange={(e) => setOverrideTemplate(e.target.value)}>
                    {TEMPLATE_CODES.map((c) => <option key={c} value={c}>{c}</option>)}
                  </Select>
                </Field>
                <Field label="Locale">
                  <Select value={overrideLocale} onChange={(e) => setOverrideLocale(e.target.value)}>
                    {LOCALES.map((l) => <option key={l} value={l}>{l}</option>)}
                  </Select>
                </Field>
              </div>
              <Field label="Subject">
                <Input value={overrideSubject} onChange={(e) => setOverrideSubject(e.target.value)} autoComplete="off" />
              </Field>
              <Field label="Body">
                <Textarea rows={4} value={overrideBody} onChange={(e) => setOverrideBody(e.target.value)} />
              </Field>
              <Button onClick={saveOverride} loading={saving}>Save override</Button>
              <p className="muted" style={{ marginTop: 10 }}>
                Overrides pass the same neutrality validator as the built-in templates: no variables, contact details or identifiers.
              </p>
            </Panel>

            <Panel title="Legal entity and units" subtitle="Registered entity and organisational units for the selected tenant">
              <div className="stack">
                {selectedTenantId && (
                  <>
                    <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
                      {legalEntities.map((le) => <Badge key={le.id} tone="neutral">{le.registered_name} · {le.country_code}</Badge>)}
                      {legalEntities.length === 0 && <span className="muted">No legal entities yet.</span>}
                    </div>
                    <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
                      {ou.map((u) => <Badge key={u.id} tone="info">{u.name}</Badge>)}
                      {ou.length === 0 && <span className="muted">No organisational units yet.</span>}
                    </div>
                    <LegalEntityQuickAdd tenantId={selectedTenantId} session={session} onAdded={() => selectTenant(selectedTenantId)} />
                    <OrganisationalUnitQuickAdd tenantId={selectedTenantId} session={session} onAdded={() => selectTenant(selectedTenantId)} />
                  </>
                )}
              </div>
            </Panel>
          </div>

          <Panel title="Template overrides for selected tenant" padded={false}>
            <DataTable
              keyField="id"
              empty={<EmptyState title="No overrides" description="Tenant uses the built-in neutral templates." />}
              columns={[
                { key: 'template_code', label: 'Template', render: (r) => <Badge tone="accent">{r.template_code}</Badge> },
                { key: 'locale', label: 'Locale', render: (r) => <Badge tone="neutral">{r.locale}</Badge> },
                { key: 'subject', label: 'Subject', render: (r) => r.subject },
                { key: 'body', label: 'Body preview', render: (r) => <span className="muted">{r.body.slice(0, 80)}{r.body.length > 80 ? '…' : ''}</span> },
              ]}
              rows={overrides}
            />
          </Panel>

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
        </>
      )}
    </main>
  );
}

function LegalEntityQuickAdd({
  tenantId,
  session,
  onAdded,
}: {
  tenantId: string;
  session: ReturnType<typeof useSession>['session'];
  onAdded: () => void;
}) {
  const { push } = useToast();
  const [name, setName] = useState('');
  const [country, setCountry] = useState('ZA');
  const [saving, setSaving] = useState(false);

  async function add() {
    if (!name.trim()) {
      push('Provide the registered name', 'warn');
      return;
    }
    setSaving(true);
    try {
      await createLegalEntity(tenantId, { registered_name: name.trim(), country_code: country }, session);
      push('Legal entity added', 'ok');
      setName('');
      onAdded();
    } catch (err) {
      push(err instanceof Error ? err.message : 'Could not add legal entity', 'danger');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="row" style={{ gap: 8 }}>
      <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Registered name" autoComplete="off" />
      <Select value={country} onChange={(e) => setCountry(e.target.value)} style={{ maxWidth: 90 }}>
        {['ZA', 'US', 'GB', 'KE', 'NG', 'DE', 'AE'].map((c) => <option key={c} value={c}>{c}</option>)}
      </Select>
      <Button variant="secondary" onClick={add} loading={saving}>Add entity</Button>
    </div>
  );
}

function OrganisationalUnitQuickAdd({
  tenantId,
  session,
  onAdded,
}: {
  tenantId: string;
  session: ReturnType<typeof useSession>['session'];
  onAdded: () => void;
}) {
  const { push } = useToast();
  const [name, setName] = useState('');
  const [saving, setSaving] = useState(false);

  async function add() {
    if (!name.trim()) {
      push('Provide the unit name', 'warn');
      return;
    }
    setSaving(true);
    try {
      await createOrganisationalUnit(tenantId, { name: name.trim(), unit_type: 'department' }, session);
      push('Organisational unit added', 'ok');
      setName('');
      onAdded();
    } catch (err) {
      push(err instanceof Error ? err.message : 'Could not add organisational unit', 'danger');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="row" style={{ gap: 8 }}>
      <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Unit name (e.g. Operations)" autoComplete="off" />
      <Button variant="secondary" onClick={add} loading={saving}>Add unit</Button>
    </div>
  );
}
