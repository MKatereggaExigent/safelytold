'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Logo, ThemeToggle } from '@safelytold/ui/components';

const LINKS = [
  { href: '/', label: 'Home' },
  { href: '/governance', label: 'Governance' },
  { href: '/integrity', label: 'Integrity' },
  { href: '/privacy', label: 'Privacy' },
  { href: '/ai', label: 'AI' },
  { href: '/reports', label: 'Reports' },
];

export function TrustHeader() {
  const pathname = usePathname();
  return (
    <>
      <div className="bar-banner">
        <strong>⚠</strong>
        <span>This application is not an emergency service.</span>
      </div>
      <header className="site-header">
        <div className="site-header-inner">
          {/* Plain anchors so the links escape the /trust basePath and return
              to the main site root served by nginx. */}
          <a href="/" aria-label="Home to main site"><Logo label="Workplace Integrity Trust Centre" /></a>
          <nav className="nav-links" aria-label="Primary">
            {LINKS.map((link) => (
              link.href === '/' ? (
                <a key={link.href} href="/" className="nav-link">Home</a>
              ) : (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`nav-link${pathname === link.href ? ' nav-link-active' : ''}`}
                >
                  {link.label}
                </Link>
              )
            ))}
            <ThemeToggle />
          </nav>
        </div>
      </header>
    </>
  );
}
