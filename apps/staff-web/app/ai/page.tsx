'use client';

import { useCallback, useEffect, useState } from 'react';
import { Alert, Badge, Button, DataTable, EmptyState, Field, PageHeader, Panel, Select, StatusPill, Textarea } from '@safelytold/ui/components';
import { getAiGovernance, listAiRuns, reviewAiRun, runAi, type AiCapability, type AiGovernance, type AiRunView } from '@safelytold/ui/api';
import { useSession } from '@safelytold/ui/context';
import { useToast } from '@safelytold/ui/context';
import { formatDate } from '@safelytold/ui/hooks';

const CAPABILITIES: { value: AiCapability; label: string; hint: string }[] = [
  { value: 'reporter_writing', label: 'Reporter writing', hint: 'Draft a clear, neutral account of events - no coaching, no judgment' },
  { value: 'triage_copilot', label: 'Triage copilot', hint: 'Suggest intake triage from redacted text' },
  { value: 'evidence_chronology', label: 'Evidence chronology', hint: 'Build a timeline from evidence refs' },
  { value: 'policy_retrieval', label: 'Policy retrieval', hint: 'Match policy clauses to a query' },
  { value: 'investigation_summary', label: 'Investigation summary', hint: 'Summarise an investigation for a decision-maker' },
  { value: 'pattern_analytics', label: 'Pattern analytics', hint: 'Aggregate, de-identified trend summary' },
  { value: 'sla_remediation', label: 'SLA remediation', hint: 'Draft a remediation note for a missed SLA' },
];

export default function AiPage() {
  const { session } = useSession();
  const { push } = useToast();
  const [governance, setGovernance] = useState<AiGovernance | null>(null);
  const [capability, setCapability] = useState<AiCapability>('triage_copilot');
  const [purpose, setPurpose] = useState('drafting redacted case notes');
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<AiRunView | null>(null);
  const [runs, setRuns] = useState<AiRunView[]>([]);
  const [runsLoading, setRunsLoading] = useState(true);
  const [reviewing, setReviewing] = useState<string | null>(null);
  const [version, setVersion] = useState(0);
  const refresh = useCallback(() => setVersion((v) => v + 1), []);

  useEffect(() => {
    getAiGovernance().then(setGovernance).catch(() => setGovernance(null));
  }, []);

  useEffect(() => {
    const active = { current: true };
    setRunsLoading(true);
    listAiRuns(session, { limit: 100 })
      .then((data) => {
        if (active.current) {
          setRuns(data.runs);
          setRunsLoading(false);
        }
      })
      .catch(() => {
        if (active.current) setRunsLoading(false);
      });
    return () => {
      active.current = false;
    };
  }, [session, version]);

  async function runCapability() {
    if (!input.trim()) {
      push('Provide redacted input for the capability', 'warn');
      return;
    }
    setBusy(true);
    setResult(null);
    try {
      const res = await runAi({ tenant_id: session.tenantId, capability, purpose, redacted_input: input }, session);
      setResult({ ...(res as unknown as AiRunView), id: res.run_id, tenant_id: session.tenantId });
      push('Run recorded - awaiting human review', 'info');
      refresh();
    } catch (err) {
      push(err instanceof Error ? err.message : 'Run failed', 'danger');
    } finally {
      setBusy(false);
    }
  }

  async function decide(id: string, approved: boolean) {
    setReviewing(id);
    try {
      const updated = await reviewAiRun(id, { approved, note: approved ? 'Approved by reviewer' : 'Rejected by reviewer' }, session);
      setResult(updated);
      push(`Draft ${approved ? 'approved' : 'rejected'}`, 'ok');
      refresh();
    } catch (err) {
      push(err instanceof Error ? err.message : 'Review failed', 'danger');
    } finally {
      setReviewing(null);
    }
  }

  return (
    <main className="shell">
      <PageHeader
        eyebrow="AI copilot"
        title="Advisory intelligence, human judgement"
        subtitle="Models draft, humans decide. AI never authorises, never sees raw evidence, and every run is recorded and reviewed."
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
              <option value="reporter narrative draft">Reporter narrative draft</option>
            </Select>
          </Field>
          <Field label="Redacted input" required hint="Strip names, roles and locations before submitting. The gateway stores only a hash.">
            <Textarea rows={6} value={input} onChange={(e) => setInput(e.target.value)} placeholder="Paste redacted text here…" />
          </Field>
          <Button onClick={runCapability} loading={busy} size="lg">Run capability</Button>
        </Panel>

        <div className="stack">
          {result && (
            <Panel title={`Output · ${String(result.capability)}`}>
              <Alert tone={result.status === 'awaiting_human_review' ? 'warn' : 'ok'} title={`${result.status.replace(/_/g, ' ')} · requires human approval`}>
                <p style={{ whiteSpace: 'pre-wrap' }}>{result.output}</p>
                <p className="muted" style={{ marginTop: 8 }}>
                  Uncertainty: {result.uncertainty} · Sources: {result.source_refs?.join(', ') ?? 'none'}
                </p>
              </Alert>
              {result.status === 'awaiting_human_review' && (
                <div className="row" style={{ gap: 8, marginTop: 12 }}>
                  <Button onClick={() => decide(result.id, true)} loading={reviewing === result.id} size="sm">Approve draft</Button>
                  <Button variant="danger" onClick={() => decide(result.id, false)} loading={reviewing === result.id} size="sm">Reject draft</Button>
                </div>
              )}
            </Panel>
          )}
          <Panel title="Governance">
            {governance ? (
              <div className="stack">
                <p className="muted"><strong>Provider:</strong> {governance.provider}</p>
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

      <Panel title="Run log" subtitle={runsLoading ? 'Loading…' : `${runs.length} recorded runs`} padded={false}>
        <DataTable
          keyField="id"
          loading={runsLoading}
          empty={<EmptyState title="No AI runs yet" description="Runs recorded by the AI gateway appear here, awaiting human review." />}
          columns={[
            { key: 'capability', label: 'Capability', render: (r) => <Badge tone="info">{(r as unknown as AiRunView).capability.replace(/_/g, ' ')}</Badge> },
            { key: 'purpose', label: 'Purpose', render: (r) => <span className="muted">{(r as unknown as AiRunView).purpose}</span> },
            { key: 'status', label: 'Status', render: (r) => <StatusPill status={(r as unknown as AiRunView).status} /> },
            { key: 'requested_by', label: 'Requested by', render: (r) => <span className="muted">{(r as unknown as AiRunView).requested_by ?? 'anonymous'}</span> },
            { key: 'requested_at', label: 'Run at', render: (r) => <span className="muted">{formatDate((r as unknown as AiRunView).requested_at)}</span> },
            {
              key: 'actions',
              label: 'Review',
              render: (r) => {
                const run = r as unknown as AiRunView;
                if (run.status !== 'awaiting_human_review') return <span className="muted">{run.decision_note ?? run.status}</span>;
                return (
                  <div className="row" style={{ gap: 8 }}>
                    <Button variant="ghost" size="sm" onClick={() => decide(run.id, true)}>Approve</Button>
                    <Button variant="ghost" size="sm" onClick={() => decide(run.id, false)}>Reject</Button>
                  </div>
                );
              },
            },
          ]}
          rows={runs as unknown as Array<Record<string, unknown>>}
        />
      </Panel>
    </main>
  );
}
