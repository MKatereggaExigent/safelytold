import '@safelytold/ui/styles.css';
import './globals.css';
import type { Metadata } from 'next';
import { Toaster } from '@safelytold/ui/components';
import { FoundationProvider } from '@safelytold/ui/context';
import en from '../messages/en.json';
import af from '../messages/af.json';
import zu from '../messages/zu.json';
import { AuthGate } from './AuthGate';
import { PageShell } from './PageShell';

export const metadata: Metadata = {
  title: 'Integrity Workspace',
  description: 'Staff portal for case triage, investigation, evidence, protection and governance.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-theme="light">
      <body>
        <FoundationProvider messages={{ en, af, zu }}>
          <AuthGate>
            <PageShell>{children}</PageShell>
          </AuthGate>
          <Toaster />
        </FoundationProvider>
      </body>
    </html>
  );
}
