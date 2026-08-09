'use client';

import { useCallback, useEffect, useState } from 'react';
import { Alert, Button, Checkbox, EmptyState, Field, Input, Modal, PageHeader, Panel, Pagination, Textarea } from '@safelytold/ui/components';
import { decryptString, encryptString, loadOrCreateVaultKey } from '@safelytold/ui/crypto';
import { useI18n, useToast } from '@safelytold/ui/context';
import { formatDate, usePagination } from '@safelytold/ui/hooks';

interface JournalEntry {
  id: string;
  title: string;
  sealed: string;
  created_at: string;
  updated_at?: string;
}

const KEY_NAME = 'journal';
const STORAGE_KEY = 'wpc:journal';
const STORAGE_PREF_KEY = 'wpc:journal:persist';

function loadEntries(): JournalEntry[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '[]') as JournalEntry[];
  } catch {
    return [];
  }
}

export default function JournalPage() {
  const { t } = useI18n();
  const { push } = useToast();
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [busy, setBusy] = useState(true);
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [viewing, setViewing] = useState<JournalEntry | null>(null);
  const [plain, setPlain] = useState('');
  const [decrypting, setDecrypting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [persistJournal, setPersistJournal] = useState(true);

  const refresh = useCallback(() => setEntries(loadEntries().sort((a, b) => b.created_at.localeCompare(a.created_at))), []);
  useEffect(() => {
    refresh();
    setBusy(false);
  }, [refresh]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const stored = localStorage.getItem(STORAGE_PREF_KEY);
    if (stored !== null) setPersistJournal(stored === 'true');
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    localStorage.setItem(STORAGE_PREF_KEY, String(persistJournal));
    if (!persistJournal) {
      localStorage.removeItem(STORAGE_KEY);
      setEntries([]);
    } else {
      refresh();
    }
  }, [persistJournal, refresh]);
  const { pageItems, ...pagination } = usePagination<JournalEntry>(entries);

  async function saveEntry() {
    if (!persistJournal) {
      push(t('cr_toast_storage_disabled'), 'warn');
      return;
    }
    if (!title.trim() || !body.trim()) {
      push(t('cr_toast_add_notes'), 'warn');
      return;
    }
    setSaving(true);
    try {
      const key = await loadOrCreateVaultKey(KEY_NAME);
      const sealed = await encryptString(key, body);
      const now = new Date().toISOString();
      const all = loadEntries();
      const existing = all.find((e) => e.id === viewing?.id);
      if (existing) {
        existing.sealed = sealed;
        existing.title = title.trim();
        existing.updated_at = now;
      } else {
        all.push({ id: crypto.randomUUID(), title: title.trim(), sealed, created_at: now });
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(all));
      refresh();
      setTitle('');
      setBody('');
      setViewing(null);
      setPlain('');
      push(existing ? t('cr_toast_entry_updated') : t('cr_toast_entry_saved'), 'ok');
    } catch (err) {
      push(err instanceof Error ? err.message : t('cr_toast_save_failed'), 'danger');
    } finally {
      setSaving(false);
    }
  }

  async function openEntry(entry: JournalEntry) {
    setViewing(entry);
    setDecrypting(true);
    setPlain('');
    try {
      const key = await loadOrCreateVaultKey(KEY_NAME);
      const decrypted = await decryptString(key, entry.sealed);
      setPlain(decrypted);
    } catch {
      setPlain('__error__');
    } finally {
      setDecrypting(false);
    }
  }

  function deleteEntry(id: string) {
    const all = loadEntries().filter((e) => e.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(all));
    refresh();
    setViewing(null);
    setPlain('');
    push(t('cr_toast_entry_removed'), 'info');
  }

  const quickExit = () => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* noop */
    }
    window.location.href = 'https://weather.com/';
  };

  return (
    <main className="shell">
      <PageHeader
        eyebrow={t('cr_eyebrow')}
        title={t('cr_title')}
        subtitle={t('cr_subtitle')}
        actions={(
          <div className="row" style={{ gap: 8 }}>
            <Button variant="danger" size="sm" onClick={quickExit}>{t('cr_quick_exit')}</Button>
            <Button variant="secondary" onClick={() => { setTitle(''); setBody(''); setViewing(null); setPlain(''); }}>{t('cr_new_entry')}</Button>
          </div>
        )}
      />

      <Alert tone="danger" title={t('cr_alert_company_device')}>
        <p>
          {t('cr_alert_company_device_body')}
        </p>
      </Alert>
      <Alert tone="warn" title={t('cr_alert_device_risks')}>
        <p>
          {t('cr_alert_device_risks_body')}
        </p>
      </Alert>
      <Panel title={t('cr_safety_tips')}>
        <ul>
          <li>{t('cr_tip_1')}</li>
          <li>{t('cr_tip_2')}</li>
          <li>{t('cr_tip_3')}</li>
          <li>{t('cr_tip_4')}</li>
        </ul>
      </Panel>

      <div className="split">
        <div className="stack">
          <Panel title={viewing ? t('cr_edit_entry') : t('cr_new_entry')}>
            <div style={{ marginBottom: 12 }}>
              <Alert tone="info" title={t('cr_storage_preference')}>
                <Checkbox
                  checked={persistJournal}
                  onChange={(e) => setPersistJournal(e.target.checked)}
                  label={t('cr_storage_allow_label')}
                />
                <p className="muted" style={{ marginTop: 6 }}>
                  {t('cr_storage_disable_hint')}
                </p>
              </Alert>
            </div>
            <Field label={t('cr_field_title')} required>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} autoComplete="off" />
            </Field>
            <Field label={t('cr_field_notes')} required>
              <Textarea rows={10} value={body} onChange={(e) => setBody(e.target.value)} placeholder={t('cr_notes_placeholder')} />
            </Field>
            <div className="row">
              <Button onClick={saveEntry} loading={saving}>{viewing ? t('cr_save_changes') : t('cr_save_encrypted')}</Button>
              <Button variant="ghost" onClick={() => { setTitle(''); setBody(''); setViewing(null); setPlain(''); }}>{t('cr_clear')}</Button>
            </div>
          </Panel>
        </div>

        <div className="stack">
          {busy ? (
            <p className="muted">{t('cr_loading')}</p>
          ) : entries.length === 0 ? (
            <EmptyState title={t('cr_empty_title')} description={t('cr_empty_description')} />
          ) : (
            <>
              {pageItems.map((entry) => (
                <Panel key={entry.id} title={entry.title}>
                  <p className="muted" style={{ margin: 0 }}>{t('cr_created', { date: formatDate(entry.created_at) })}{entry.updated_at ? t('cr_updated', { date: formatDate(entry.updated_at) }) : ''}</p>
                  <div className="row" style={{ marginTop: 10 }}>
                    <Button variant="secondary" size="sm" onClick={() => openEntry(entry)}>{t('cr_view')}</Button>
                    <Button variant="ghost" size="sm" onClick={() => { setTitle(entry.title); setViewing(entry); setBody(''); }}>{t('cr_edit')}</Button>
                  </div>
                </Panel>
              ))}
              <Pagination {...pagination} />
            </>
          )}
        </div>
      </div>

      <Modal
        open={viewing !== null && plain !== ''}
        onClose={() => { setViewing(null); setPlain(''); }}
        title={viewing?.title ?? t('cr_entry')}
        footer={
          <div className="row">
            <Button variant="secondary" size="sm" onClick={() => deleteEntry(viewing!.id)}>{t('cr_delete_entry')}</Button>
            <Button variant="ghost" size="sm" onClick={() => { setTitle(viewing!.title); setViewing(null); setPlain(''); }}>{t('cr_close')}</Button>
          </div>
        }
      >
        {decrypting ? <p className="muted">{t('cr_decrypting')}</p> : plain === '__error__' ? (
          <Alert tone="danger" title={t('cr_decrypt_error_title')}>{t('cr_decrypt_error_body')}</Alert>
        ) : (
          <p style={{ whiteSpace: 'pre-wrap' }}>{plain}</p>
        )}
      </Modal>
    </main>
  );
}
