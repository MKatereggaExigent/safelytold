'use client';

import { useCallback, useState } from 'react';
import { Alert, Badge, Button, DataTable, EmptyState, Field, Input, PageHeader, Panel, Select, StatusPill, Textarea } from '@safelytold/ui/components';
import { createRecord, listRecords, type RecordView } from '@safelytold/ui/api';
import { useSession } from '@safelytold/ui/context';
import { useToast } from '@safelytold/ui/context';
import { formatDate, useMailboxConcerns, useRecords } from '@safelytold/ui/hooks';
import { latestCaseRecords, summarizeCase } from '../../lib/staff';

export default function ProtectionPage() {
  const { session } = useSession();
  const { push } = useToast();
  const { concerns, refresh: refreshConcerns } = useMailboxConcerns();
  const { records: plans, loading: plansLoading, refresh: refreshPlans } = useRecords('protection', 'protection_plan');
  const { records: invitations, refresh: refreshInvitations } = useRecords('support', 'support_invitation');
  const { records: caseRecords } = useRecords('case');

  const cases = latestCaseRecords(caseRecords).map(summarizeCase);
  const [caseId, setCaseId] = useState('');
  const [measures, setMeasures] = useState('');
  const [safeContact, setSafeContact] = useState('');
  const [reviewDays, setReviewDays] = useState('14');
  const [saving, setSaving] = useState(false);

  const refreshAll = useCallback(() => {
    refreshConcerns();
    refreshPlans();
    refreshInvitations();
  }, [refreshConcerns, refreshPlans, refreshInvitations]);

  async function createPlan() {
    if (!caseId || !measures.trim()) {
      push('Select a case and describe the protective measures', 'warn');
      return;
    }
    setSaving(true);
    try {
      const next = new Date(Date.now() + Number(reviewDays) * 86400000).toISOString();
      await createRecord('protection', 'protection_plan', {
        case_id: caseId,
        approved_measures: measures.trim(),
        safe_contact_method: safeContact.trim() || undefined,
        next_review_at: next,
        status: 'active',
        created_at: new Date().toISOString(),
      }, session);
      push('Protection plan created', 'ok');
      setMeasures('');
      setSafeContact('');
      refreshPlans();
    } catch (err) {
      push(err instanceof Error ? err.message : 'Could not create the plan', 'danger');
    } finally {
      setSaving(false);
    }
  }

  async function recordCheckIn(planId: string, caseRef: string) {
    try {
      await createRecord('protection', 'protection_checkin', {
        case_id: caseRef,
        plan_id: planId,
        status: 'completed',
        created_at: new Date().toISOString(),
      }, session);
      push('Check-in recorded', 'ok');
      refreshPlans();
    } catch (err) {
      push(err instanceof Error ? err.message : 'Could not record check-in', 'danger');
    }
  }

  return (
    <main className="shell">
      <PageHeader
        eyebrow="Anti-retaliation"
        title="Protection plans and follow-up"
        subtitle="Protection continues after case closure. Correlation is never treated as proof of retaliation."
      />

      {concerns.length > 0 && (
        <Alert tone="danger" title={`${concerns.length} retaliation concern${concerns.length === 1 ? '' : 's'} pending`}>
          <p>Independent escalation should review these promptly. Missed check-ins and alleged threats route outside the implicated hierarchy.</p>
        </Alert>
      )}

      <div className="split">
        <Panel title="New protection plan">
          <Field label="Case" required>
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
          <Field label="Approved measures" required>
            <Textarea rows={3} value={measures} onChange={(e) => setMeasures(e.target.value)} placeholder="Safe contact arrangements, reporting-line concerns, interim measures…" />
          </Field>
          <Field label="Safe contact method">
            <Input value={safeContact} onChange={(e) => setSafeContact(e.target.value)} autoComplete="off" />
          </Field>
          <Field label="Next review in (days)">
            <Select value={reviewDays} onChange={(e) => setReviewDays(e.target.value)}>
              {['7', '14', '30', '60'].map((d) => <option key={d} value={d}>{d} days</option>)}
            </Select>
          </Field>
          <Button onClick={createPlan} loading={saving} size="lg">Create protection plan</Button>
        </Panel>

        <Panel title="Active plans" subtitle={plansLoading ? 'Loading…' : undefined}>
          {plans.length === 0 ? (
            <EmptyState title="No protection plans" description="Plans you create appear here with review dates." />
          ) : (
            plans.map((p) => {
              const pl = p.payload as Record<string, string>;
              return (
                <div key={p.id} style={{ marginBottom: 14 }}>
                  <div className="row" style={{ justifyContent: 'space-between' }}>
                    <Badge tone="ok">Active</Badge>
                    <span className="muted">next review {formatDate(pl.next_review_at)}</span>
                  </div>
                  <p className="muted" style={{ margin: '6px 0' }}>{pl.approved_measures}</p>
                  <Button variant="secondary" size="sm" onClick={() => recordCheckIn(p.id, pl.case_id ?? '')}>Record check-in</Button>
                </div>
              );
            })
          )}
        </Panel>
      </div>

      <div className="split" style={{ marginTop: 20 }}>
        <Panel title="Retaliation concerns" padded={false}>
          <DataTable
            keyField="id"
            empty={<EmptyState title="No concerns" description="Concerns raised through the anonymous mailbox appear here." />}
            columns={[
              { key: 'case', label: 'Case', render: (r) => <span className="mono">{r.case_id ? r.case_id.slice(0, 8) : '—'}</span> },
              { key: 'concern', label: 'Concern', render: (r) => <span className="muted">{r.details}</span> },
              { key: 'risk_band', label: 'Risk', render: (r) => <Badge tone={r.risk_band === 'high' || r.risk_band === 'critical' ? 'danger' : 'warn'}>{r.risk_band}</Badge> },
              { key: 'status', label: 'Status', render: (r) => <StatusPill status={r.status} /> },
              { key: 'created_at', label: 'When', render: (r) => <span className="muted">{formatDate(r.created_at)}</span> },
            ]}
            rows={concerns}
          />
        </Panel>

        <Panel title="Support invitations" padded={false}>
          <DataTable
            keyField="id"
            empty={<EmptyState title="No invitations" description="Reporter-invited supporters appear here with their permissions." />}
            columns={[
              { key: 'identity', label: 'Identity', render: () => <Badge tone="neutral">Sealed</Badge> },
              { key: 'relationship', label: 'Relationship', render: (r) => <span className="muted">{(r.payload as Record<string, unknown>).relationship as string}</span> },
              { key: 'permissions', label: 'Permissions', render: (r) => <span className="muted">{((r.payload as Record<string, unknown>).permissions as string[])?.join(', ')}</span> },
              { key: 'status', label: 'Status', render: (r) => <StatusPill status={r.status} /> },
            ]}
            rows={invitations}
          />
        </Panel>
      </div>
    </main>
  );
}
