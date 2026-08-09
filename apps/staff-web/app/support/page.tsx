'use client';

import { useCallback } from 'react';
import { Alert, Badge, Button, DataTable, EmptyState, PageHeader, Panel, StatusPill } from '@safelytold/ui/components';
import { createRecord, type RecordView } from '@safelytold/ui/api';
import { useSession } from '@safelytold/ui/context';
import { useToast } from '@safelytold/ui/context';
import { formatDate, useRecords } from '@safelytold/ui/hooks';

const PERMISSION_LABELS: Record<string, string> = {
  receive_updates: 'Status updates',
  attend_meetings: 'Meeting attendance',
  send_messages: 'Messages',
  view_documents: 'Documents',
};

export default function SupportPage() {
  const { session } = useSession();
  const { push } = useToast();
  const { records: invitations, loading, refresh } = useRecords('support');

  const activate = useCallback(async (inv: RecordView) => {
    try {
      await createRecord('support', 'support_ack', {
        case_id: (inv.payload as Record<string, unknown>).case_id as string,
        invitation_ref: inv.id,
        status: 'active',
        acknowledged_by: session.subject,
        acknowledged_at: new Date().toISOString(),
      }, session);
      push('Invitation activated', 'ok');
      refresh();
    } catch (err) {
      push(err instanceof Error ? err.message : 'Could not activate invitation', 'danger');
    }
  }, [session, push, refresh]);

  return (
    <main className="shell">
      <PageHeader
        eyebrow="Support circles"
        title="Reporter-chosen supporters"
        subtitle="A supporter is granted exactly the permissions a reporter chooses — never the case code, recovery secret or full case."
      />

      <Alert tone="info" title="Least-privilege support">
        <p>
          Supporters are not investigators. Activating an invitation only allows the supporter to use the permissions
          the reporter ticked. Supporter identities are encrypted on the reporter's device and never stored in
          plaintext — staff only see the relationship, permissions and status.
        </p>
      </Alert>

      <Panel title="Support invitations" subtitle={loading ? 'Loading…' : `${invitations.length} invitations across cases — supporter identities are sealed`} padded={false}>
        <DataTable
          keyField="id"
          loading={loading}
          empty={<EmptyState title="No support invitations" description="Invitations created by reporters appear here." />}
          columns={[
            { key: 'case', label: 'Case', render: (r) => <span className="mono">{(r.payload as Record<string, unknown>).case_id as string}</span> },
            { key: 'identity', label: 'Identity', render: () => <Badge tone="neutral">Sealed</Badge> },
            { key: 'relationship', label: 'Relationship', render: (r) => <span className="muted">{(r.payload as Record<string, unknown>).relationship as string}</span> },
            {
              key: 'permissions',
              label: 'Permissions',
              render: (r) => (
                <span className="row" style={{ gap: 4, flexWrap: 'wrap' }}>
                  {((r.payload as Record<string, unknown>).permissions as string[] ?? []).map((p) => (
                    <Badge key={p} tone="info">{PERMISSION_LABELS[p] ?? p.replace(/_/g, ' ')}</Badge>
                  ))}
                </span>
              ),
            },
            { key: 'status', label: 'Status', render: (r) => <StatusPill status={(r.payload as Record<string, unknown>).status as string} /> },
            { key: 'created', label: 'Created', render: (r) => <span className="muted">{formatDate((r.payload as Record<string, unknown>).created_at as string)}</span> },
            {
              key: 'actions',
              label: 'Actions',
              render: (r) => (
                (r.payload as Record<string, unknown>).status === 'pending' ? (
                  <Button size="sm" variant="secondary" onClick={() => activate(r)}>Activate</Button>
                ) : <span className="muted">—</span>
              ),
            },
          ]}
          rows={invitations}
        />
      </Panel>
    </main>
  );
}
