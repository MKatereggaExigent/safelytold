'use client';

import { useState } from 'react';
import { Alert, Badge, Button, Field, Input, PageHeader, Panel, Select } from '@safelytold/ui/components';
import { useSession } from '@safelytold/ui/context';
import { useToast } from '@safelytold/ui/context';
import { PURPOSES, STAFF_ROLES, staffSession } from '../lib/staff';

export default function SessionPage() {
  const { session, setSession } = useSession();
  const { push } = useToast();
  const [role, setRole] = useState<string>(session.roles[0] ?? 'triage_officer');
  const [purpose, setPurpose] = useState<string>(session.purpose ?? 'triage');
  const [displayName, setDisplayName] = useState<string>(session.displayName ?? 'O. Nel');
  const [busy, setBusy] = useState(false);

  function enterWorkspace() {
    setBusy(true);
    setSession(staffSession(role, purpose, displayName));
    push(`Signed in as ${STAFF_ROLES.find((r) => r.value === role)?.label}`, 'ok');
    window.location.href = '/staff/dashboard';
  }

  return (
    <main className="shell">
      <PageHeader
        eyebrow="Integrity workspace"
        title="Choose how you work today"
        subtitle="Roles and purposes drive the policy engine: you only ever see what your assigned role and declared purpose authorise."
      />

      <Alert tone="info" title="Development sign-in">
        <p>
          This portal uses the development authentication bypass. In production, staff sign in with corporate SSO (OIDC /
          SAML + MFA) and never choose their own role.
        </p>
      </Alert>

      <div className="split">
        <Panel title="Session">
          <Field label="Working role" required>
            <Select value={role} onChange={(e) => setRole(e.target.value)}>
              {STAFF_ROLES.map((r) => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </Select>
          </Field>
          <Field label="Purpose of access" required hint="Purpose binding means an investigator cannot open a case ‘to browse’.">
            <Select value={purpose} onChange={(e) => setPurpose(e.target.value)}>
              {PURPOSES.map((p) => (
                <option key={p} value={p}>{p.replace(/-/g, ' ')}</option>
              ))}
            </Select>
          </Field>
          <Field label="Display name" required>
            <Input value={displayName} onChange={(e) => setDisplayName(e.target.value)} autoComplete="off" />
          </Field>
          <Button onClick={enterWorkspace} loading={busy} size="lg">Enter workspace</Button>
        </Panel>

        <div className="stack">
          <Panel title="Role expectations">
            {STAFF_ROLES.map((r) => (
              <div key={r.value} className="row" style={{ justifyContent: 'space-between', marginBottom: 8 }}>
                <span>{r.label}</span>
                <Badge tone={r.value === role ? 'accent' : 'neutral'}>
                  {r.value === role ? 'Selected' : r.value.replace(/_/g, ' ')}
                </Badge>
              </div>
            ))}
          </Panel>
          <Panel title="Guardrails">
            <p className="muted">
              No role receives default access to case content. Every decision, conflict check and export is recorded in
              the append-only audit chain.
            </p>
          </Panel>
        </div>
      </div>
    </main>
  );
}
