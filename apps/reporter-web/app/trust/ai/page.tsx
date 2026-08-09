'use client';

import { useEffect, useState } from 'react';
import { Badge, Panel } from '@safelytold/ui/components';
import { getAiGovernance, type AiGovernance } from '@safelytold/ui/api';
import { useI18n } from '@safelytold/ui/context';
import { TrustNav } from '../TrustNav';

export default function AiPage() {
  const { t } = useI18n();
  const [governance, setGovernance] = useState<AiGovernance | null>(null);

  useEffect(() => {
    getAiGovernance().then(setGovernance).catch(() => setGovernance(null));
  }, []);

  const capabilities = governance?.capabilities ?? [];
  const prohibited = governance?.prohibited_purposes ?? [];

  return (
    <main className="shell">
      <TrustNav />
      <div className="hero">
        <h1>{t('ai_title')}</h1>
        <p>{t('ai_subtitle')}</p>
      </div>

      <div className="split">
        <Panel title={t('ai_may_title')}>
          {capabilities.length === 0 ? (
            <p className="muted">{t('ai_loading_capabilities')}</p>
          ) : (
            <ul>
              {capabilities.map((c) => (
                <li key={c.name}>
                  <Badge tone="info">{t(`ai_cap_${c.name}`)}</Badge>
                  {c.description ? <span className="muted"> — {t(`ai_cap_${c.name}_desc`)}</span> : null}
                </li>
              ))}
            </ul>
          )}
          <p className="muted" style={{ marginTop: 8 }}>
            {t('ai_raw_evidence_label')}<strong>{String(governance?.raw_evidence_allowed)}</strong>{t('ai_human_approval_label')}{' '}
            <strong>{String(governance?.human_approval_default)}</strong>
          </p>
        </Panel>
        <Panel title={t('ai_never_title')}>
          {prohibited.length === 0 ? (
            <p className="muted">{t('ai_loading_prohibited')}</p>
          ) : (
            <ul>
              {prohibited.map((p) => (
                <li key={p}><Badge tone="warn">{t(`ai_forbidden_${p}`)}</Badge></li>
              ))}
            </ul>
          )}
          <p className="muted" style={{ marginTop: 8 }}>
            {t('ai_never_body')}
          </p>
        </Panel>
      </div>
    </main>
  );
}
