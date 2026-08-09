'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useI18n } from '@safelytold/ui/context';

const SECTIONS = [
  { href: '/trust', key: 'tnav_overview' },
  { href: '/trust/governance', key: 'tnav_governance' },
  { href: '/trust/integrity', key: 'tnav_integrity' },
  { href: '/trust/privacy', key: 'tnav_privacy' },
  { href: '/trust/ai', key: 'tnav_ai' },
  { href: '/trust/reports', key: 'tnav_reports' },
  { href: '/trust/verify', key: 'tnav_verify' },
];

export function TrustNav() {
  const pathname = usePathname();
  const { t } = useI18n();
  return (
    <nav className="trust-nav" aria-label={t('tnav_aria')}>
      {SECTIONS.map((s) => (
        <Link
          key={s.href}
          href={s.href}
          className={`trust-nav-link${pathname === s.href ? ' trust-nav-link-active' : ''}`}
        >
          {t(s.key)}
        </Link>
      ))}
    </nav>
  );
}
