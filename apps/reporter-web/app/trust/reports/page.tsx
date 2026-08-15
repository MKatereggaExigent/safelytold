'use client';

import { useMemo } from 'react';
import { Alert, Badge, Panel, Stat } from '@safelytold/ui/components';
import { listRecords, type RecordView } from '@safelytold/ui/api';
import { useEffect, useState } from 'react';
import { useI18n } from '@safelytold/ui/context';
import { TrustNav } from '../TrustNav';

const MIN_COHORT = 5;

const TAXONOMY_LABELS: Record<string, string> = {
  discrimination: 'rep_tax_discrimination',
  harassment: 'rep_tax_harassment',
  fraud: 'tax_fraud',
  theft: 'tax_theft',
  bribery: 'tax_bribery',
  procurement_irregularity: 'tax_procurement_irregularity',
  money_laundering: 'tax_money_laundering',
  expense_fraud: 'tax_expense_fraud',
  bullying: 'tax_bullying',
  sexual_harassment: 'tax_sexual_harassment',
  favouritism: 'tax_favouritism',
  racism: 'tax_racism',
  intimidation: 'tax_intimidation',
  nepotism: 'tax_nepotism',
  victimisation: 'tax_victimisation',
  promotion_irregularity: 'tax_promotion_irregularity',
  performance_management_abuse: 'tax_performance_management_abuse',
  unfair_disciplinary_action: 'tax_unfair_disciplinary_action',
  unfair_labour_practice: 'tax_unfair_labour_practice',
  working_conditions: 'tax_working_conditions',
  hr_matters: 'tax_hr_matters',
  inappropriate_conduct: 'tax_inappropriate_conduct',
  unethical_business_practice: 'tax_unethical_business_practice',
  policy_breach: 'tax_policy_breach',
  abuse_of_authority: 'tax_abuse_of_authority',
  misconduct: 'tax_misconduct',
  health_and_safety: 'tax_health_and_safety',
  violence: 'tax_violence',
  unsafe_working_conditions: 'tax_unsafe_working_conditions',
  corruption: 'tax_corruption',
  service_delivery: 'tax_service_delivery',
  environment: 'tax_environment',
  public_infrastructure: 'tax_public_infrastructure',
  abuse_of_power: 'rep_tax_abuse_of_power',
  financial_misconduct: 'rep_tax_financial_misconduct',
  safety_hazard: 'rep_tax_safety_hazard',
  retaliation: 'rep_tax_retaliation',
  conflict_of_interest: 'rep_tax_conflict_of_interest',
  other: 'rep_tax_other',
};

export default function ReportsPage() {
  const { t } = useI18n();
  const [records, setRecords] = useState<RecordView[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    listRecords('intake', null)
      .then((rs) => { if (alive) setRecords(rs); })
      .catch((err: unknown) => { if (alive) setError(err instanceof Error ? err.message : t('rep_load_error')); })
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
      <TrustNav />
      <div className="hero">
        <h1>{t('rep_title')}</h1>
        <p>{t('rep_subtitle')}</p>
      </div>

      {error ? (
        <Alert tone="warn" title={t('rep_live_unavailable')}>{error}</Alert>
      ) : (
        <>
          <div className="grid">
            <Stat label={t('rep_received_label')} value={loading ? '…' : records.length} hint={t('rep_received_hint')} tone="accent" />
            <Stat label={t('rep_published_label')} value={loading ? '…' : published.length} hint={t('rep_published_hint', { count: MIN_COHORT })} tone="info" />
            <Stat label={t('rep_hidden_label')} value={loading ? '…' : hidden.length} hint={t('rep_hidden_hint')} tone="neutral" />
          </div>

          <div className="split">
            <Panel title={t('rep_concerns_title')}>
              {published.length === 0 ? (
                <p className="muted">{loading ? t('rep_loading') : t('rep_no_published')}</p>
              ) : (
                <div className="stack">
                  {published.map(([code, n]) => (
                    <div key={code}>
                      <div className="row" style={{ justifyContent: 'space-between' }}>
                        <span>{t(TAXONOMY_LABELS[code] ?? code.replace(/_/g, ' '))}</span>
                        <strong>{n}</strong>
                      </div>
                      <div className="chart-bar"><div className="chart-bar-fill" style={{ width: `${(n / max) * 100}%` }} /></div>
                    </div>
                  ))}
                </div>
              )}
            </Panel>

            <div className="stack">
              <Panel title={t('rep_mode_title')}>
                {byMode.length === 0 ? (
                  <p className="muted">{loading ? t('rep_loading') : t('rep_no_reports')}</p>
                ) : (
                  byMode.map(([mode, n]) => (
                    <div key={mode} className="row" style={{ justifyContent: 'space-between' }}>
                      <span className="capitalize">{mode}</span>
                      <strong>{n}</strong>
                    </div>
                  ))
                )}
              </Panel>
              <Panel title={t('rep_rules_title')}>
                <ul>
                  <li>{t('rep_rule_min', { count: MIN_COHORT })}</li>
                  <li>{t('rep_rule_smaller')}</li>
                  <li>{t('rep_rule_rankings')}</li>
                  <li>{t('rep_rule_metrics')}</li>
                </ul>
              </Panel>
            </div>
          </div>

          {hidden.length > 0 && (
            <Alert tone="info" title={hidden.length === 1 ? t('rep_withheld_one') : t('rep_withheld_many', { count: hidden.length })}>
              <p>{t('rep_withheld_body')}</p>
            </Alert>
          )}
        </>
      )}
    </main>
  );
}
