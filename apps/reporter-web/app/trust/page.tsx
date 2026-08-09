'use client';

import Link from 'next/link';
import { PageHeader, Panel, Alert, Badge } from '@safelytold/ui/components';
import { useI18n } from '@safelytold/ui/context';
import { TrustNav } from './TrustNav';

const PILLARS = [
  {
    key: 'identity',
    title: 'trust_pillar_identity',
    body: 'trust_pillar_identity_body',
  },
  {
    key: 'evidence',
    title: 'trust_pillar_evidence',
    body: 'trust_pillar_evidence_body',
  },
  {
    key: 'authority',
    title: 'trust_pillar_authority',
    body: 'trust_pillar_authority_body',
  },
  {
    key: 'ledger',
    title: 'trust_pillar_ledger',
    body: 'trust_pillar_ledger_body',
  },
  {
    key: 'minimisation',
    title: 'trust_pillar_minimisation',
    body: 'trust_pillar_minimisation_body',
  },
  {
    key: 'governance',
    title: 'trust_pillar_governance',
    body: 'trust_pillar_governance_body',
  },
];

export default function TrustPage() {
  const { t } = useI18n();
  return (
    <main className="shell">
      <TrustNav />
      <PageHeader
        eyebrow={t('trust_eyebrow')}
        title={t('trust_title')}
        subtitle={t('trust_subtitle')}
      />

      <Alert tone="info" title={t('trust_alert_title')}>
        <p>
          {t('trust_alert_body')}
        </p>
      </Alert>

      <div className="grid">
        {PILLARS.map((pillar) => (
          <Panel key={pillar.key} title={t(pillar.title)}>
            <p className="muted">{t(pillar.body)}</p>
          </Panel>
        ))}
      </div>

      <div className="split" style={{ marginTop: 20 }}>
        <Panel title={t('trust_verify_chain_title')}>
          <p>
            {t('trust_verify_chain_body')}
          </p>
          <Link href="/trust/verify" className="btn btn-primary btn-md">{t('trust_verify_chain_link')}</Link>
        </Panel>
        <Panel title={t('trust_verify_proof_title')}>
          <p>
            {t('trust_verify_proof_body')}
          </p>
          <Link href="/trust/verify" className="btn btn-secondary btn-md">{t('trust_verify_proof_link')}</Link>
        </Panel>
      </div>

      <Panel title={t('trust_reports_title')}>
        <p>
          {t('trust_reports_body')}
        </p>
        <Link href="/trust/reports" className="btn btn-primary btn-md">{t('trust_reports_link')}</Link>
      </Panel>

      <Panel title={t('trust_standards_title')}>
        <div className="row" style={{ flexWrap: 'wrap', gap: 8 }}>
          <Badge tone="accent">{t('trust_badge_iso27001')}</Badge>
          <Badge tone="accent">{t('trust_badge_minimisation')}</Badge>
          <Badge tone="accent">{t('trust_badge_dual_approval')}</Badge>
          <Badge tone="accent">{t('trust_badge_purpose_bound')}</Badge>
          <Badge tone="accent">{t('trust_badge_append_only')}</Badge>
          <Badge tone="accent">{t('trust_badge_blockchain')}</Badge>
          <Badge tone="accent">{t('trust_badge_human_ai')}</Badge>
        </div>
      </Panel>
    </main>
  );
}
