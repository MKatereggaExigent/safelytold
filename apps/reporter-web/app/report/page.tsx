'use client';

import { Suspense, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import {
  Alert,
  Badge,
  Button,
  Checkbox,
  CodeBlock,
  Field,
  Input,
  PageHeader,
  Panel,
  RadioCard,
  Select,
  Stepper,
  Textarea,
} from '@safelytold/ui/components';
import { createRecord, createReporterHandle, storeVaultIdentity, runAi, type AiRunResult } from '@safelytold/ui/api';
import { useI18n, useToast } from '@safelytold/ui/context';
import { encryptString, generateRandomKey, exportKeyBase64 } from '@safelytold/ui/crypto';
import {
  IMPACT_CATEGORIES,
  JURISDICTIONS,
  REPORT_MODES,
  TAXONOMY,
  storeReporterCase,
} from '../../lib/reporter';

function detectPii(text: string) {
  const emails = text.match(/[\w.+-]+@[\w-]+\.[\w.]+/g) ?? [];
  const phones = text.match(/(?<!\d)(?:\+?\d[\d\s()-]{6,}\d)(?!\d)/g) ?? [];
  return { emails: [...new Set(emails)], phones: [...new Set(phones)] };
}

function ReportPageInner() {
  const searchParams = useSearchParams();
  const initialMode = (searchParams.get('mode') as 'anonymous' | 'confidential' | 'identified') ?? 'anonymous';
  const { push } = useToast();
  const { t } = useI18n();

  const steps = [t('rpt_step_mode'), t('rpt_step_details'), t('rpt_step_narrative'), t('rpt_step_review'), t('rpt_step_receipt')];

  const [step, setStep] = useState(0);
  const [mode, setMode] = useState(initialMode);
  const [category, setCategory] = useState('');
  const [jurisdiction, setJurisdiction] = useState('ZA');
  const [immediateRisk, setImmediateRisk] = useState(false);
  const [preservation, setPreservation] = useState(false);
  const [dates, setDates] = useState('');
  const [locations, setLocations] = useState('');
  const [witnesses, setWitnesses] = useState('');
  const [impacts, setImpacts] = useState<string[]>([]);
  const [contactName, setContactName] = useState('');
  const [contactInfo, setContactInfo] = useState('');
  const [narrative, setNarrative] = useState('');
  const [saveToJournal, setSaveToJournal] = useState(false);
  const [receipt, setReceipt] = useState<{ caseId: string; code: string; secret: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scan, setScan] = useState<AiRunResult | null>(null);
  const [scanning, setScanning] = useState(false);
  const scanTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [legalQuestion, setLegalQuestion] = useState('');
  const [legalAnswer, setLegalAnswer] = useState<string | null>(null);
  const [legalCitations, setLegalCitations] = useState<Array<{ citation: string; excerpt: string }>>([]);
  const [legalLoading, setLegalLoading] = useState(false);
  const [legalError, setLegalError] = useState<string | null>(null);

  const pii = useMemo(() => detectPii(narrative), [narrative]);

  function onNarrativeChange(value: string) {
    setNarrative(value);
    if (scanTimer.current) clearTimeout(scanTimer.current);
    if (value.trim().length < 30) {
      setScan(null);
      return;
    }
    setScanning(true);
    scanTimer.current = setTimeout(async () => {
      try {
        const result = await runAi(
          { capability: 'anonymity_scan', purpose: 'reporter-anonymity-scan', redacted_input: value.slice(0, 50000) },
          null,
        );
        setScan(result);
      } catch {
        setScan(null);
      } finally {
        setScanning(false);
      }
    }, 700);
  }

  async function submit() {
    setError(null);
    if (!category || narrative.trim().length < 20) {
      setError(t('rpt_err_choose_category'));
      return;
    }
    setSubmitting(true);
    try {
      const journalCopied = saveToJournal ? await copyToJournal(narrative) : false;
      const encryptedRef = await sealNarrative(narrative);
      const questionnaire = {
        approximate_dates: dates,
        locations,
        witness_refs: witnesses.split(',').map((w) => w.trim()).filter(Boolean),
        impact_categories: impacts,
        preservation_requests: preservation ? ['preserve_related_materials'] : [],
        created_at: new Date().toISOString(),
      };
      const record = await createRecord(
        'intake',
        'report',
        {
          mode,
          jurisdiction_code: jurisdiction,
          taxonomy_codes: [category],
          immediate_risk: immediateRisk,
          encrypted_narrative_ref: encryptedRef.sealed,
          narrative,
          development_readable_copy: true,
          questionnaire,
          contact_vaulted: mode !== 'anonymous' && Boolean(contactName || contactInfo),
          saved_to_journal: journalCopied,
          created_at: new Date().toISOString(),
        },
        null,
      );

      const handle = await createReporterHandle(record.id);
      const caseId = record.id;
      if (mode !== 'anonymous' && (contactName || contactInfo)) {
        try {
          await storeVaultIdentity(caseId, { name: contactName, contact: contactInfo, stored_at: new Date().toISOString() });
        } catch {
          // 409 already stored is harmless; other failures do not block the receipt.
        }
      }
      localStorage.setItem(
        `wpc:reporter:narrative:${caseId}`,
        JSON.stringify({ sealed: encryptedRef.sealed, key: encryptedRef.key }),
      );
      storeReporterCase({ caseId, publicCode: handle.public_code });
      setReceipt({ caseId, code: handle.public_code, secret: handle.recovery_secret });
      setStep(4);
      push(t('rpt_report_created'), 'ok');
    } catch (err) {
      setError(err instanceof Error ? err.message : t('rpt_err_submit_failed'));
    } finally {
      setSubmitting(false);
    }
  }

  async function copyToJournal(text: string): Promise<boolean> {
    try {
      const key = await generateRandomKey();
      const sealed = await encryptString(key, text);
      const journal = JSON.parse(localStorage.getItem('wpc:journal') ?? '[]') as { id: string; sealed: string; key: string; created_at: string }[];
      journal.push({ id: crypto.randomUUID(), sealed, key: await exportKeyBase64(key), created_at: new Date().toISOString() });
      localStorage.setItem('wpc:journal', JSON.stringify(journal));
      return true;
    } catch {
      return false;
    }
  }

  const canContinue =
    step === 0 || (step === 1 && category && jurisdiction) || (step === 2 && narrative.trim().length >= 20);

  const quickExit = () => {
    try {
      Object.keys(localStorage)
        .filter((key) => key.startsWith('wpc:'))
        .forEach((key) => localStorage.removeItem(key));
    } catch {
      /* noop */
    }
    window.location.href = 'https://weather.com/';
  };

  async function fetchLegalGuidance() {
    setLegalError(null);
    setLegalAnswer(null);
    setLegalCitations([]);
    if (legalQuestion.trim().length < 30) {
      setLegalError(t('rpt_err_legal_detail'));
      return;
    }
    setLegalLoading(true);
    try {
      const response = await fetch('/api/legal-assist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jurisdiction, issue: legalQuestion, mode }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error ?? t('rpt_ai_unavailable'));
      }
      const data = await response.json();
      setLegalAnswer(data.summary ?? t('rpt_no_summary'));
      setLegalCitations(data.references ?? []);
    } catch (err) {
      setLegalError(err instanceof Error ? err.message : t('rpt_ai_unavailable'));
    } finally {
      setLegalLoading(false);
    }
  }

  return (
    <main className="shell">
      <PageHeader
        eyebrow={t('rpt_eyebrow')}
        title={t('rpt_page_title')}
        subtitle={t('rpt_page_subtitle')}
        actions={<Button variant="danger" size="sm" onClick={quickExit}>{t('rpt_quick_exit')}</Button>}
      />
      <Stepper steps={steps} current={step} />

      <Alert tone="danger" title={t('rpt_device_alert_title')}>
        <p>
          {t('rpt_device_alert_body')}
        </p>
      </Alert>
      <Panel title={t('rpt_safety_tips_title')} subtitle={t('rpt_safety_tips_subtitle')}>
        <ul>
          <li>{t('rpt_tip_1')}</li>
          <li>{t('rpt_tip_2')}</li>
          <li>{t('rpt_tip_3')}</li>
          <li>{t('rpt_tip_4')}</li>
        </ul>
      </Panel>

      {error && <Alert tone="danger" title={t('rpt_error_title')}>{error}</Alert>}

      {step === 0 && (
        <div className="stack">
          <p className="muted"><strong>{t('rpt_step_1_of_4')}</strong> {t('rpt_how_raise_concern')}</p>
          {REPORT_MODES.map((m) => (
            <RadioCard
              key={m.value}
              value={m.value}
              selected={mode === m.value}
              onSelect={(value) => setMode(value as 'anonymous' | 'confidential' | 'identified')}
              title={t(m.key)}
              badge={<Badge tone="accent">{t(m.value === 'anonymous' ? 'mode_anon_badge' : m.value === 'confidential' ? 'mode_conf_badge' : 'mode_iden_badge')}</Badge>}
              description={t(m.value === 'anonymous' ? 'mode_anon_desc' : m.value === 'confidential' ? 'mode_conf_desc' : 'mode_iden_desc')}
            />
          ))}
          <div className="row">
            <Button variant="secondary" onClick={() => setStep(1)} disabled={!canContinue}>{t('rpt_continue')}</Button>
          </div>
        </div>
      )}

      {step === 1 && (
        <Panel title={t('rpt_details_title')} subtitle={t('rpt_details_subtitle')}>
          <div className="grid">
            <Field label={t('rpt_category')} required>
              <Select value={category} onChange={(e) => setCategory(e.target.value)} placeholder={t('rpt_select_category')}>
                {TAXONOMY.map((item) => <option key={item.value} value={item.value}>{t(item.key)}</option>)}
              </Select>
            </Field>
            <Field label={t('rpt_jurisdiction')} hint={t('rpt_jurisdiction_hint')}>
              <Select value={jurisdiction} onChange={(e) => setJurisdiction(e.target.value)} options={JURISDICTIONS.map((j) => ({ ...j, label: t(j.key) }))} />
            </Field>
          </div>
          <div className="grid">
            <Field label={t('rpt_approx_dates')} hint={t('rpt_approx_dates_hint')}>
              <Input value={dates} onChange={(e) => setDates(e.target.value)} placeholder={t('rpt_dates_placeholder')} autoComplete="off" />
            </Field>
            <Field label={t('rpt_locations')}>
              <Input value={locations} onChange={(e) => setLocations(e.target.value)} placeholder={t('rpt_locations_placeholder')} autoComplete="off" />
            </Field>
          </div>
          <Field label={t('rpt_witnesses')} hint={t('rpt_witnesses_hint')}>
            <Input value={witnesses} onChange={(e) => setWitnesses(e.target.value)} placeholder={t('rpt_witnesses_placeholder')} autoComplete="off" />
          </Field>
          <Field label={t('rpt_impact_categories')}>
            <div className="stack">
              {IMPACT_CATEGORIES.map((c) => (
                <Checkbox
                  key={c.value}
                  checked={impacts.includes(c.value)}
                  onChange={(e) => setImpacts(e.target.checked ? [...impacts, c.value] : impacts.filter((v) => v !== c.value))}
                  label={t(c.key)}
                />
              ))}
            </div>
          </Field>
          <div className="stack">
            <Checkbox checked={immediateRisk} onChange={(e) => setImmediateRisk(e.target.checked)} label={t('rpt_urgent_protection')} />
            <Checkbox checked={preservation} onChange={(e) => setPreservation(e.target.checked)} label={t('rpt_preserve_materials')} />
          </div>
          {mode !== 'anonymous' && (
            <Panel title={t('rpt_contact_details_title')} subtitle={t('rpt_contact_details_subtitle')}>
              <div className="grid">
                <Field label={t('rpt_name')}>
                  <Input value={contactName} onChange={(e) => setContactName(e.target.value)} autoComplete="off" />
                </Field>
                <Field label={t('rpt_contact_info')}>
                  <Input value={contactInfo} onChange={(e) => setContactInfo(e.target.value)} autoComplete="off" />
                </Field>
              </div>
            </Panel>
          )}
          <div className="row between">
            <Button variant="secondary" onClick={() => setStep(0)}>{t('rpt_back')}</Button>
            <Button onClick={() => setStep(2)} disabled={!canContinue}>{t('rpt_continue')}</Button>
          </div>
          <Panel title={t('rpt_rights_title')} subtitle={t('rpt_rights_subtitle')}>
            <Field label={t('rpt_question_for', { jurisdiction })}>
              <Textarea
                rows={4}
                value={legalQuestion}
                onChange={(e) => setLegalQuestion(e.target.value)}
                placeholder={t('rpt_legal_placeholder')}
              />
            </Field>
            <div className="row" style={{ gap: 8 }}>
              <Button onClick={fetchLegalGuidance} loading={legalLoading} disabled={legalQuestion.trim().length < 30}>{t('rpt_get_guidance')}</Button>
              {legalAnswer && <Button variant="ghost" onClick={() => { setLegalAnswer(null); setLegalCitations([]); }}>{t('rpt_clear')}</Button>}
            </div>
            {legalError && <Alert tone="danger" title={t('rpt_ai_assistant')}>{legalError}</Alert>}
            {legalAnswer && (
              <div className="stack" style={{ marginTop: 12 }}>
                <Alert tone="info" title={t('rpt_summary')}>
                  <p>{legalAnswer}</p>
                </Alert>
                {legalCitations.length > 0 && (
                  <Panel title={t('rpt_references')}>
                    <ul>
                      {legalCitations.map((ref) => (
                        <li key={`${ref.citation}-${ref.excerpt.slice(0, 24)}`}>
                          <strong>{ref.citation}</strong> – {ref.excerpt}
                        </li>
                      ))}
                    </ul>
                  </Panel>
                )}
              </div>
            )}
            <Alert tone="warn" title={t('rpt_not_legal_advice')}>
              <p>
                {t('rpt_not_legal_advice_body')}
              </p>
            </Alert>
          </Panel>
        </Panel>
      )}

      {step === 2 && (
        <Panel title={t('rpt_events_title')} subtitle={t('rpt_events_subtitle')}>
          <Field label={t('rpt_your_account')} required hint={t('rpt_your_account_hint')}>
            <Textarea
              rows={12}
              value={narrative}
              onChange={(e) => onNarrativeChange(e.target.value)}
              placeholder={t('rpt_narrative_placeholder')}
            />
          </Field>

          {pii.emails.length > 0 || pii.phones.length > 0 ? (
            <Alert tone="warn" title={t('rpt_pii_alert_title')}>
              <p>
                {pii.emails.length > 0 && <>{t('rpt_email_addresses')}: {pii.emails.join(', ')}. </>}
                {pii.phones.length > 0 && <>{t('rpt_phone_numbers')}: {pii.phones.join(', ')}. </>}
                {t('rpt_pii_advice')}
              </p>
            </Alert>
          ) : null}

          {scanning && <p className="muted" role="status">{t('rpt_reviewing')}</p>}
          {scan && (
            <Alert tone="info" title={t('rpt_scan_title', { status: scan.status, uncertainty: scan.uncertainty })}>
              <p>{scan.output}</p>
              <p className="muted" style={{ fontSize: '0.8rem' }}>{t('rpt_scan_advice')}</p>
            </Alert>
          )}

          <Checkbox
            checked={saveToJournal}
            onChange={(e) => setSaveToJournal(e.target.checked)}
            label={t('rpt_save_journal_copy')}
            hint={t('rpt_save_journal_hint')}
          />

          <div className="row between">
            <Button variant="secondary" onClick={() => setStep(1)}>{t('rpt_back')}</Button>
            <Button onClick={() => setStep(3)} disabled={!canContinue}>{t('rpt_review_report')}</Button>
          </div>
        </Panel>
      )}

      {step === 3 && (
        <Panel title={t('rpt_review_submit_title')} subtitle={t('rpt_review_submit_subtitle')}>
          <Alert tone="info" title={t('rpt_what_happens')}>
            <p>
              {t('rpt_what_happens_mode')} <strong>{t(REPORT_MODES.find((m) => m.value === mode)?.key ?? '')}</strong>{t('rpt_what_happens_body')}
            </p>
          </Alert>
          <CodeBlock title={t('rpt_payload_preview')} text={JSON.stringify({
            mode,
            jurisdiction_code: jurisdiction,
            taxonomy_codes: [category],
            immediate_risk: immediateRisk,
            questionnaire: { dates, locations, witnesses: witnesses.split(',').map((w) => w.trim()).filter(Boolean), impacts, preservation_requests: preservation ? ['preserve_related_materials'] : [] },
            narrative_length: narrative.length,
          }, null, 2)} />
          <Panel title={t(TAXONOMY.find((item) => item.value === category)?.key ?? 'rpt_uncategorised')}>
            <p style={{ whiteSpace: 'pre-wrap' }}>{narrative}</p>
          </Panel>
          <div className="row between">
            <Button variant="secondary" onClick={() => setStep(2)}>{t('rpt_back')}</Button>
            <Button onClick={submit} loading={submitting}>{t('rpt_create_report')}</Button>
          </div>
        </Panel>
      )}

      {step === 4 && receipt && (
        <Panel title={t('rpt_report_created_title')}>
          <Alert tone="ok" title={t('rpt_codes_safe')}>
            <p>{t('rpt_codes_shown_once')}</p>
          </Alert>
          <div className="receipt">
            <p className="muted" style={{ margin: 0 }}>{t('rpt_case_code')}</p>
            <p className="receipt-code">{receipt.code}</p>
            <p className="muted" style={{ margin: '16px 0 0' }}>{t('rpt_recovery_secret')}</p>
            <p className="receipt-code">{receipt.secret}</p>
            <div className="row" style={{ marginTop: 14 }}>
              <Button variant="secondary" size="sm" onClick={() => navigator.clipboard?.writeText(receipt.code).catch(() => undefined)}>{t('rpt_copy_code')}</Button>
              <Button variant="secondary" size="sm" onClick={() => navigator.clipboard?.writeText(receipt.secret).catch(() => undefined)}>{t('rpt_copy_secret')}</Button>
            </div>
          </div>
          <div className="row">
            <Link href="/control-room/mailbox"><Button>{t('rpt_open_mailbox')}</Button></Link>
            <Link href="/control-room/case"><Button variant="secondary">{t('rpt_track_case')}</Button></Link>
            <Link href="/"><Button variant="ghost">{t('rpt_back_home')}</Button></Link>
          </div>
        </Panel>
      )}
    </main>
  );
}

export default function ReportPage() {
  const { t } = useI18n();
  return (
    <Suspense fallback={<main className="shell"><p className="muted">{t('rpt_loading')}</p></main>}>
      <ReportPageInner />
    </Suspense>
  );
}

async function sealNarrative(text: string): Promise<{ sealed: string; key: string }> {
  const key = await generateRandomKey();
  const sealed = await encryptString(key, text);
  return { sealed, key: await exportKeyBase64(key) };
}
