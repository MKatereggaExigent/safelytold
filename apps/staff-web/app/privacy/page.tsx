'use client';

import { useCallback, useMemo, useState } from 'react';
import { Alert, Badge, Button, DataTable, EmptyState, Field, Input, PageHeader, Panel, Select, StatusPill, Textarea } from '@safelytold/ui/components';
import {
  createVaultAccessRequest, decideVaultAccessRequest, revealVaultIdentity, verifyAuditChain,
  type RecordView,
} from '@safelytold/ui/api';
import { useSession } from '@safelytold/ui/context';
import { useToast } from '@safelytold/ui/context';
import { formatDate, useRecords } from '@safelytold/ui/hooks';
import { latestCaseRecords, summarizeCase } from '../../lib/staff';

type RequestState = Record<string, { status: string; purpose: string; requested_at?: string }>;

export default function PrivacyPage() {
  const { session } = useSession();
  const { push } = useToast();
  const { records: caseRecords } = useRecords('case');
  const { records: auditRecords } = useRecords('audit');

  const cases = latestCaseRecords(caseRecords).map(summarizeCase);
  const [caseId, setCaseId] = useState('');
  const [purpose, setPurpose] = useState('investigation-necessity');
  const [requests, setRequests] = useState<RequestState>({});
  const [revealed, setRevealed] = useState<Record<string, Record<string, unknown>>>({});
  const [busy, setBusy] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState<string | null>(null);

  const requestCaseIds = useMemo(() => new Set(cases.map((c) => c.id)), [cases]);

  async function requestAccess() {
    if (!caseId) {
      push('Select a case with a vaulted identity', 'warn');
      return;
    }
    setBusy(true);
    try {
      const result = await createVaultAccessRequest(caseId, purpose, session);
      setRequests((prev) => ({ ...prev, [caseId]: { status: result.status, purpose: result.purpose } }));
      push(`Access request created — ${result.required_approvals} approval${result.required_approvals === 1 ? '' : 's'} required`, 'ok');
    } catch (err) {
      push(err instanceof Error ? err.message : 'Could not create access request', 'danger');
    } finally {
      setBusy(false);
    }
  }

  const decide = useCallback(async (id: string, decision: 'approve' | 'deny') => {
    try {
      const result = await decideVaultAccessRequest(id, decision, 'Dual-control test', session);
      setRequests((prev) => ({ ...prev, [id]: { status: result.status, purpose: prev[id]?.purpose ?? '' } }));
      push(`Request ${result.decision} — ${result.status}`, 'ok');
    } catch (err) {
      push(err instanceof Error ? err.message : 'Decision failed', 'danger');
    }
  }, [session, push]);

  async function reveal(id: string) {
    try {
      const result = await revealVaultIdentity(id, session);
      setRevealed((prev) => ({ ...prev, [id]: result.identity }));
      push('Identity revealed under declared purpose and logged', 'ok');
    } catch (err) {
      push(err instanceof Error ? err.message : 'Reveal failed', 'danger');
    }
  }

  async function verifyChain() {
    setVerifying(true);
    try {
      const result = await verifyAuditChain(session.tenantId, session);
      setVerifyResult(result.valid
        ? `Audit chain valid — ${result.entries} entries, head ${result.head?.slice(0, 16)}…`
        : `Audit chain INVALID at sequence ${result.failed_sequence}`);
    } catch (err) {
      setVerifyResult(err instanceof Error ? err.message : 'Verification failed');
    } finally {
      setVerifying(false);
    }
  }

  const requestItems: { id: string; case_id: string; payload: Record<string, unknown> }[] = useMemo(() => {
    const items: { id: string; case_id: string; payload: Record<string, unknown> }[] = [];
    for (const [cid, r] of Object.entries(requests)) {
      items.push({ id: cid, case_id: cid, payload: { purpose: r.purpose, status: r.status } });
    }
    return items;
  }, [requests]);

  return (
    <main className="shell">
      <PageHeader
        eyebrow="Privacy control room"
        title="Reporter identity vault"
        subtitle="Identity is sealed in a separate realm. Opening it requires a declared purpose, dual approval and an audited log entry."
      />

      <Alert tone="warn" title="Highest-sensitivity control">
        <p>
          No role can open the vault by default. Break-glass requires a reason, time limit, approval and automatic
          revocation — and is never used to identify an anonymous reporter for convenience.
        </p>
      </Alert>

      <div className="split">
        <Panel title="Request identity access">
          <Field label="Case" required hint="Only cases created in the confidential or identified modes may hold a vault identity.">
            {cases.length === 0 ? (
              <Input value={caseId} onChange={(e) => setCaseId(e.target.value)} placeholder="Enter case reference" className="mono" />
            ) : (
              <Select value={caseId} onChange={(e) => setCaseId(e.target.value)} placeholder="Select a case…">
                {cases.map((c) => (
                  <option key={c.id} value={c.id}>{c.id.slice(0, 8)} · {c.status}</option>
                ))}
              </Select>
            )}
          </Field>
          <Field label="Declared purpose" required>
            <Select value={purpose} onChange={(e) => setPurpose(e.target.value)}>
              <option value="investigation-necessity">Investigation necessity</option>
              <option value="protection-contact">Protection / safe contact</option>
              <option value="legal-requirement">Legal requirement</option>
              <option value="reporter-consent">Reporter consent</option>
            </Select>
          </Field>
          <Button onClick={requestAccess} loading={busy} size="lg">Create access request</Button>
        </Panel>

        <Panel title="Audit integrity">
          <p className="muted">
            Every access decision, conflict check and export is recorded in an append-only, tamper-evident hash chain.
            You can ask the audit service to verify the whole chain for this tenant.
          </p>
          <Button variant="secondary" onClick={verifyChain} loading={verifying}>Verify audit chain</Button>
          {verifyResult && (
            <Alert tone={verifyResult.startsWith('Audit chain valid') ? 'ok' : 'danger'} title="Verification">
              {verifyResult}
            </Alert>
          )}
        </Panel>
      </div>

      <div className="stack" style={{ marginTop: 20 }}>
        <Panel title="Access requests" subtitle="Pending requests await the required number of independent approvals." padded={false}>
          <DataTable
            keyField="id"
            empty={<EmptyState title="No access requests" description="Requests created in this session appear here." />}
            columns={[
              { key: 'case', label: 'Case', render: (r) => <span className="mono">{(r as { case_id: string }).case_id.slice(0, 8)}</span> },
              { key: 'purpose', label: 'Purpose', render: (r) => <Badge tone="info">{(r as { payload: Record<string, unknown> }).payload.purpose as string}</Badge> },
              { key: 'status', label: 'Status', render: (r) => <StatusPill status={(r as { payload: Record<string, unknown> }).payload.status as string} /> },
              {
                key: 'actions',
                label: 'Actions',
                render: (r) => {
                  const id = (r as { case_id: string }).case_id;
                  const req = requests[id];
                  return (
                    <div className="row" style={{ gap: 6 }}>
                      {(!req || req.status === 'pending') && (
                        <>
                          <Button variant="secondary" size="sm" onClick={() => decide(id, 'approve')}>Approve</Button>
                          <Button variant="ghost" size="sm" onClick={() => decide(id, 'deny')}>Deny</Button>
                        </>
                      )}
                      {req?.status === 'approved' && (
                        <Button variant="danger" size="sm" onClick={() => reveal(id)}>Reveal identity</Button>
                      )}
                    </div>
                  );
                },
              },
            ]}
            rows={requestItems}
          />
        </Panel>

        {Object.keys(revealed).length > 0 && (
          <Panel title="Revealed identities" subtitle="Shown only because approval was granted; this display is for the development demo.">
            {Object.entries(revealed).map(([id, identity]) => (
              <Alert key={id} tone="danger" title={`Revealed for ${id.slice(0, 8)}`}>
                <p className="mono" style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(identity, null, 2)}</p>
              </Alert>
            ))}
          </Panel>
        )}

        <Panel title="Recent audit entries" subtitle={`${auditRecords.length} records in this tenant’s audit service`} padded={false}>
          <DataTable
            keyField="id"
            empty={<EmptyState title="No audit entries" description="Audit events generated by the services appear here." />}
            columns={[
              { key: 'event', label: 'Event', render: (r) => <Badge tone="neutral">{(r as RecordView).kind.replace(/_/g, ' ')}</Badge> },
              { key: 'subject', label: 'Subject', render: (r) => <span className="mono">{(r as RecordView).payload.subject_ref as string ?? '—'}</span> },
              { key: 'status', label: 'Status', render: (r) => <StatusPill status={(r as RecordView).status} /> },
            ]}
            rows={auditRecords}
          />
        </Panel>
      </div>
    </main>
  );
}
