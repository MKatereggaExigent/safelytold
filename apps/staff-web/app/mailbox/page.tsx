'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, Badge, Button, EmptyState, Field, PageHeader, Panel, StatusPill, Textarea } from '@safelytold/ui/components';
import {
  listMailboxChallenges,
  listMailboxConcerns,
  listMailboxThread,
  replyMailboxMessage,
  type MailboxMessage,
} from '@safelytold/ui/api';
import { useI18n, useSession, useToast } from '@safelytold/ui/context';
import { formatDate, useRecords } from '@safelytold/ui/hooks';
import { CASE_STATUS_LABELS, latestCaseRecords, summarizeCase } from '../../lib/staff';

export default function MailboxRoomPage() {
  const { t } = useI18n();
  const { session } = useSession();
  const { push } = useToast();
  const { records: caseRecords } = useRecords('case');

  const cases = useMemo(() => latestCaseRecords(caseRecords).map(summarizeCase), [caseRecords]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MailboxMessage[]>([]);
  const [concerns, setConcerns] = useState<{ id: string; risk_band: string; details: string; status: string; created_at: string }[]>([]);
  const [challenges, setChallenges] = useState<{ id: string; reason_category: string; details: string; status: string; created_at: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (!activeId) return;
    if (!cases.some((c) => c.id === activeId)) {
      setActiveId(cases[0]?.id ?? null);
    }
  }, [cases, activeId]);

  const loadThread = useCallback(
    async (caseId: string) => {
      setLoading(true);
      setError(null);
      try {
        const [thread, concernList, challengeList] = await Promise.all([
          listMailboxThread(caseId, session),
          listMailboxConcerns(caseId, session),
          listMailboxChallenges(caseId, session),
        ]);
        setMessages(thread);
        setConcerns(concernList);
        setChallenges(challengeList);
      } catch (err) {
        setError(err instanceof Error ? err.message : t('mbx_load_failed'));
      } finally {
        setLoading(false);
      }
    },
    [session, t],
  );

  useEffect(() => {
    if (activeId) loadThread(activeId);
  }, [activeId, loadThread]);

  async function sendReply() {
    if (!activeId || draft.trim().length === 0) return;
    setSending(true);
    try {
      await replyMailboxMessage(activeId, draft.trim(), session);
      setDraft('');
      await loadThread(activeId);
      push(t('mbx_sent_ok'), 'ok');
    } catch (err) {
      push(err instanceof Error ? err.message : t('mbx_send_failed'), 'danger');
    } finally {
      setSending(false);
    }
  }

  const activeCase = cases.find((c) => c.id === activeId);

  return (
    <main className="shell">
      <PageHeader eyebrow={t('mbx_eyebrow')} title={t('mbx_title')} subtitle={t('mbx_subtitle')} />

      <div className="split">
        <Panel title={t('mbx_case_label')} subtitle={`${cases.length} open`} padded={false}>
          {cases.length === 0 ? (
            <div className="panel-body">
              <EmptyState title={t('mbx_no_cases')} description={t('mbx_loading')} />
            </div>
          ) : (
            <ul className="plain-list" style={{ maxHeight: 520, overflowY: 'auto' }}>
              {cases.map((c) => (
                <li key={c.id}>
                  <button
                    type="button"
                    className={`staff-nav-link${activeId === c.id ? ' staff-nav-active' : ''}`}
                    onClick={() => setActiveId(c.id)}
                    style={{ width: '100%', textAlign: 'left', borderRadius: 8 }}
                  >
                    <span className="mono">{c.id.slice(0, 12)}…</span>
                    <span className="muted" style={{ display: 'block', fontSize: '0.8rem' }}>
                      {c.mode} · {CASE_STATUS_LABELS[c.status] ?? c.status}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <div className="stack" style={{ flex: 1 }}>
          {!activeId ? (
            <Panel title={t('mbx_thread_title')}>
              <EmptyState title={t('mbx_no_cases')} description={t('mbx_subtitle')} />
            </Panel>
          ) : (
            <>
              <Panel
                title={t('mbx_thread_title')}
                subtitle={loading ? t('mbx_loading') : `${activeCase?.mode ?? ''} · ${messages.length} message${messages.length === 1 ? '' : 's'}`}
                padded={false}
              >
                {error && <div className="panel-body"><Alert tone="danger" title="Load failed">{error}</Alert></div>}
                <div style={{ padding: '16px 18px', minHeight: 240 }}>
                  <div className="chat">
                    {!loading && messages.length === 0 ? (
                      <EmptyState title={t('mbx_thread_empty')} description={t('mbx_subtitle')} />
                    ) : (
                      messages.map((m) => (
                        <div key={m.id} className={`bubble bubble-${m.sender === 'reporter' ? 'in' : 'out'}`}>
                          {m.body}
                          <span className="bubble-meta">
                            {m.sender === 'reporter' ? t('mbx_reporter') : t('mbx_you')} · {formatDate(m.created_at)}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
                <div style={{ padding: '14px 18px', borderTop: '1px solid var(--line)' }}>
                  <Field label={t('mbx_reply_label')}>
                    <Textarea rows={3} value={draft} onChange={(e) => setDraft(e.target.value)} placeholder={t('mbx_reply_placeholder')} />
                  </Field>
                  <Button onClick={sendReply} loading={sending} disabled={draft.trim().length === 0}>{t('mbx_send')}</Button>
                </div>
              </Panel>

              <div className="grid">
                <Panel title={t('mbx_concerns_title')} padded={false}>
                  {concerns.length === 0 ? (
                    <div className="panel-body"><EmptyState title={t('mbx_concerns_empty')} /></div>
                  ) : (
                    <ul className="plain-list">
                      {concerns.map((c) => (
                        <li key={c.id} className="panel-body" style={{ borderTop: '1px solid var(--line)' }}>
                          <div className="row" style={{ justifyContent: 'space-between' }}>
                            <StatusPill status={c.status} label={c.risk_band} />
                            <span className="muted">{formatDate(c.created_at)}</span>
                          </div>
                          <p className="muted" style={{ margin: '6px 0 0' }}>{c.details}</p>
                        </li>
                      ))}
                    </ul>
                  )}
                </Panel>

                <Panel title={t('mbx_challenges_title')} padded={false}>
                  {challenges.length === 0 ? (
                    <div className="panel-body"><EmptyState title={t('mbx_challenges_empty')} /></div>
                  ) : (
                    <ul className="plain-list">
                      {challenges.map((c) => (
                        <li key={c.id} className="panel-body" style={{ borderTop: '1px solid var(--line)' }}>
                          <Badge tone="warn">{c.reason_category}</Badge>
                          <p className="muted" style={{ margin: '6px 0 0' }}>{c.details}</p>
                          <span className="muted">{formatDate(c.created_at)}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </Panel>
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
