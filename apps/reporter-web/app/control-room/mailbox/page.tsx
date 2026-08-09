'use client';

import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';
import { Alert, Button, EmptyState, Field, Input, PageHeader, Panel, Textarea } from '@safelytold/ui/components';
import {
  listMailboxMessages,
  reporterSession,
  sendMailboxMessage,
  submitRetaliationConcern,
  type MailboxMessage,
} from '@safelytold/ui/api';
import { useI18n, useToast } from '@safelytold/ui/context';
import { formatDate } from '@safelytold/ui/hooks';
import { clearReporterCase, loadReporterCase, storeReporterCase } from '../../../lib/reporter';

export default function MailboxPage() {
  const { t } = useI18n();
  const { push } = useToast();
  const [connected, setConnected] = useState<{ caseId: string; publicCode: string } | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [code, setCode] = useState('');
  const [secret, setSecret] = useState('');
  const [opening, setOpening] = useState(false);
  const [openError, setOpenError] = useState<string | null>(null);
  const [messages, setMessages] = useState<MailboxMessage[]>([]);
  const [visibleCount, setVisibleCount] = useState(30);
  const [loading, setLoading] = useState(false);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const [concernOpen, setConcernOpen] = useState(false);
  const [concern, setConcern] = useState('');
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const stored = loadReporterCase();
    if (!stored) return;
    setConnected({ caseId: stored.caseId, publicCode: stored.publicCode });
    if (stored.token) setToken(stored.token);
  }, []);

  const loadMessages = useCallback(
    async (caseId: string, access: string) => {
      setLoading(true);
      try {
        const thread = await listMailboxMessages(caseId, access);
        setMessages(thread);
      } catch (err) {
        if (err instanceof Error && /401|403/.test(err.message)) {
          clearReporterCase();
          setConnected(null);
          setToken(null);
          setMessages([]);
          push(t('mb_toast_session_expired'), 'danger');
        } else {
          push(err instanceof Error ? err.message : t('mb_toast_load_failed'), 'danger');
        }
      } finally {
        setLoading(false);
      }
    },
    [push, t],
  );

  useEffect(() => {
    if (!connected || !token) return;
    setVisibleCount(30);
    loadMessages(connected.caseId, token);
    pollRef.current = setInterval(() => loadMessages(connected.caseId, token), 10000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [connected, token, loadMessages]);

  async function openMailbox(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setOpenError(null);
    if (!code.trim() || !secret.trim()) {
      setOpenError(t('mb_open_error_missing_codes'));
      return;
    }
    setOpening(true);
    try {
      const result = await reporterSession(code.trim(), secret.trim());
      storeReporterCase({
        caseId: result.case_id,
        publicCode: code.trim(),
        token: result.session,
        expiresAt: result.expires_at,
      });
      setConnected({ caseId: result.case_id, publicCode: code.trim() });
      setToken(result.session);
      setSecret('');
      push(t('mb_toast_opened'), 'ok');
    } catch (err) {
      setOpenError(err instanceof Error ? err.message : t('mb_open_error_failed'));
    } finally {
      setOpening(false);
    }
  }

  async function sendMessage() {
    if (!connected || !token || draft.trim().length === 0) return;
    setSending(true);
    try {
      await sendMailboxMessage(connected.caseId, draft.trim(), token);
      setDraft('');
      await loadMessages(connected.caseId, token);
      push(t('mb_toast_sent'), 'ok');
    } catch (err) {
      push(err instanceof Error ? err.message : t('mb_toast_send_failed'), 'danger');
    } finally {
      setSending(false);
    }
  }

  async function submitConcern() {
    if (!connected || !token || concern.trim().length === 0) return;
    try {
      await submitRetaliationConcern(connected.caseId, { risk_band: 'medium', details: concern.trim() }, token);
      setConcern('');
      setConcernOpen(false);
      push(t('mb_toast_concern_registered'), 'ok');
    } catch (err) {
      push(err instanceof Error ? err.message : t('mb_toast_concern_failed'), 'danger');
    }
  }

  if (!connected || !token) {
    return (
      <main className="shell">
        <PageHeader
          eyebrow={t('mb_eyebrow')}
          title={t('mb_open_title')}
          subtitle={t('mb_open_subtitle')}
        />
        <div className="split">
          <Panel title={t('mb_panel_open_codes')}>
            <form onSubmit={openMailbox}>
              <Field label={t('mb_field_case_code')} required>
                <Input value={code} onChange={(e) => setCode(e.target.value)} autoComplete="off" />
              </Field>
              <Field label={t('mb_field_secret')} required hint={t('mb_field_secret_hint')}>
                <Input type="password" value={secret} onChange={(e) => setSecret(e.target.value)} autoComplete="off" />
              </Field>
              {openError && <Alert tone="danger" title={t('mb_alert_unable_open')}>{openError}</Alert>}
              <Button type="submit" loading={opening} size="lg">{t('mb_open_button')}</Button>
            </form>
          </Panel>
          <Panel title={t('mb_panel_new_title')}>
            <p>
              {t('mb_new_body')}
            </p>
            <Button variant="secondary" onClick={() => (window.location.href = '/report')}>{t('mb_new_helpme')}</Button>
          </Panel>
        </div>
      </main>
    );
  }

  return (
    <main className="shell">
      <PageHeader
        eyebrow={t('mb_eyebrow')}
        title={t('mb_mailbox_title', { code: connected.publicCode })}
        subtitle={t('mb_subtitle')}
        actions={
          <Button variant="ghost" size="sm" onClick={() => { clearReporterCase(); setConnected(null); setToken(null); setMessages([]); }}>{t('mb_disconnect')}</Button>
        }
      />

      <div className="split">
        <Panel title={t('mb_conversation_title')} subtitle={loading ? t('mb_refreshing') : t('mb_conversation_subtitle')} padded={false}>
          <div style={{ padding: '16px 18px' }}>
            <div className="chat">
              {messages.length === 0 ? (
                <EmptyState title={t('mb_empty_title')} description={t('mb_empty_description')} />
              ) : (
                <>
                  {messages.length > visibleCount && (
                    <button type="button" className="btn btn-ghost btn-sm" onClick={() => setVisibleCount((v) => v + 30)}>
                      {t('mb_show_earlier', { count: messages.length - visibleCount })}
                    </button>
                  )}
                  {messages.slice(-visibleCount).map((m) => (
                    <div key={m.id} className={`bubble bubble-${m.sender === 'platform' ? 'in' : 'out'}`}>
                      {m.body}
                      <span className="bubble-meta">{m.sender === 'platform' ? t('mb_platform_team') : t('mb_you')} · {formatDate(m.created_at)}</span>
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>
          <div style={{ padding: '14px 18px', borderTop: '1px solid var(--line)' }}>
            <Field label={t('mb_field_reply')}>
              <Textarea rows={3} value={draft} onChange={(e) => setDraft(e.target.value)} placeholder={t('mb_reply_placeholder')} />
            </Field>
            <div className="row">
              <Button onClick={sendMessage} loading={sending} disabled={draft.trim().length === 0}>{t('mb_send_button')}</Button>
              <Button variant="secondary" onClick={() => setConcernOpen((v) => !v)}>{t('mb_report_concern_button')}</Button>
            </div>
          </div>
        </Panel>

        <div className="stack">
          {concernOpen && (
            <Panel title={t('mb_concern_title')}>
              <Alert tone="danger" title={t('mb_concern_alert_title')}>
                <p>{t('mb_concern_alert_body')}</p>
              </Alert>
              <Field label={t('mb_concern_field')}>
                <Textarea rows={4} value={concern} onChange={(e) => setConcern(e.target.value)} />
              </Field>
              <Button variant="danger" onClick={submitConcern} disabled={concern.trim().length === 0}>{t('mb_register_concern_button')}</Button>
            </Panel>
          )}
          <Panel title={t('mb_protection_support_title')}>
            <p>
              {t('mb_protection_support_body')}
            </p>
            <Button variant="secondary" onClick={() => (window.location.href = '/support')}>{t('mb_invite_support_button')}</Button>
          </Panel>
        </div>
      </div>
    </main>
  );
}
