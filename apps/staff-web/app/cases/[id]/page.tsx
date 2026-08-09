'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  Alert, Badge, Button, DataTable, EmptyState, Field, Input, Kv, Modal, PageHeader, Panel, Select, StatusPill, Textarea,
} from '@safelytold/ui/components';
import { createRecord, getRecord, listRecords, listMailboxThread, policyDecide, replyMailboxMessage, type MailboxMessage, type PolicyOutput, type RecordView } from '@safelytold/ui/api';
import { useSession } from '@safelytold/ui/context';
import { useToast } from '@safelytold/ui/context';
import { formatDate } from '@safelytold/ui/hooks';
import { CASE_STATUS_LABELS, latestCaseRecords, TAXONOMY_LABELS } from '../../../lib/staff';

type ActionKey = 'acknowledge' | 'triage' | 'assign' | 'finding' | 'decision' | 'appeal' | 'close';

export default function CaseWorkbenchPage() {
  const params = useParams<{ id: string }>();
  const caseId = params.id;
  const { session } = useSession();
  const { push } = useToast();

  const [report, setReport] = useState<RecordView | null>(null);
  const [caseRecords, setCaseRecords] = useState<RecordView[]>([]);
  const [messages, setMessages] = useState<MailboxMessage[]>([]);
  const [protection, setProtection] = useState<RecordView[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [activeAction, setActiveAction] = useState<ActionKey | null>(null);
  const [status, setStatus] = useState('triage');
  const [note, setNote] = useState('');
  const [assigneeRole, setAssigneeRole] = useState('investigator');
  const [findingStatus, setFindingStatus] = useState('substantiated');
  const [decision, setDecision] = useState('remedy');
  const [appealDecision, setAppealDecision] = useState('uphold');
  const [busy, setBusy] = useState(false);
  const [policy, setPolicy] = useState<PolicyOutput | null>(null);
  const [policyLoading, setPolicyLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [reportRecord, caseList, mailboxList, protectionList] = await Promise.all([
        getRecord('intake', caseId, session).catch(() => null),
        listRecords('case', session, { caseId, limit: 1000 }),
        listMailboxThread(caseId, session).catch(() => []),
        listRecords('protection', session, { caseId, limit: 1000 }),
      ]);
      setReport(reportRecord);
      setCaseRecords(caseList ?? []);
      setMessages(mailboxList ?? []);
      setProtection(protectionList ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load the case');
    } finally {
      setLoading(false);
    }
  }, [caseId, session]);

  useEffect(() => {
    load();
  }, [load]);

  const current = useMemo(() => latestCaseRecords(caseRecords).find((r) => r.kind === 'case'), [caseRecords]);
  const caseStatus = current?.status ?? 'unverified';
  const payload = report?.payload as Record<string, unknown> | undefined;

  const findings = caseRecords.filter((r) => r.kind === 'finding');
  const decisions = caseRecords.filter((r) => r.kind === 'decision');
  const appeals = caseRecords.filter((r) => r.kind === 'appeal');
  const assignments = caseRecords.filter((r) => r.kind === 'assignment');
  const timeline = caseRecords.filter((r) => r.kind === 'timeline_event');

  async function runConflictCheck() {
    setPolicyLoading(true);
    setPolicy(null);
    try {
      const result = await policyDecide(
        {
          action: 'case:assign',
          resource_type: 'case',
          resource_id: caseId,
          subject_id: session.subject,
          roles: session.roles,
          purpose: session.purpose,
        },
        session,
      );
      setPolicy(result);
    } catch (err) {
      push(err instanceof Error ? err.message : 'Policy check failed', 'danger');
    } finally {
      setPolicyLoading(false);
    }
  }

  async function performAction() {
    if (!note.trim()) {
      push('Add a note for the audit record', 'warn');
      return;
    }
    setBusy(true);
    try {
      const base = { case_id: caseId, actor_role: session.roles[0], note: note.trim(), created_at: new Date().toISOString() };
      switch (activeAction) {
        case 'acknowledge':
          await createRecord('case', 'case', { ...base, kind: 'acknowledge', status: 'triage' }, session);
          await replyMailboxMessage(caseId, note.trim(), session);
          break;
        case 'triage':
          await createRecord('case', 'case', { ...base, kind: 'triage', status }, session);
          break;
        case 'assign':
          await createRecord('case', 'assignment', { ...base, assignee_role: assigneeRole, status: 'assigned' }, session);
          break;
        case 'finding':
          await createRecord('case', 'finding', { ...base, finding_status: findingStatus }, session);
          break;
        case 'decision':
          await createRecord('case', 'decision', { ...base, decision }, session);
          break;
        case 'appeal':
          await createRecord('case', 'appeal', { ...base, appeal_decision: appealDecision }, session);
          break;
        case 'close':
          await createRecord('case', 'case', { ...base, kind: 'close', status: 'closed' }, session);
          break;
      }
      setActiveAction(null);
      setNote('');
      push('Action recorded and appended to the audit trail', 'ok');
      await load();
    } catch (err) {
      push(err instanceof Error ? err.message : 'Action failed', 'danger');
    } finally {
      setBusy(false);
    }
  }

  const actionMeta: Record<ActionKey, { title: string; fields?: () => React.ReactNode }> = {
    acknowledge: { title: 'Acknowledge report' },
    triage: {
      title: 'Triage decision',
      fields: () => (
        <Field label="New status">
          <Select value={status} onChange={(e) => setStatus(e.target.value)}>
            {Object.entries(CASE_STATUS_LABELS).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </Select>
        </Field>
      ),
    },
    assign: {
      title: 'Assign handler',
      fields: () => (
        <Field label="Assignee role">
          <Select value={assigneeRole} onChange={(e) => setAssigneeRole(e.target.value)}>
            <option value="investigator">Investigator</option>
            <option value="case_manager">Case manager</option>
            <option value="legal_counsel">Legal counsel</option>
            <option value="ombuds">External ombuds</option>
          </Select>
        </Field>
      ),
    },
    finding: {
      title: 'Record finding',
      fields: () => (
        <Field label="Finding">
          <Select value={findingStatus} onChange={(e) => setFindingStatus(e.target.value)}>
            <option value="substantiated">Substantiated</option>
            <option value="unsubstantiated">Unsubstantiated</option>
            <option value="inconclusive">Inconclusive</option>
          </Select>
        </Field>
      ),
    },
    decision: {
      title: 'Record decision / remedy',
      fields: () => (
        <Field label="Decision type">
          <Select value={decision} onChange={(e) => setDecision(e.target.value)}>
            <option value="remedy">Remedy / corrective action</option>
            <option value="disciplinary">Disciplinary outcome</option>
            <option value="referral">Referral to independent route</option>
            <option value="no_action">No action</option>
          </Select>
        </Field>
      ),
    },
    appeal: {
      title: 'Appeal / review decision',
      fields: () => (
        <Field label="Outcome">
          <Select value={appealDecision} onChange={(e) => setAppealDecision(e.target.value)}>
            <option value="uphold">Uphold original decision</option>
            <option value="overturn">Overturn original decision</option>
            <option value="partial">Partially uphold</option>
            <option value="remand">Remand for further review</option>
          </Select>
        </Field>
      ),
    },
    close: { title: 'Close case' },
  };

  return (
    <main className="shell">
      <PageHeader
        eyebrow="Case workbench"
        title={`Case ${caseId.slice(0, 8)}…`}
        subtitle={`${payload?.mode as string ?? 'mode unknown'} report · ${TAXONOMY_LABELS[(payload?.taxonomy_codes as string[])?.[0] ?? ''] ?? 'unclassified'}`}
        actions={<Link href="/cases" className="btn btn-ghost btn-sm">← Queue</Link>}
      />

      {loading && <p className="muted">Loading case…</p>}
      {error && <Alert tone="danger" title="Load failed">{error}</Alert>}

      {report && (
        <>
          <div className="grid">
            <Panel title="Status">
              <StatusPill status={caseStatus} label={CASE_STATUS_LABELS[caseStatus] ?? caseStatus} />
              <Kv
                columns={1}
                items={[
                  { label: 'Case reference', value: <span className="mono">{caseId}</span> },
                  { label: 'Mode', value: payload?.mode as string },
                  { label: 'Jurisdiction', value: payload?.jurisdiction_code as string },
                  { label: 'Immediate risk', value: payload?.immediate_risk ? 'Yes — urgent' : 'No' },
                  { label: 'Received', value: formatDate(payload?.created_at as string) },
                  { label: 'Category', value: (payload?.taxonomy_codes as string[])?.join(', ') },
                ]}
              />
            </Panel>
            <Panel title="Narrative">
              <p style={{ whiteSpace: 'pre-wrap' }}>{payload?.narrative as string ?? '—'}</p>
              <Alert tone="warn" title="Reporter chose to share a readable copy">
                <p>Anonymous reports normally arrive with narrative sealed. This development environment stores a readable copy.</p>
              </Alert>
            </Panel>
          </div>

          <div className="split">
            <div className="stack">
              <Panel title="Actions" subtitle="Every action is recorded in the append-only audit chain.">
                <div className="row" style={{ flexWrap: 'wrap', gap: 8 }}>
                  {(['acknowledge', 'triage', 'assign', 'finding', 'decision', 'appeal', 'close'] as ActionKey[]).map((a) => (
                    <Button key={a} variant={a === 'close' ? 'danger' : 'secondary'} size="sm" onClick={() => setActiveAction(a)}>
                      {actionMeta[a].title}
                    </Button>
                  ))}
                </div>
                <Button variant="ghost" size="sm" onClick={runConflictCheck} loading={policyLoading} style={{ marginTop: 10 }}>
                  Run conflict / assignment policy check
                </Button>
                {policy && (
                  <Alert tone={policy.decision === 'allow' ? 'ok' : policy.decision === 'recuse' ? 'danger' : 'warn'} title={`Policy: ${policy.decision.replace(/_/g, ' ')}`}>
                    <ul>
                      {policy.reasons.map((r) => <li key={r}>{r}</li>)}
                    </ul>
                    {policy.obligations.length > 0 && <p className="muted">{policy.obligations.join(' · ')}</p>}
                  </Alert>
                )}
              </Panel>

              <Panel title="Timeline" padded={false}>
                {timeline.length === 0 ? (
                  <div className="panel-body"><EmptyState title="No timeline events" description="Use the actions above to record progress." /></div>
                ) : (
                  <ul className="plain-list">
                    {[...timeline].reverse().map((t) => (
                      <li key={t.id} className="row" style={{ justifyContent: 'space-between', gap: 12 }}>
                        <span className="muted">{(t.payload as Record<string, unknown>).note as string}</span>
                        <span className="muted">{formatDate((t.payload as Record<string, unknown>).created_at as string)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </Panel>
            </div>

            <div className="stack">
              <Panel title="Assignments & conflicts" padded={false}>
                {assignments.length === 0 ? (
                  <div className="panel-body"><p className="muted">No assignments recorded. Run a conflict check before assigning.</p></div>
                ) : (
                  <DataTable
                    keyField="id"
                    columns={[
                      { key: 'assignee_role', label: 'Role', render: (r) => <Badge tone="accent">{(r.payload as Record<string, unknown>).assignee_role as string}</Badge> },
                      { key: 'note', label: 'Note', render: (r) => <span className="muted">{(r.payload as Record<string, unknown>).note as string}</span> },
                      { key: 'created_at', label: 'When', render: (r) => <span className="muted">{formatDate((r.payload as Record<string, unknown>).created_at as string)}</span> },
                    ]}
                    rows={assignments}
                  />
                )}
              </Panel>

              <Panel title="Findings" padded={false}>
                {findings.length === 0 ? (
                  <div className="panel-body"><p className="muted">No findings yet. Findings are recorded per allegation with evidence links.</p></div>
                ) : (
                  findings.map((f) => (
                    <div key={f.id} className="panel-body" style={{ borderTop: '1px solid var(--line)' }}>
                      <StatusPill status={(f.payload as Record<string, unknown>).finding_status as string} />
                      <p className="muted" style={{ margin: '6px 0 0' }}>{(f.payload as Record<string, unknown>).note as string}</p>
                    </div>
                  ))
                )}
              </Panel>

              <Panel title="Mailbox preview" subtitle={`${messages.length} message${messages.length === 1 ? '' : 's'} exchanged`}>
                <div className="chat">
                  {messages.length === 0 ? (
                    <p className="muted">No messages yet. Use “Acknowledge report” to open the channel.</p>
                  ) : (
                    messages.map((m) => (
                      <div key={m.id} className={`bubble bubble-${m.sender === 'reporter' ? 'in' : 'out'}`}>
                        {m.body}
                        <span className="bubble-meta">{formatDate(m.created_at)}</span>
                      </div>
                    ))
                  )}
                </div>
                <Link href="/privacy" className="btn btn-ghost btn-sm">Protection & privacy room</Link>
              </Panel>
            </div>
          </div>
        </>
      )}

      <Modal
        open={activeAction !== null}
        onClose={() => setActiveAction(null)}
        title={activeAction ? actionMeta[activeAction].title : ''}
        footer={
          <div className="row">
            <Button onClick={performAction} loading={busy} variant={activeAction === 'close' ? 'danger' : 'primary'}>Save action</Button>
            <Button variant="ghost" onClick={() => setActiveAction(null)}>Cancel</Button>
          </div>
        }
      >
        <Alert tone="info" title="Audited action">
          <p>This action will be recorded with your role, purpose and a timestamp in the hash-chained audit log.</p>
        </Alert>
        {activeAction && actionMeta[activeAction].fields?.()}
        <Field label="Note / rationale" required>
          <Textarea rows={4} value={note} onChange={(e) => setNote(e.target.value)} placeholder="Why is this action being taken?" />
        </Field>
      </Modal>
    </main>
  );
}
