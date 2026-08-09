'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useI18n } from '@safelytold/ui/context';

const SECTIONS = [
  { href: '/control-room', key: 'cnav_journal' },
  { href: '/control-room/mailbox', key: 'cnav_mailbox' },
  { href: '/control-room/case', key: 'cnav_case' },
  { href: '/control-room/support', key: 'cnav_support' },
];

export function ControlNav() {
  const pathname = usePathname();
  const { t } = useI18n();
  return (
    <nav className="trust-nav" aria-label={t('cnav_aria')}>
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
