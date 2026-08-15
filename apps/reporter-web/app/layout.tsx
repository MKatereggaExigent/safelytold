import '@safelytold/ui/styles.css';
import './globals.css';
import type { Metadata } from 'next';
import { Toaster } from '@safelytold/ui/components';
import { FoundationProvider } from '@safelytold/ui/context';
import en from '../messages/en.json';
import af from '../messages/af.json';
import zu from '../messages/zu.json';
import { PublicHeader } from './PublicHeader';
import { SiteFooter } from './SiteFooter';
import { PageShell } from './PageShell';

export const metadata: Metadata = {
  title: 'Speak safely. Stay in control.',
  description: 'Privacy-preserving integrity reporting, protected case management, an anonymous mailbox and trusted support.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-theme="light">
      <body>
        <FoundationProvider messages={{ en, af, zu }}>
          <PublicHeader />
          <PageShell>{children}</PageShell>
          <SiteFooter />
          <Toaster />
        </FoundationProvider>
      </body>
    </html>
  );
}
