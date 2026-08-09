'use client';

import { useMemo } from 'react';
import { Alert, Badge, PageHeader, Panel, Stat } from '@safelytold/ui/components';
import { useRecords } from '@safelytold/ui/hooks';
import { TAXONOMY_LABELS } from '../../lib/staff';

const MIN_COHORT = 5;

export default function AnalyticsPage() {
  const { records: reports, loading } = useRecords('intake', 'report');
  const { records: analytics } = useRecords('analytics');

  const byTaxonomy = useMemo(() => {
    const counts = new Map<string, number>();
    for (const r of reports) {
      const codes = (r.payload as Record<string, unknown>).taxonomy_codes as string[] | undefined;
      for (const code of codes ?? []) counts.set(code, (counts.get(code) ?? 0) + 1);
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [reports]);

  const byMode = useMemo(() => {
    const counts = new Map<string, number>();
    for (const r of reports) {
      const mode = (r.payload as Record<string, unknown>).mode as string | undefined;
      counts.set(mode ?? 'unknown', (counts.get(mode ?? 'unknown') ?? 0) + 1);
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [reports]);

  const overThreshold = byTaxonomy.filter(([, n]) => n >= MIN_COHORT);
  const underThreshold = byTaxonomy.filter(([, n]) => n < MIN_COHORT);
  const max = Math.max(...byTaxonomy.map(([, n]) => n), 1);

  const maxAnchors = useMemo(() => analytics.length, [analytics]);

  return (
    <main className="shell">
      <PageHeader
        eyebrow="Organisational analytics"
        title="Patterns, not people"
        subtitle="Aggregates are only shown above minimum cohort thresholds. There are no individual complaint rankings."
      />

      <Alert tone="warn" title="Reporting volume is not culture quality">
        <p>
          An increase in reports can mean greater trust, not worsening culture. Interpret alongside response time,
          communication quality and remediation — never as a “most complained-about employee” list.
        </p>
      </Alert>

      <div className="grid">
        <Stat label="Reports received" value={reports.length} hint={loading ? 'Loading…' : 'From the public portal'} tone="accent" />
        <Stat label="Taxonomy categories" value={byTaxonomy.length} hint="With at least one report" tone="info" />
        <Stat label="Analytics records" value={maxAnchors} hint="Derived, de-identified" tone="violet" />
      </div>

      <div className="split">
        <Panel title="Reports by category" subtitle={`${overThreshold.length} categories above the ${MIN_COHORT}-report cohort threshold`}>
          {byTaxonomy.length === 0 ? (
            <p className="muted">No reports yet.</p>
          ) : (
            <div className="stack">
              {byTaxonomy.map(([code, n]) => {
                const above = n >= MIN_COHORT;
                return (
                  <div key={code}>
                    <div className="row" style={{ justifyContent: 'space-between' }}>
                      <span>{TAXONOMY_LABELS[code] ?? code.replace(/_/g, ' ')}</span>
                      <span className="row" style={{ gap: 8 }}>
                        {!above && <Badge tone="neutral">below cohort</Badge>}
                        <strong>{n}</strong>
                      </span>
                    </div>
                    <div className="chart-bar"><div className="chart-bar-fill" style={{ width: `${(n / max) * 100}%` }} /></div>
                  </div>
                );
              })}
            </div>
          )}
        </Panel>

        <div className="stack">
          <Panel title="Reports by reporting mode">
            {byMode.length === 0 ? (
              <p className="muted">No reports yet.</p>
            ) : (
              byMode.map(([mode, n]) => (
                <div key={mode} className="row" style={{ justifyContent: 'space-between' }}>
                  <span className="capitalize">{mode}</span>
                  <strong>{n}</strong>
                </div>
              ))
            )}
          </Panel>
          <Panel title="Guardrails">
            <ul>
              <li>No individual complaint rankings, ever.</li>
              <li>Small cohorts are hidden below the minimum threshold.</li>
              <li>Differential privacy can be enabled for sensitive groups.</li>
              <li>Drill-down never reconstructs identities.</li>
            </ul>
          </Panel>
        </div>
      </div>

      {underThreshold.length > 0 && (
        <Alert tone="info" title={`${underThreshold.length} categor${underThreshold.length === 1 ? 'y is' : 'ies are'} hidden below the cohort threshold`}>
          <p>Their counts stay private until enough reports exist to make the aggregate safe.</p>
        </Alert>
      )}
    </main>
  );
}
