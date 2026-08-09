'use client';

import { useCallback, useEffect, useState } from 'react';
import { Alert, Badge, Button, EmptyState, Field, Input, PageHeader, Panel, Select, Checkbox } from '@safelytold/ui/components';
import { createRecord, listRecords, type RecordView } from '@safelytold/ui/api';
import { decryptString, encryptString, loadOrCreateVaultKey } from '@safelytold/ui/crypto';
import { useI18n, useToast } from '@safelytold/ui/context';
import { formatDate } from '@safelytold/ui/hooks';
import { loadReporterCase } from '../../../lib/reporter';

const RELATIONSHIPS = ['colleague', 'manager', 'union representative', 'family member', 'health professional', 'legal representative', 'other'];
const PERMISSIONS = ['receive_updates', 'attend_meetings', 'receive_messages', 'view_case_status'];

export default function SupportPage() {
  const { t } = useI18n();
  const { push } = useToast();
  const [caseId, setCaseId] = useState<string | null>(null);
  const [publicCode, setPublicCode] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [contact, setContact] = useState('');
  const [relationship, setRelationship] = useState(RELATIONSHIPS[0]);
  const [permissions, setPermissions] = useState<string[]>(['receive_updates']);
  const [invitations, setInvitations] = useState<RecordView[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [decrypted, setDecrypted] = useState<Record<string, { name: string; contact: string } | null>>({});

  const refresh = useCallback(async (id: string) => {
    setLoading(true);
    try {
      const records = await listRecords('support', null);
      const mine = records.filter((r) => r.payload.case_id === id && r.kind === 'support_invitation');
      setInvitations(mine);
      let key: CryptoKey | null = null;
      const map: Record<string, { name: string; contact: string } | null> = {};
      for (const inv of mine) {
        const sealed = (inv.payload as Record<string, unknown>).sealed_identity as string | undefined;
        if (!sealed) {
          map[inv.id] = null;
          continue;
        }
        try {
          key ??= await loadOrCreateVaultKey(`support_invitation:${id}`);
          const parsed = JSON.parse(await decryptString(key, sealed)) as { name: string; contact: string };
          map[inv.id] = parsed;
        } catch {
          map[inv.id] = null;
        }
      }
      setDecrypted(map);
    } catch {
      setInvitations([]);
      setDecrypted({});
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const stored = loadReporterCase();
    if (stored) {
      setCaseId(stored.caseId);
      setPublicCode(stored.publicCode);
      refresh(stored.caseId);
    }
  }, [refresh]);

  function togglePermission(key: string, checked: boolean) {
    setPermissions((prev) => (checked ? [...new Set([...prev, key])] : prev.filter((k) => k !== key)));
  }

  async function sendInvitation() {
    if (!caseId || !name.trim() || !contact.trim()) {
      push(t('crsup_toast_require_fields'), 'warn');
      return;
    }
    setSending(true);
    try {
      const key = await loadOrCreateVaultKey(`support_invitation:${caseId}`);
      const sealedIdentity = await encryptString(
        key,
        JSON.stringify({ name: name.trim(), contact: contact.trim() }),
      );
      await createRecord(
        'support',
        'support_invitation',
        {
          case_id: caseId,
          sealed_identity: sealedIdentity,
          relationship,
          permissions,
          status: 'pending',
          created_at: new Date().toISOString(),
        },
        null,
      );
      setName('');
      setContact('');
      setRelationship(RELATIONSHIPS[0]);
      setPermissions(['receive_updates']);
      await refresh(caseId);
      push(t('crsup_toast_created'), 'ok');
    } catch (err) {
      push(err instanceof Error ? err.message : t('crsup_toast_create_failed'), 'danger');
    } finally {
      setSending(false);
    }
  }

  return (
    <main className="shell">
      <PageHeader
        eyebrow={t('crsup_eyebrow')}
        title={t('crsup_title')}
        subtitle={t('crsup_subtitle')}
      />

      {!caseId ? (
        <Alert tone="info" title={t('crsup_alert_open_case_title')}>
          <p>
            {t('crsup_alert_open_case_body')}{' '}
            <a href="/control-room/case">{t('crsup_alert_open_case_link')}</a>.
          </p>
        </Alert>
      ) : (
        <>
          <Alert tone="info" title={t('crsup_inviting_title', { code: publicCode ?? caseId.slice(0, 8) })}>
            <p>
              {t('crsup_inviting_body')}
            </p>
          </Alert>

          <div className="split">
            <Panel title={t('crsup_panel_new_title')}>
              <Field label={t('crsup_field_name')} required>
                <Input value={name} onChange={(e) => setName(e.target.value)} autoComplete="off" />
              </Field>
              <Field label={t('crsup_field_contact')} required hint={t('crsup_field_contact_hint')}>
                <Input value={contact} onChange={(e) => setContact(e.target.value)} autoComplete="off" />
              </Field>
              <Field label={t('crsup_field_relationship')}>
                <Select value={relationship} onChange={(e) => setRelationship(e.target.value)}>
                  {RELATIONSHIPS.map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </Select>
              </Field>
              <Field label={t('crsup_field_permissions')}>
                {PERMISSIONS.map((key) => (
                  <Checkbox
                    key={key}
                    label={key.replace(/_/g, ' ')}
                    checked={permissions.includes(key)}
                    onChange={(e) => togglePermission(key, e.target.checked)}
                  />
                ))}
              </Field>
              <Button onClick={sendInvitation} loading={sending} size="lg">{t('crsup_send_button')}</Button>
            </Panel>

            <div className="stack">
              <Panel title={t('crsup_invitations_title')} subtitle={loading ? t('crsup_loading') : t('crsup_sealed_hint')}>
                {invitations.length === 0 ? (
                  <EmptyState title={t('crsup_empty_title')} description={t('crsup_empty_description')} />
                ) : (
                  invitations.map((inv) => {
                    const p = inv.payload as Record<string, string>;
                    const d = decrypted[inv.id];
                    return (
                      <div key={inv.id} style={{ marginBottom: 12 }}>
                        <div className="row" style={{ justifyContent: 'space-between' }}>
                          <strong>{d ? d.name : t('crsup_sealed')}</strong>
                          <Badge tone={p.status === 'accepted' ? 'ok' : p.status === 'pending' ? 'warn' : 'neutral'}>{p.status}</Badge>
                        </div>
                        <p className="muted" style={{ margin: '4px 0 0' }}>
                          {d ? `${d.contact} · ` : ''}{p.relationship} · {t('crsup_invited')} {formatDate(p.created_at)}
                        </p>
                      </div>
                    );
                  })
                )}
              </Panel>
            </div>
          </div>
        </>
      )}
    </main>
  );
}
