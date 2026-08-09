'use client';

import { PageHeader, Stat } from '@safelytold/ui/components';
import { COMMON_REMEDIES, COMMON_REPORT_TYPES, OUTCOME_SIGNALS, ROOT_CAUSES, type RankedInsight } from '../lib/world-insights';
import { useI18n } from '@safelytold/ui/context';

function RankedList({ titleKey, items, showShare }: { titleKey: string; items: RankedInsight[]; showShare?: boolean }) {
  const { t } = useI18n();
  return (
    <div className="insights-panel">
      <h3 className="insights-panel-title">{t(titleKey)}</h3>
      <ol className="ranked-list">
        {items.map((item) => (
          <li key={`${titleKey}-${item.rank}`} className="ranked-row">
            <span className="ranked-rank" aria-hidden>{item.rank}</span>
            <div className="ranked-body">
              <div className="ranked-head">
                <span className="ranked-label">{t(item.key)}</span>
                {showShare && item.share && <span className="ranked-share">{item.share}</span>}
              </div>
              <div className="ranked-track">
                <div
                  className="ranked-fill"
                  style={{ width: `${showShare && item.share ? 100 - item.rank * 8 : 100 - item.rank * 10}%` }}
                />
              </div>
              <p className="ranked-note">{t(item.noteKey)}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

export function WorldInsights() {
  const { t } = useI18n();
  return (
    <section className="world-insights" aria-labelledby="world-insights-title">
      <PageHeader
        eyebrow={t('wi_eyebrow')}
        title={t('wi_title')}
        subtitle={t('wi_subtitle')}
      />

      <div className="insights-privacy">
        <span aria-hidden>🔒</span>
        <p>
          <strong>{t('wi_privacy_strong')}</strong> {t('wi_privacy_body')}
        </p>
      </div>

      <div className="grid grid-3 insights-stats">
        {OUTCOME_SIGNALS.map((s) => (
          <Stat key={s.key} label={t(s.key)} value={s.value} hint={t(s.hintKey)} tone="accent" />
        ))}
      </div>

      <div className="insights-grid">
        <RankedList titleKey="wi_list_types" items={COMMON_REPORT_TYPES} showShare />
        <RankedList titleKey="wi_list_causes" items={ROOT_CAUSES} />
      </div>
      <div className="insights-grid">
        <RankedList titleKey="wi_list_remedies" items={COMMON_REMEDIES} />
        <div className="insights-panel">
          <h3 className="insights-panel-title">{t('wi_means_title')}</h3>
          <ul className="insights-takeaways">
            <li>{t('wi_takeaway_1')}</li>
            <li>{t('wi_takeaway_2')}</li>
            <li>{t('wi_takeaway_3')}</li>
            <li>{t('wi_takeaway_4')}</li>
          </ul>
        </div>
      </div>
    </section>
  );
}
