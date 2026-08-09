'use client';

import { usePathname } from 'next/navigation';
import { PageTransition } from '@safelytold/ui/components';

export function PageShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return <PageTransition path={pathname}>{children}</PageTransition>;
}
