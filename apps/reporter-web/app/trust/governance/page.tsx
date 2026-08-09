'use client';

import { Badge, Panel } from '@safelytold/ui/components';
import { useI18n } from '@safelytold/ui/context';
import { TrustNav } from '../TrustNav';

const PRINCIPLES = [
  {
    title: 'gov_fair_process_title',
    body: 'gov_fair_process_body',
  },
  {
    title: 'gov_least_privilege_title',
    body: 'gov_least_privilege_body',
  },
  {
    title: 'gov_human_accountability_title',
    body: 'gov_human_accountability_body',
  },
  {
    title: 'gov_data_minimisation_title',
    body: 'gov_data_minimisation_body',
  },
  {
    title: 'gov_transparent_title',
    body: 'gov_transparent_body',
  },
];

export default function GovernancePage() {
  const { t } = useI18n();
  return (
    <main className="shell">
      <TrustNav />
      <div className="hero">
        <h1>{t('gov_title')}</h1>
        <p>{t('gov_subtitle')}</p>
      </div>

      <div className="grid">
        {PRINCIPLES.map((p) => (
          <Panel key={p.title} title={t(p.title)}>
            <p>{t(p.body)}</p>
          </Panel>
        ))}
      </div>

      <div className="split">
        <Panel title={t('gov_separation_title')}>
          <Badge>{t('gov_separation_badge')}</Badge>
          <p>
            {t('gov_separation_body')}
          </p>
        </Panel>
        <Panel title={t('gov_oversight_title')}>
          <Badge>{t('gov_oversight_badge')}</Badge>
          <p>
            {t('gov_oversight_body')}
          </p>
        </Panel>
      </div>
    </main>
  );
}
