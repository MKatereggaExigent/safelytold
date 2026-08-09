'use client';

import { useMemo } from 'react';
import { Alert, Badge, Panel, Stat } from '@safelytold/ui/components';
import { listRecords, type RecordView } from '@safelytold/ui/api';
import { useEffect, useState } from 'react';

const MIN_COHORT = 5;

const TAXONOMY_LABELS: Record<string, string> = {
  discrimination: 'Discrimination',
  harassment: 'Harassment',
  bullying: 'Bullying',
  abuse_of_power: 'Abuse of power',
  financial_misconduct: 'Financial misconduct',
  safety_hazard: 'Safety hazard',
  retaliation: 'Retaliation',
  conflict_of_interest: 'Conflict of interest',
  other: 'Other',
};

export default function ReportsPage() {
  const [records, setRecords] = useState<RecordView[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    listRecords('intake', null)
      .then((rs) => { if (alive) setRecords(rs); })
      .catch((err: unknown) => { if (alive) setError(err instanceof Error ? err.message : 'Could not load transparency data'); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, []);

  const byTaxonomy = useMemo(() => {
    const counts = new Map<string, number>();
    for (const r of records) {
      const codes = (r.payload as Record<string, unknown>).taxonomy_codes as string[] | undefined;
      for (const code of codes ?? []) counts.set(code, (counts.get(code) ?? 0) + 1);
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [records]);

  const byMode = useMemo(() => {
    const counts = new Map<string, number>();
    for (const r of records) {
      const mode = (r.payload as Record<string, unknown>).mode as string | undefined;
      counts.set(mode ?? 'unknown', (counts.get(mode ?? 'unknown') ?? 0) + 1);
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [records]);

  const published = byTaxonomy.filter(([, n]) => n >= MIN_COHORT);
  const hidden = byTaxonomy.filter(([, n]) => n < MIN_COHORT);
  const max = Math.max(...published.map(([, n]) => n), 1);

  return (
    <main className="shell">
      <div className="hero">
        <h1>Transparency reports</h1>
        <p>Aggregate, de-identified figures that show whether the process is working — never who reported what.</p>
      </div>

      {error ? (
        <Alert tone="warn" title="Live data unavailable">{error}</Alert>
      ) : (
        <>
          <div className="grid">
            <Stat label="Reports received" value={loading ? '…' : records.length} hint="Since this tenant activated" tone="accent" />
            <Stat label="Published categories" value={loading ? '…' : published.length} hint={`Above the ${MIN_COHORT}-report cohort threshold`} tone="info" />
            <Stat label="Hidden categories" value={loading ? '…' : hidden.length} hint="Cohort too small to publish" tone="neutral" />
          </div>

          <div className="split">
            <Panel title="Reported concerns">
              {published.length === 0 ? (
                <p className="muted">{loading ? 'Loading…' : 'No category has reached the publishable cohort size yet.'}</p>
              ) : (
                <div className="stack">
                  {published.map(([code, n]) => (
                    <div key={code}>
                      <div className="row" style={{ justifyContent: 'space-between' }}>
                        <span>{TAXONOMY_LABELS[code] ?? code.replace(/_/g, ' ')}</span>
                        <strong>{n}</strong>
                      </div>
                      <div className="chart-bar"><div className="chart-bar-fill" style={{ width: `${(n / max) * 100}%` }} /></div>
                    </div>
                  ))}
                </div>
              )}
            </Panel>

            <div className="stack">
              <Panel title="Reporting mode">
                {byMode.length === 0 ? (
                  <p className="muted">{loading ? 'Loading…' : 'No reports yet.'}</p>
                ) : (
                  byMode.map(([mode, n]) => (
                    <div key={mode} className="row" style={{ justifyContent: 'space-between' }}>
                      <span className="capitalize">{mode}</span>
                      <strong>{n}</strong>
                    </div>
                  ))
                )}
              </Panel>
              <Panel title="Publication rules">
                <ul>
                  <li>Only aggregates of at least {MIN_COHORT} reports are published.</li>
                  <li>Smaller cohorts are withheld to protect individuals.</li>
                  <li>No individual complaint rankings are ever published.</li>
                  <li>Process metrics (response time, remediation) are published separately from case content.</li>
                </ul>
              </Panel>
            </div>
          </div>

          {hidden.length > 0 && (
            <Alert tone="info" title={`${hidden.length} categor${hidden.length === 1 ? 'y is' : 'ies are'} withheld`}>
              <p>Their counts stay private until the cohort is large enough to be safe.</p>
            </Alert>
          )}
        </>
      )}
    </main>
  );
}
