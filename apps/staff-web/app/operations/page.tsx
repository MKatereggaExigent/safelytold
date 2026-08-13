'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, Badge, Button, Field, PageHeader, Panel, Select, Textarea } from '@safelytold/ui/components';
import {
  createOperationalRecord,
  getCoverageStatus,
  listOperationalRecords,
  transitionOperationalRecord,
  type OperationalRecordView,
  type OperationsArea,
} from '@safelytold/ui/api';
import { useI18n, useSession, useToast } from '@safelytold/ui/context';
import { formatDate } from '@safelytold/ui/hooks';

const AREAS: OperationsArea[] = ['awareness', 'training', 'qa', 'continuity', 'coverage', 'hotline', 'reporting'];
const EXAMPLES: Record<OperationsArea, Record<string, unknown>> = {
  awareness: { title: 'Speak up safely', version: '1.0', languages: ['en', 'af', 'zu'] },
  training: { learner_subject: 'staff-id', course: 'case-handler', due_at: new Date().toISOString() },
  qa: { sample_period: new Date().toISOString().slice(0, 7), sample_size: 10, critical_defects: 0 },
  continuity: { scenario: 'primary-region-loss', target_rto_minutes: 240, target_rpo_minutes: 15 },
  coverage: { shift_start: new Date().toISOString(), shift_end: new Date(Date.now() + 8 * 3600000).toISOString() },
  hotline: { provider_call_id: 'provider-reference', reporting_mode: 'anonymous', language: 'en', started_at: new Date().toISOString() },
  reporting: { cadence: 'monthly', period_start: new Date().toISOString().slice(0, 10), period_end: new Date().toISOString().slice(0, 10) },
};
const NEXT: Record<OperationsArea, Record<string, string[]>> = {
  awareness: { draft: ['approved'], approved: ['published'], published: ['retired'] },
  training: { assigned: ['in_progress', 'passed', 'failed'], in_progress: ['passed', 'failed'], failed: ['in_progress'] },
  qa: { open: ['approved', 'blocked'], blocked: ['open'] },
  continuity: { planned: ['passed', 'failed'], failed: ['planned'] },
  coverage: { planned: ['active', 'cancelled'], active: ['completed', 'cancelled'] },
  hotline: { received: ['submitted', 'escalated'], submitted: ['closed', 'escalated'], escalated: ['closed'] },
  reporting: { scheduled: ['generated'], generated: ['approved'], approved: ['distributed'] },
};

function objectFrom(text: string): Record<string, unknown> {
  const value: unknown = JSON.parse(text);
  if (!value || Array.isArray(value) || typeof value !== 'object') throw new Error('object required');
  return value as Record<string, unknown>;
}

export default function OperationsPage() {
  const { t } = useI18n();
  const { session } = useSession();
  const { push } = useToast();
  const [area, setArea] = useState<OperationsArea>('awareness');
  const [records, setRecords] = useState<OperationalRecordView[]>([]);
  const [payload, setPayload] = useState(JSON.stringify(EXAMPLES.awareness, null, 2));
  const [evidence, setEvidence] = useState('{}');
  const [target, setTarget] = useState('');
  const [selected, setSelected] = useState<string>('');
  const [busy, setBusy] = useState(false);
  const [covered, setCovered] = useState(false);

  const load = useCallback(async () => {
    const [items, coverage] = await Promise.all([listOperationalRecords(session, area), getCoverageStatus(session)]);
    setRecords(items); setCovered(coverage.covered);
  }, [area, session]);

  useEffect(() => { load().catch(() => undefined); }, [load]);
  useEffect(() => {
    setPayload(JSON.stringify(EXAMPLES[area], null, 2)); setSelected(''); setTarget(''); setEvidence('{}');
  }, [area]);

  const active = useMemo(() => records.find((record) => record.id === selected), [records, selected]);
  const targets = active ? (NEXT[active.area][active.status] ?? []) : [];

  async function create() {
    let parsed: Record<string, unknown>;
    try { parsed = objectFrom(payload); } catch { push(t('ops_invalid_json'), 'danger'); return; }
    setBusy(true);
    try { await createOperationalRecord(session, area, parsed); await load(); push(t('ops_saved'), 'ok'); }
    catch (error) { push(error instanceof Error ? error.message : t('ops_failed'), 'danger'); }
    finally { setBusy(false); }
  }

  async function transition() {
    if (!active || !target) return;
    let parsed: Record<string, unknown>;
    try { parsed = objectFrom(evidence); } catch { push(t('ops_invalid_json'), 'danger'); return; }
    setBusy(true);
    try { await transitionOperationalRecord(session, active.id, target, parsed); await load(); setTarget(''); push(t('ops_saved'), 'ok'); }
    catch (error) { push(error instanceof Error ? error.message : t('ops_failed'), 'danger'); }
    finally { setBusy(false); }
  }

  return <main className="shell">
    <PageHeader eyebrow={t('ops_eyebrow')} title={t('ops_title')} subtitle={t('ops_subtitle')} />
    <Alert tone={covered ? 'ok' : 'warn'} title={covered ? t('ops_coverage_ready') : t('ops_coverage_gap')} />
    <div className="split">
      <Panel title={t('ops_create')}>
        <div className="stack">
          <Field label={t('ops_area')}><Select value={area} onChange={(event) => setArea(event.target.value as OperationsArea)} options={AREAS.map((value) => ({ value, label: value.replace('_', ' ') }))} /></Field>
          <Field label={t('ops_payload')}><Textarea rows={12} className="mono" value={payload} onChange={(event) => setPayload(event.target.value)} /></Field>
          <Button loading={busy} onClick={create}>{busy ? t('ops_creating') : t('ops_create')}</Button>
        </div>
      </Panel>
      <Panel title={t('ops_transition')}>
        <div className="stack">
          <Field label={t('ops_records')}><Select value={selected} onChange={(event) => { setSelected(event.target.value); setTarget(''); }} placeholder={t('ops_empty')} options={records.map((record) => ({ value: record.id, label: `${record.status} · ${record.id.slice(0, 8)}` }))} /></Field>
          {active && <>
            <div className="row"><Badge tone="info">{active.area}</Badge><Badge tone="neutral">{active.status}</Badge></div>
            <pre className="code-block">{JSON.stringify(active.payload, null, 2)}</pre>
            <Field label={t('ops_target')}><Select value={target} onChange={(event) => setTarget(event.target.value)} options={targets.map((value) => ({ value, label: value.replace('_', ' ') }))} /></Field>
            <Field label={t('ops_evidence')}><Textarea rows={8} className="mono" value={evidence} onChange={(event) => setEvidence(event.target.value)} /></Field>
            <Button disabled={!target} loading={busy} onClick={transition}>{t('ops_apply')}</Button>
          </>}
        </div>
      </Panel>
    </div>
    <Panel title={t('ops_records')}>
      {records.length === 0 ? <p className="muted">{t('ops_empty')}</p> : <div className="stack">{records.map((record) => <div key={record.id} className="row" style={{ justifyContent: 'space-between' }}><span className="mono">{record.id.slice(0, 8)}</span><Badge tone="neutral">{record.status}</Badge><span className="muted">{formatDate(record.updated_at)}</span></div>)}</div>}
    </Panel>
  </main>;
}
