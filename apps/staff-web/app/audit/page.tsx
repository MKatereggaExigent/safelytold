'use client';

import { useEffect, useState } from 'react';
import { Alert, Badge, Button, DataTable, EmptyState, Field, Input, PageHeader, Panel, Select, StatusPill } from '@safelytold/ui/components';
import { appendAuditEntry, listAuditEntries, verifyAuditChain } from '@safelytold/ui/api';
import { useSession } from '@safelytold/ui/context';
import { useToast } from '@safelytold/ui/context';
import { formatDate } from '@safelytold/ui/hooks';

const EVENT_TYPES = [
  'case.opened',
  'case.viewed',
  'case.exported',
  'identity.vault_accessed',
  'access_request.approved',
  'access_request.denied',
  'evidence.uploaded',
  'evidence.legal_hold',
  'policy.decided',
  'ai.run',
];

export default function AuditPage() {
  const { session } = useSession();
  const { push } = useToast();
  const [records,setRecords]=useState<any[]>([]); const [loading,setLoading]=useState(true);
  async function refresh(){setLoading(true);try{setRecords(await listAuditEntries(session))}finally{setLoading(false)}}
  useEffect(()=>{void refresh()},[session.accessToken,session.tenantId]);

  const [eventType, setEventType] = useState<string>(EVENT_TYPES[0] ?? 'case.opened');
  const [subjectRef, setSubjectRef] = useState('');
  const [purpose, setPurpose] = useState('operational oversight');
  const [busy, setBusy] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState<string | null>(null);

  async function recordEvent() {
    if (!subjectRef.trim()) {
      push('Provide a subject reference', 'warn');
      return;
    }
    setBusy(true);
    try {
      const entry = await appendAuditEntry({
        event_type: eventType,
        subject_ref: subjectRef.trim(),
        purpose,
        metadata: { source: 'staff-web' },
      }, session);
      push(`Audit entry #${entry.sequence} recorded`, 'ok');
      setSubjectRef('');
      refresh();
    } catch (err) {
      push(err instanceof Error ? err.message : 'Could not record audit entry', 'danger');
    } finally {
      setBusy(false);
    }
  }

  async function verify() {
    setVerifying(true);
    setVerifyResult(null);
    try {
      const result = await verifyAuditChain(session.tenantId, session);
      setVerifyResult(result.valid
        ? `Chain valid — ${result.entries} entries, head ${result.head?.slice(0, 16)}…`
        : `Chain INVALID at sequence ${result.failed_sequence}`);
    } catch (err) {
      setVerifyResult(err instanceof Error ? err.message : 'Verification failed');
    } finally {
      setVerifying(false);
    }
  }

  return (
    <main className="shell">
      <PageHeader
        eyebrow="Audit trail"
        title="Append-only, tamper-evident"
        subtitle="Every significant action is recorded by the services as a signed hash-chained entry that no staff role can edit."
      />

      <div className="split">
        <Panel title="Record an audit entry">
          <Field label="Event type">
            <Select value={eventType} onChange={(e) => setEventType(e.target.value)}>
              {EVENT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </Select>
          </Field>
          <Field label="Subject reference" required hint="Case ref, identity ref, evidence id or policy decision.">
            <Input value={subjectRef} onChange={(e) => setSubjectRef(e.target.value)} placeholder="case/abc123…" className="mono" autoComplete="off" />
          </Field>
          <Field label="Purpose">
            <Select value={purpose} onChange={(e) => setPurpose(e.target.value)}>
              <option value="operational oversight">Operational oversight</option>
              <option value="regulatory response">Regulatory response</option>
              <option value="security incident">Security incident</option>
              <option value="user initiated export">User initiated export</option>
            </Select>
          </Field>
          <Button onClick={recordEvent} loading={busy}>Record entry</Button>
        </Panel>

        <Panel title="Verify the chain">
          <p className="muted">
            The audit service re-derives the hash chain from the first entry and compares each link. Any missing or
            altered entry is reported by sequence number.
          </p>
          <Button variant="secondary" onClick={verify} loading={verifying}>Verify full chain</Button>
          {verifyResult && (
            <Alert tone={verifyResult.startsWith('Chain valid') ? 'ok' : 'danger'} title="Verification">
              {verifyResult}
            </Alert>
          )}
        </Panel>
      </div>

      <Panel title="Audit entries" subtitle={loading ? 'Loading…' : `${records.length} entries in this tenant’s audit service`} padded={false}>
        <DataTable
          keyField="id"
          loading={loading}
          empty={<EmptyState title="No audit entries" description="Events recorded by services appear here." />}
          columns={[
            { key: 'event', label: 'Event', render: (r) => <Badge tone="info">{r.event_type}</Badge> },
            { key: 'subject', label: 'Subject', render: (r) => <span className="mono">{r.subject_ref}</span> },
            { key: 'purpose', label: 'Purpose', render: (r) => <span className="muted">{r.purpose}</span> },
            { key: 'status', label: 'Sequence', render: (r) => <StatusPill status={`#${r.sequence}`} /> },
            { key: 'created', label: 'Recorded', render: (r) => <span className="muted">{formatDate(r.created_at)}</span> },
          ]}
          rows={records}
        />
      </Panel>
    </main>
  );
}
