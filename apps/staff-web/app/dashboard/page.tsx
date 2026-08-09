'use client';

import { useMemo } from 'react';
import Link from 'next/link';
import { Alert, Badge, PageHeader, Panel, Stat, StatusPill } from '@safelytold/ui/components';
import { useRecords, useGatewayHealth, useMailboxConcerns } from '@safelytold/ui/hooks';
import { formatDate } from '@safelytold/ui/hooks';
import { CASE_STATUS_LABELS, latestCaseRecords, summarizeCase } from '../../lib/staff';

export default function DashboardPage() {
  const { records: reports, loading: reportsLoading } = useRecords('intake', 'report');
  const { records: cases, loading: casesLoading } = useRecords('case');
  const { concerns } = useMailboxConcerns();
  const { records: evidence } = useRecords('evidence');
  const { health } = useGatewayHealth();

  const summaries = useMemo(() => latestCaseRecords(cases).map(summarizeCase), [cases]);

  const open = summaries.filter((c) => !['closed', 'resolved'].includes(c.status)).length;
  const inTriage = summaries.filter((c) => ['unverified', 'triage'].includes(c.status)).length;
  const atRisk = reports.filter((r) => Boolean((r.payload as Record<string, unknown>).immediate_risk)).length;
  const totalServices = health ? Object.keys(health).length : 0;
  const healthy = health ? Object.values(health).filter((h) => h.status === 'ok' || h.status === 'healthy').length : 0;

  const recent = [...summaries].sort((a, b) => (b.created_at ?? '').localeCompare(a.created_at ?? '')).slice(0, 6);

  return (
    <main className="shell">
      <PageHeader
        eyebrow="Dashboard"
        title="Case queue at a glance"
        subtitle="Purpose-bound and audited — access is limited to what your role and declared purpose authorise."
      />

      <div className="grid">
        <Stat label="Open cases" value={open} hint="Across all statuses" tone="accent" />
        <Stat label="Awaiting triage" value={inTriage} hint="Unverified / triage" tone="warn" />
        <Stat label="Immediate-risk reports" value={atRisk} hint="Flagged at intake" tone="danger" />
        <Stat label="Retaliation concerns" value={concerns.length} hint="Protection follow-up" tone="violet" />
      </div>

      {healthy < totalServices && (
        <Alert tone="danger" title="Some services are unreachable">
          <p>
            Gateway reports {healthy}/{totalServices} services healthy. Evidence, AI and ledger actions may fail until they recover.
          </p>
        </Alert>
      )}

      <div className="split">
        <Panel title="Recent cases" subtitle={casesLoading ? 'Loading…' : 'Newest first'} padded={false}>
          {recent.length === 0 ? (
            <div className="panel-body">
              <p className="muted">No cases yet. New reports from the public portal appear here for triage.</p>
            </div>
          ) : (
            <ul className="plain-list">
              {recent.map((c) => (
                <li key={c.id}>
                  <Link href={`/cases/${c.id}`} className="row" style={{ justifyContent: 'space-between', gap: 12 }}>
                    <span>
                      <span className="mono" style={{ fontSize: '0.82rem' }}>{c.id.slice(0, 8)}</span>
                      <span className="muted"> · {CASE_STATUS_LABELS[c.status] ?? c.status}</span>
                    </span>
                    <span className="row" style={{ gap: 8 }}>
                      {c.immediate_risk && <Badge tone="danger">risk</Badge>}
                      <StatusPill status={c.status} />
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <div className="stack">
          <Panel title="Response commitments">
            <p className="muted">
              Acknowledge every report within the tenant SLA, keep the reporter updated, and never let a conflict steer
              the case.
            </p>
            <div className="row">
              <Link href="/cases" className="btn btn-primary btn-md">Open case queue</Link>
              <Link href="/ai" className="btn btn-secondary btn-md">AI copilot</Link>
            </div>
          </Panel>
          <Panel title="Gateway health" subtitle={health ? `${healthy}/${totalServices} services reporting` : 'Gateway unreachable'}>
            {health && (
              <div className="row" style={{ flexWrap: 'wrap', gap: 8 }}>
                {Object.entries(health).map(([name, h]) => (
                  <Badge key={name} tone={h.status === 'ok' || h.status === 'healthy' ? 'ok' : 'danger'}>
                    {name}
                  </Badge>
                ))}
              </div>
            )}
          </Panel>
        </div>
      </div>
    </main>
  );
}
