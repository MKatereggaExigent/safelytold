'use client';

import { useCallback, useEffect, useState, type FormEvent } from 'react';
import Link from 'next/link';
import { Alert, Badge, Button, DataTable, EmptyState, Field, Input, Kv, PageHeader, Panel, StatusPill } from '@safelytold/ui/components';
import { getRecord, listMailboxMessages, listRecords, reporterSession, type MailboxMessage, type RecordView } from '@safelytold/ui/api';
import { decryptString, importKeyBase64 } from '@safelytold/ui/crypto';
import { useI18n, useToast } from '@safelytold/ui/context';
import { formatDate } from '@safelytold/ui/hooks';
import { CASE_STATUS_LABELS, loadReporterCase, storeReporterCase } from '../../../lib/reporter';

interface LocalNarrative {
  sealed: string;
  key: string;
}

export default function CasePage() {
  const { t } = useI18n();
  const { push } = useToast();
  const [caseId, setCaseId] = useState<string | null>(null);
  const [publicCode, setPublicCode] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [code, setCode] = useState('');
  const [secret, setSecret] = useState('');
  const [opening, setOpening] = useState(false);
  const [report, setReport] = useState<RecordView | null>(null);
  const [caseRecords, setCaseRecords] = useState<RecordView[]>([]);
  const [protection, setProtection] = useState<RecordView[]>([]);
  const [messages, setMessages] = useState<MailboxMessage[]>([]);
  const [narrative, setNarrative] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const stored = loadReporterCase();
    if (stored) {
      setCaseId(stored.caseId);
      setPublicCode(stored.publicCode);
      if (stored.token) setToken(stored.token);
    }
  }, []);

  const loadCase = useCallback(async (id: string, access: string | null) => {
    setLoading(true);
    setError(null);
    try {
      const [reportRecord, caseList, protectionList, mailboxList] = await Promise.all([
        getRecord('intake', id, null).catch(() => null),
        listRecords('case', null, { caseId: id, limit: 1000 }),
        listRecords('protection', null, { caseId: id, limit: 1000 }),
        access ? listMailboxMessages(id, access).catch(() => []) : Promise.resolve([]),
      ]);
      setReport(reportRecord);
      setCaseRecords(caseList ?? []);
      setProtection(protectionList ?? []);
      setMessages(mailboxList ?? []);

      const raw = localStorage.getItem(`wpc:reporter:narrative:${id}`);
      if (raw) {
        const local = JSON.parse(raw) as LocalNarrative;
        setNarrative(await decryptString(await importKeyBase64(local.key), local.sealed));
      } else {
        setNarrative(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t('cse_toast_load_failed'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (caseId) loadCase(caseId, token);
  }, [caseId, token, loadCase]);

  async function open(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setOpening(true);
    try {
      const result = await reporterSession(code.trim(), secret.trim());
      storeReporterCase({
        caseId: result.case_id,
        publicCode: code.trim(),
        token: result.session,
        expiresAt: result.expires_at,
      });
      setCaseId(result.case_id);
      setPublicCode(code.trim());
      setToken(result.session);
      push(t('cse_toast_loaded'), 'ok');
    } catch (err) {
      setError(err instanceof Error ? err.message : t('cse_open_error_failed'));
    } finally {
      setOpening(false);
    }
  }

  const caseStatusRecord = caseRecords.find((r) => r.kind === 'case');
  const status = (caseStatusRecord?.payload as Record<string, string> | undefined)?.status;
  const activeMessages = messages.length;

  if (!caseId) {
    return (
      <main className="shell">
        <PageHeader eyebrow={t('cse_eyebrow')} title={t('cse_track_title')} subtitle={t('cse_track_subtitle')} />
        <div className="split">
          <Panel title={t('cse_open_case_title')}>
            <form onSubmit={open}>
              <Field label={t('cse_field_case_code')} required>
                <Input value={code} onChange={(e) => setCode(e.target.value)} autoComplete="off" />
              </Field>
              <Field label={t('cse_field_secret')} required>
                <Input type="password" value={secret} onChange={(e) => setSecret(e.target.value)} autoComplete="off" />
              </Field>
              {error && <Alert tone="danger" title={t('cse_alert_unable_open')}>{error}</Alert>}
              <Button type="submit" loading={opening} size="lg">{t('cse_open_case_button')}</Button>
            </form>
          </Panel>
          <Panel title={t('cse_lost_codes_title')}>
            <p>
              {t('cse_lost_codes_body')}
            </p>
            <Button variant="secondary" onClick={() => (window.location.href = '/journal')}>{t('cse_open_journal_button')}</Button>
          </Panel>
        </div>
      </main>
    );
  }

  return (
    <main className="shell">
      <PageHeader
        eyebrow={t('cse_eyebrow')}
        title={t('cse_case_title', { code: publicCode ?? caseId.slice(0, 8) })}
        subtitle={t('cse_subtitle')}
        actions={<Button variant="ghost" size="sm" onClick={() => loadCase(caseId, token)}>{t('cse_refresh')}</Button>}
      />

      {loading && <p className="muted">{t('cse_loading_details')}</p>}
      {error && <Alert tone="danger" title={t('cse_alert_error_title')}>{error}</Alert>}

      {report && (
        <div className="grid">
          <Panel title={t('cse_status_title')}>
            <StatusPill status={status ?? (report.payload as Record<string, unknown>).status as string} label={t(CASE_STATUS_LABELS[status ?? 'unverified'].key)} />
            <Kv
              columns={1}
              items={[
                { label: t('cse_kv_case_ref'), value: <span className="mono">{caseId}</span> },
                { label: t('cse_kv_mode'), value: (report.payload as Record<string, unknown>).mode as string },
                { label: t('cse_kv_jurisdiction'), value: (report.payload as Record<string, unknown>).jurisdiction_code as string },
                { label: t('cse_kv_submitted'), value: formatDate((report.payload as Record<string, unknown>).created_at as string) },
              ]}
            />
          </Panel>
          <Panel title={t('cse_protection_title')}>
            {protection.length === 0 ? (
              <p className="muted">{t('cse_no_protection_plan')}</p>
            ) : (
              protection.map((p) => (
                <div key={p.id} style={{ marginBottom: 10 }}>
                  <Badge tone="ok">{t('cse_plan_active')}</Badge>
                  <p className="muted" style={{ margin: '6px 0 0' }}>
                    {(p.payload as Record<string, unknown>).approved_measures as string ?? t('cse_measures_approved')} · {t('cse_next_review')}{' '}
                    {formatDate((p.payload as Record<string, unknown>).next_review_at as string)}
                  </p>
                </div>
              ))
            )}
          </Panel>
          <Panel title={t('cse_mailbox_title')}>
            <Badge tone="info">{t('cse_message_count', { count: activeMessages })}</Badge>
            <p className="muted">{t('cse_mailbox_body')}</p>
            <Link href="/control-room/mailbox" className="btn btn-secondary btn-md">{t('cse_open_mailbox')}</Link>
          </Panel>
        </div>
      )}

      <div className="stack" style={{ marginTop: 20 }}>
        {narrative && (
          <Panel title={t('cse_narrative_title')}>
            <Alert tone="info" title={t('cse_local_copy_title')}>
              <p>{t('cse_local_copy_body')}</p>
            </Alert>
            <p style={{ whiteSpace: 'pre-wrap' }}>{narrative}</p>
          </Panel>
        )}

        <Panel title={t('cse_activity_title')} subtitle={t('cse_activity_subtitle')} padded={false}>
          <DataTable
            keyField="id"
            loading={loading}
            empty={<EmptyState title={t('cse_activity_empty_title')} description={t('cse_activity_empty_description')} />}
            columns={[
              { key: 'kind', label: t('cse_col_record'), render: (r) => <Badge tone="accent">{r.kind.replace(/_/g, ' ')}</Badge> },
              { key: 'status', label: t('cse_col_status'), render: (r) => <StatusPill status={r.status} /> },
              { key: 'payload', label: t('cse_col_details'), render: (r) => <span className="mono">{JSON.stringify(r.payload).slice(0, 140)}</span> },
            ]}
            rows={caseRecords}
          />
        </Panel>
      </div>
    </main>
  );
}
