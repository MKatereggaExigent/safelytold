import '@safelytold/ui/styles.css';
import type { Metadata } from 'next';
import { Toaster } from '@safelytold/ui/components';
import { FoundationProvider } from '@safelytold/ui/context';
import { TrustHeader } from './TrustHeader';
import { PageShell } from './PageShell';

export const metadata: Metadata = {
  title: 'Workplace Integrity Trust Centre',
  description: 'Public product principles, privacy commitments, aggregate transparency and support resources.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-theme="light">
      <body>
        <FoundationProvider>
          <TrustHeader />
          <PageShell>{children}</PageShell>
          <footer className="site-footer">
            <div className="site-footer-inner">
              <span>Workplace Integrity · Trust Centre</span>
              <span>No adverse decisions by AI · Not an emergency service</span>
            </div>
          </footer>
          <Toaster />
        </FoundationProvider>
      </body>
    </html>
  );
}
