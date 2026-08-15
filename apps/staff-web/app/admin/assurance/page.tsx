'use client';

import { useEffect, useState } from 'react';
import { Alert, Badge, PageHeader, Panel } from '@safelytold/ui/components';
import { useSession } from '@safelytold/ui/context';
import { isSuperuser, listAssuranceControls, type AssuranceControlView } from '../../../lib/admin';

const STATUS = {
  enforced: { label: 'Enforced', tone: 'ok' as const },
  partially_enforced: { label: 'Partially enforced', tone: 'warn' as const },
  not_deployed: { label: 'Not yet deployed', tone: 'danger' as const },
};

export default function AssuranceRegisterPage() {
  const { session } = useSession();
  const [controls, setControls] = useState<AssuranceControlView[]>([]);
  const [error, setError] = useState('');
  const allowed = isSuperuser(session);

  useEffect(() => {
    if (!allowed) return;
    listAssuranceControls(session).then(setControls).catch((value: unknown) => {
      setError(value instanceof Error ? value.message : 'Assurance register unavailable');
    });
  }, [allowed, session.accessToken]);

  return (
    <main className="shell">
      <PageHeader eyebrow="Restricted platform assurance" title="Privacy-control register" subtitle="Internal implementation status, verification procedures and engineering evidence." />
      {!allowed && <Alert tone="danger" title="Platform administrator required">This register is restricted to approved platform super-admin accounts.</Alert>}
      {error && <Alert tone="danger" title="Access denied or unavailable">{error}</Alert>}
      {allowed && !error && (
        <div className="grid">
          {controls.map((control) => {
            const status = STATUS[control.status];
            return (
              <Panel key={control.id} title={control.name}>
                <Badge tone={status.tone}>{status.label}</Badge>
                <p>{control.claim}</p>
                <p><strong>How to verify:</strong> {control.verification}</p>
                <details>
                  <summary>Implementation evidence</summary>
                  <ul>{control.evidence.map((item) => <li key={item}><code>{item}</code></li>)}</ul>
                </details>
              </Panel>
            );
          })}
        </div>
      )}
    </main>
  );
}
