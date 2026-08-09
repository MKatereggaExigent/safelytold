'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { Badge, DataTable, EmptyState, PageHeader, Panel, Pagination, Segmented, StatusPill } from '@safelytold/ui/components';
import { formatDate, usePagination, useRecords } from '@safelytold/ui/hooks';
import { CASE_STATUS_LABELS, latestCaseRecords, summarizeCase } from '../../lib/staff';

type Filter = 'all' | 'triage' | 'active' | 'closed';

export default function CasesPage() {
  const { records, loading, error, refresh } = useRecords('case');
  const [filter, setFilter] = useState<Filter>('all');

  const summaries = useMemo(() => latestCaseRecords(records).map(summarizeCase), [records]);

  const filtered = useMemo(() => {
    if (filter === 'all') return summaries;
    if (filter === 'triage') return summaries.filter((c) => ['unverified', 'triage'].includes(c.status));
    if (filter === 'active') return summaries.filter((c) => !['closed', 'resolved'].includes(c.status));
    return summaries.filter((c) => ['closed', 'resolved'].includes(c.status));
  }, [summaries, filter]);
  const { pageItems: paged, ...pagination } = usePagination(filtered);

  return (
    <main className="shell">
      <PageHeader
        eyebrow="Case management"
        title="Case queue"
        subtitle="Reports enter here from the public portal. Every row is a case with its own status, mode and risk flags."
        actions={<button type="button" className="btn btn-secondary btn-md" onClick={refresh}>Refresh</button>}
      />

      <Panel padded={false}>
        <div className="panel-toolbar">
          <Segmented<Filter>
            ariaLabel="Filter cases"
            value={filter}
            onChange={setFilter}
            options={[
              { value: 'all', label: `All (${summaries.length})` },
              { value: 'triage', label: `Triage (${summaries.filter((c) => ['unverified', 'triage'].includes(c.status)).length})` },
              { value: 'active', label: 'Active' },
              { value: 'closed', label: 'Closed' },
            ]}
          />
        </div>
        <DataTable
          keyField="id"
          loading={loading}
          empty={
            error ? (
              <EmptyState title="Could not load cases" description={error} />
            ) : (
              <EmptyState title="No cases yet" description="When reporters submit concerns, cases appear here for triage." />
            )
          }
          columns={[
            {
              key: 'id',
              label: 'Case',
              render: (r) => (
                <Link href={`/cases/${r.id}`} className="mono" style={{ fontSize: '0.85rem' }}>
                  {r.id.slice(0, 12)}…
                </Link>
              ),
            },
            { key: 'mode', label: 'Mode', render: (r) => <Badge tone="neutral">{r.mode}</Badge> },
            {
              key: 'taxonomy',
              label: 'Category',
              render: (r) => (
                <span className="muted">{r.taxonomy_codes?.[0]?.replace(/_/g, ' ') ?? 'unclassified'}</span>
              ),
            },
            { key: 'status', label: 'Status', render: (r) => <StatusPill status={r.status} label={CASE_STATUS_LABELS[r.status] ?? r.status} /> },
            { key: 'created_at', label: 'Received', render: (r) => <span className="muted">{formatDate(r.created_at)}</span> },
            {
              key: 'risk',
              label: 'Risk',
              render: (r) => (r.immediate_risk ? <Badge tone="danger">immediate</Badge> : <span className="muted">—</span>),
            },
          ]}
          rows={paged}
        />
        <div className="pagination-wrap">
          <Pagination key={filter} {...pagination} />
        </div>
      </Panel>
    </main>
  );
}
