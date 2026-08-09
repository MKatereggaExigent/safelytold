'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Logo, ThemeToggle } from '@safelytold/ui/components';
import { useGatewayHealth } from '@safelytold/ui/hooks';
import { useSession } from '@safelytold/ui/context';
import { logoutUrl } from '../lib/auth';
import { STAFF_ROLE_LABEL } from '../lib/staff';

const NAV = [
  { href: '/dashboard', label: 'Dashboard', icon: '▦' },
  { href: '/cases', label: 'Cases', icon: '◉' },
  { href: '/mailbox', label: 'Mailbox', icon: '✉' },
  { href: '/evidence', label: 'Evidence', icon: '▤' },
  { href: '/protection', label: 'Protection', icon: '◈' },
  { href: '/support', label: 'Support circle', icon: '❖' },
  { href: '/analytics', label: 'Analytics', icon: '◮' },
  { href: '/admin', label: 'Admin', icon: '⚙' },
  { href: '/privacy', label: 'Privacy room', icon: '◉' },
  { href: '/ai', label: 'AI copilot', icon: '✦' },
  { href: '/ledger', label: 'Integrity ledger', icon: '⌬' },
  { href: '/audit', label: 'Audit log', icon: '≡' },
];

export function StaffShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { session } = useSession();
  const { health } = useGatewayHealth();
  const [navOpen, setNavOpen] = useState(false);
  useEffect(() => setNavOpen(false), [pathname]);
  const openCount = health
    ? Object.values(health).filter((h) => h.status === 'ok' || h.status === 'healthy').length
    : 0;
  const total = health ? Object.keys(health).length : 0;

  const signOut = () => {
    window.location.assign(logoutUrl());
  };

  return (
    <div className="staff-layout">
      {navOpen && (
        <button type="button" className="staff-nav-backdrop" aria-label="Close menu" onClick={() => setNavOpen(false)} />
      )}
      <aside className={`staff-side${navOpen ? ' staff-side-open' : ''}`}>
        <Link href="/dashboard" aria-label="Staff portal home">
          <Logo label="Integrity workspace" />
        </Link>
        <nav id="staff-nav" className="staff-nav" aria-label="Staff">
          {NAV.map((item) => {
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link key={item.href} href={item.href} className={`staff-nav-link${active ? ' staff-nav-active' : ''}`}>
                <span className="staff-nav-icon" aria-hidden>{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="staff-side-foot">
          <div className="staff-session">
            <strong>{session.displayName ?? session.roles[0]}</strong>
            <span>{STAFF_ROLE_LABEL[session.roles[0]] ?? session.roles[0]} · {session.purpose}</span>
          </div>
          <div className="staff-health">
            <span className={`health-dot ${health ? 'health-ok' : 'health-down'}`} aria-hidden />
            {health ? `${openCount}/${total} services` : 'Gateway unreachable'}
          </div>
        </div>
      </aside>
      <div className="staff-main">
        <header className="staff-top">
          <div className="staff-top-title">
            <button
              type="button"
              className="staff-menu-toggle"
              aria-expanded={navOpen}
              aria-controls="staff-nav"
              aria-label={navOpen ? 'Close menu' : 'Open menu'}
              onClick={() => setNavOpen((v) => !v)}
            >
              <span aria-hidden>☰</span>
            </button>
            <Link href="/dashboard" className="staff-home-link">Staff portal</Link>
            <span className="staff-role-tag">{STAFF_ROLE_LABEL[session.roles[0]] ?? session.roles[0]}</span>
          </div>
          <div className="row" style={{ gap: 10 }}>
            <Link href="/report" className="btn btn-primary btn-sm" target="_blank" rel="noreferrer">HELP ME</Link>
            <Link href="/staff" className="btn btn-ghost btn-sm">Switch role</Link>
            <button type="button" className="btn btn-ghost btn-sm" onClick={signOut}>Sign out</button>
            <ThemeToggle />
          </div>
        </header>
        {children}
      </div>
    </div>
  );
}
