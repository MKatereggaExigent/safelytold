'use client';

import { useEffect, useState } from 'react';
import { Alert, Badge, Button, DataTable, EmptyState, Field, PageHeader, Panel, Select, StatusPill, Textarea } from '@safelytold/ui/components';
import { getAiGovernance, runAi, type AiCapability, type AiGovernance, type RecordView } from '@safelytold/ui/api';
import { useSession } from '@safelytold/ui/context';
import { useToast } from '@safelytold/ui/context';
import { formatDate, useRecords } from '@safelytold/ui/hooks';

const CAPABILITIES: { value: AiCapability; label: string; hint: string }[] = [
  { value: 'triage_copilot', label: 'Triage copilot', hint: 'Suggest intake triage from redacted text' },
  { value: 'evidence_chronology', label: 'Evidence chronology', hint: 'Build a timeline from evidence refs' },
  { value: 'policy_retrieval', label: 'Policy retrieval', hint: 'Match policy clauses to a query' },
  { value: 'investigation_summary', label: 'Investigation summary', hint: 'Summarise an investigation for a decision-maker' },
  { value: 'pattern_analytics', label: 'Pattern analytics', hint: 'Aggregate, de-identified trend summary' },
  { value: 'sla_remediation', label: 'SLA remediation', hint: 'Draft a remediation note for a missed SLA' },
  { value: 'translation', label: 'Translation', hint: 'Translate between supported languages' },
];

export default function AiPage() {
  const { session } = useSession();
  const { push } = useToast();
  const { records: runs, loading, refresh } = useRecords('ai');
  const [governance, setGovernance] = useState<AiGovernance | null>(null);
  const [capability, setCapability] = useState<AiCapability>('triage_copilot');
  const [purpose, setPurpose] = useState('drafting redacted case notes');
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    getAiGovernance().then(setGovernance).catch(() => setGovernance(null));
  }, []);

  async function runCapability() {
    if (!input.trim()) {
      push('Provide redacted input for the capability', 'warn');
      return;
    }
    setBusy(true);
    setResult(null);
    try {
      const res = await runAi({ tenant_id: session.tenantId, capability, purpose, redacted_input: input }, session);
      setResult(res as unknown as Record<string, unknown>);
      push(`Run ${res.status} — ${res.requires_human_approval ? 'human approval required' : 'advisory output'}`, res.status === 'completed' ? 'ok' : 'info');
      refresh();
    } catch (err) {
      push(err instanceof Error ? err.message : 'Run failed', 'danger');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell">
      <PageHeader
        eyebrow="AI copilot"
        title="Advisory intelligence, human judgement"
        subtitle="Models draft, humans decide. AI never authorises, never sees raw evidence without a purpose, and every run is recorded."
      />

      <div className="split">
        <Panel title="Run a capability">
          <Field label="Capability" required>
            <Select value={capability} onChange={(e) => setCapability(e.target.value as AiCapability)}>
              {CAPABILITIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
            </Select>
          </Field>
          {CAPABILITIES.find((c) => c.value === capability)?.hint && (
            <p className="muted">{CAPABILITIES.find((c) => c.value === capability)?.hint}</p>
          )}
          <Field label="Purpose" required hint="A stated purpose is written into the run record.">
            <Select value={purpose} onChange={(e) => setPurpose(e.target.value)}>
              <option value="drafting redacted case notes">Drafting redacted case notes</option>
              <option value="chronology from evidence refs">Chronology from evidence refs</option>
              <option value="aggregate de-identified trends">Aggregate de-identified trends</option>
              <option value="translation for a reporter">Translation for a reporter</option>
            </Select>
          </Field>
          <Field label="Redacted input" required hint="Strip names, roles and locations before submitting.">
            <Textarea rows={6} value={input} onChange={(e) => setInput(e.target.value)} placeholder="Paste redacted text here…" />
          </Field>
          <Button onClick={runCapability} loading={busy} size="lg">Run capability</Button>
        </Panel>

        <div className="stack">
          {result && (
            <Panel title={`Output · ${String(result.capability)}`}>
              <Alert tone="ok" title={`${String(result.status)}${result.requires_human_approval ? ' · requires human approval' : ' · advisory'}`}>
                <p style={{ whiteSpace: 'pre-wrap' }}>{String(result.output)}</p>
                <p className="muted" style={{ marginTop: 8 }}>
                  Uncertainty: {String(result.uncertainty)} · Sources: {(result.source_refs as string[] | undefined)?.join(', ') ?? 'none'}
                </p>
              </Alert>
            </Panel>
          )}
          <Panel title="Governance">
            {governance ? (
              <div className="stack">
                <p className="muted"><strong>Raw evidence allowed:</strong> {String(governance.raw_evidence_allowed)}</p>
                <p className="muted"><strong>Human approval default:</strong> {String(governance.human_approval_default)}</p>
                <p className="muted"><strong>Prohibited purposes:</strong></p>
                <ul>
                  {governance.prohibited_purposes.map((p) => <li key={p} className="muted">{p}</li>)}
                </ul>
              </div>
            ) : (
              <p className="muted">Loading governance settings…</p>
            )}
          </Panel>
        </div>
      </div>

      <Panel title="Run log" subtitle={loading ? 'Loading…' : `${runs.length} recorded runs`} padded={false}>
        <DataTable
          keyField="id"
          loading={loading}
          empty={<EmptyState title="No AI runs yet" description="Runs recorded by the AI service appear here." />}
          columns={[
            { key: 'capability', label: 'Capability', render: (r) => <Badge tone="info">{(r as RecordView).kind.replace(/_/g, ' ')}</Badge> },
            { key: 'purpose', label: 'Purpose', render: (r) => <span className="muted">{(r as RecordView).payload.purpose as string}</span> },
            { key: 'status', label: 'Status', render: (r) => <StatusPill status={(r as RecordView).payload.status as string} /> },
            { key: 'created', label: 'Run at', render: (r) => <span className="muted">{formatDate((r as RecordView).payload.created_at as string | undefined)}</span> },
          ]}
          rows={runs}
        />
      </Panel>
    </main>
  );
}
