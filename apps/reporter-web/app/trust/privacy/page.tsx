'use client';

import { Badge, Panel } from '@safelytold/ui/components';
import { useI18n } from '@safelytold/ui/context';
import { TrustNav } from '../TrustNav';

const CONTROLS = [
  {
    title: 'priv_realms_title',
    body: 'priv_realms_body',
  },
  {
    title: 'priv_purpose_title',
    body: 'priv_purpose_body',
  },
  {
    title: 'priv_reporter_title',
    body: 'priv_reporter_body',
  },
  {
    title: 'priv_retention_title',
    body: 'priv_retention_body',
  },
];

export default function PrivacyPage() {
  const { t } = useI18n();
  return (
    <main className="shell">
      <TrustNav />
      <div className="hero">
        <h1>{t('priv_title')}</h1>
        <p>{t('priv_subtitle')}</p>
      </div>

      <div className="grid">
        {CONTROLS.map((c) => (
          <Panel key={c.title} title={t(c.title)}>
            <p>{t(c.body)}</p>
          </Panel>
        ))}
      </div>

      <div className="split">
        <Panel title={t('priv_anonymity_title')}>
          <ul>
            <li><Badge>{t('priv_anon_badge')}</Badge>{t('priv_anon_body')}</li>
            <li><Badge>{t('priv_conf_badge')}</Badge>{t('priv_conf_body')}</li>
            <li><Badge>{t('priv_iden_badge')}</Badge>{t('priv_iden_body')}</li>
          </ul>
        </Panel>
        <Panel title={t('priv_never_title')}>
          <ul>
            <li>{t('priv_never_label')}</li>
            <li>{t('priv_never_infer')}</li>
            <li>{t('priv_never_sell')}</li>
            <li>{t('priv_never_feed')}</li>
          </ul>
        </Panel>
      </div>
    </main>
  );
}
