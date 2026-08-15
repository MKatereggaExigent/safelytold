'use client';

import Link from 'next/link';
import { useI18n } from '@safelytold/ui/context';

export function SiteFooter() {
  const { t } = useI18n();
  return (
    <>
      <Link href="/report" className="helpme-fab" aria-label={t('layout_fab_aria')}>
        {t('layout_fab')}
      </Link>
      <footer className="site-footer">
        <div className="site-footer-inner">
          <span>{t('layout_org')}</span>
          <span>
            {t('layout_no_ai')} · <Link href="/emergency">{t('layout_not_emergency')}</Link>
          </span>
          <span>
            <Link href="/pricing">For organisations</Link> · <a href="mailto:sales@datasqan.com">sales@datasqan.com</a> · <a href="tel:+27686159700">+27 68 615 9700</a>
          </span>
        </div>
      </footer>
    </>
  );
}
