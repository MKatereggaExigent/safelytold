'use client';

import Link from 'next/link';
import { Badge, Button, Card, PageHeader } from '@safelytold/ui/components';
import { useState } from 'react';
import { WorldInsights } from './WorldInsights';
import { REPORT_MODES } from '../lib/reporter';
import { HomeNav } from './HomeNav';
import { useI18n } from '@safelytold/ui/context';

const FEATURES = [
  { icon: '🛡', titleKey: 'home_feat_1_title', textKey: 'home_feat_1_text' },
  { icon: '🔐', titleKey: 'home_feat_2_title', textKey: 'home_feat_2_text' },
  { icon: '🧑‍⚖️', titleKey: 'home_feat_3_title', textKey: 'home_feat_3_text' },
  { icon: '📦', titleKey: 'home_feat_4_title', textKey: 'home_feat_4_text' },
  { icon: '🔁', titleKey: 'home_feat_5_title', textKey: 'home_feat_5_text' },
  { icon: '👥', titleKey: 'home_feat_6_title', textKey: 'home_feat_6_text' },
];

const STEPS = [
  ['home_step_1_title', 'home_step_1_text'],
  ['home_step_2_title', 'home_step_2_text'],
  ['home_step_3_title', 'home_step_3_text'],
  ['home_step_4_title', 'home_step_4_text'],
];

const SECTIONS = [
  { id: 'ways', label: 'home_sec_ways' },
  { id: 'process', label: 'home_sec_process' },
  { id: 'boundaries', label: 'home_sec_boundaries' },
  { id: 'insights', label: 'home_sec_insights' },
];

export default function HomePage() {
  const { t } = useI18n();
  const [activeSection, setActiveSection] = useState(SECTIONS[0].id);
  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">{t('home_eyebrow')}</p>
        <h1 className="hero-title">{t('home_title')}</h1>
        <p className="hero-sub">{t('home_sub')}</p>
        <div className="hero-actions">
          <Link href="/report"><Button size="lg">{t('nav_report')}</Button></Link>
          <Link href="/control-room/mailbox"><Button variant="secondary" size="lg">{t('home_open_mailbox')}</Button></Link>
        </div>
        <div className="trust-strip">
          <Badge tone="ok">{t('home_badge_minimisation')}</Badge>
          <Badge tone="info">{t('home_badge_purpose')}</Badge>
          <Badge tone="violet">{t('home_badge_human')}</Badge>
          <Badge tone="accent">{t('home_badge_audit')}</Badge>
        </div>
      </section>

      <HomeNav sections={SECTIONS} active={activeSection} onSelect={setActiveSection} />

      {activeSection === 'ways' && (
        <section id="ways" className="section-panel">
          <PageHeader
            eyebrow={t('home_ways_eyebrow')}
            title={t('home_ways_title')}
            subtitle={t('home_ways_sub')}
          />
          <div className="grid grid-3 section-grid">
            {REPORT_MODES.map((mode) => (
              <Card key={mode.value} className="feature">
                <div className="feature-icon" aria-hidden>◆</div>
                <h3>{t(mode.key)}</h3>
                <Badge tone="accent">{t(mode.badgeKey)}</Badge>
                <p>{t(mode.descKey)}</p>
              </Card>
            ))}
          </div>
        </section>
      )}

      {activeSection === 'process' && (
        <section id="process" className="section-panel">
          <PageHeader eyebrow={t('home_process_eyebrow')} title={t('home_process_title')} />
          <div className="grid grid-3 section-grid">
            {STEPS.map(([titleKey, textKey]) => (
              <Card key={titleKey} className="feature">
                <h3>{t(titleKey)}</h3>
                <p>{t(textKey)}</p>
              </Card>
            ))}
          </div>
        </section>
      )}

      {activeSection === 'boundaries' && (
        <section id="boundaries" className="section-panel">
          <PageHeader eyebrow={t('home_bound_eyebrow')} title={t('home_bound_title')} />
          <div className="grid grid-3 section-grid">
            {FEATURES.map((f) => (
              <Card key={f.titleKey} className="feature">
                <div className="feature-icon" aria-hidden>{f.icon}</div>
                <h3>{t(f.titleKey)}</h3>
                <p>{t(f.textKey)}</p>
              </Card>
            ))}
          </div>
        </section>
      )}

      {activeSection === 'insights' && (
        <section id="insights" className="section-panel">
          <WorldInsights />
        </section>
      )}
    </main>
  );
}
