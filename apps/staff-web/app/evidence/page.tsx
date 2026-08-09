'use client';

import { useCallback, useRef, useState } from 'react';
import { Alert, Badge, Button, DataTable, EmptyState, Field, Input, PageHeader, Panel, Select, StatusPill } from '@safelytold/ui/components';
import { applyLegalHold, listRecords, uploadEvidence, type EvidenceReceipt, type RecordView } from '@safelytold/ui/api';
import { useSession } from '@safelytold/ui/context';
import { useToast } from '@safelytold/ui/context';
import { formatBytes, formatDate, useRecords } from '@safelytold/ui/hooks';
import { latestCaseRecords, summarizeCase } from '../../lib/staff';

export default function EvidencePage() {
  const { session } = useSession();
  const { push } = useToast();
  const { records: evidenceRecords, loading, refresh } = useRecords('evidence');
  const { records: caseRecords } = useRecords('case');

  const cases = latestCaseRecords(caseRecords).map(summarizeCase);
  const [caseId, setCaseId] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [receipt, setReceipt] = useState<EvidenceReceipt | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const upload = useCallback(async () => {
    if (!file) {
      push('Choose a file to upload', 'warn');
      return;
    }
    if (!caseId) {
      push('Select the case this evidence belongs to', 'warn');
      return;
    }
    setUploading(true);
    setReceipt(null);
    try {
      const result = await uploadEvidence(caseId, file, session);
      setReceipt(result);
      push('Evidence uploaded and sealed', 'ok');
      setFile(null);
      if (inputRef.current) inputRef.current.value = '';
      refresh();
    } catch (err) {
      push(err instanceof Error ? err.message : 'Upload failed', 'danger');
    } finally {
      setUploading(false);
    }
  }, [file, caseId, session, push, refresh]);

  const applyHold = useCallback(async (evidenceId: string) => {
    try {
      await applyLegalHold(evidenceId, session);
      push('Legal hold applied — object is preserved', 'ok');
      refresh();
    } catch (err) {
      push(err instanceof Error ? err.message : 'Could not apply legal hold', 'danger');
    }
  }, [session, push, refresh]);

  return (
    <main className="shell">
      <PageHeader
        eyebrow="Evidence vault"
        title="Sealed originals, sanitised working copies"
        subtitle="Every upload is hashed, scanned and stored as an immutable sealed original. Working copies are separate."
      />

      <div className="split">
        <Panel title="Upload evidence">
          <Field label="Case" required>
            {cases.length === 0 ? (
              <Input value={caseId} onChange={(e) => setCaseId(e.target.value)} placeholder="Enter case reference" className="mono" />
            ) : (
              <Select value={caseId} onChange={(e) => setCaseId(e.target.value)} placeholder="Select a case…">
                {cases.map((c) => (
                  <option key={c.id} value={c.id}>{c.id.slice(0, 8)} · {c.status}</option>
                ))}
              </Select>
            )}
          </Field>
          <Field label="File" required hint="Original is sealed; a sanitised working copy is created separately.">
            <input
              ref={inputRef}
              type="file"
              className="input"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </Field>
          <Button onClick={upload} loading={uploading} size="lg" disabled={!file || !caseId}>Upload & seal</Button>
          {receipt && (
            <Alert tone="ok" title="Sealed and fingerprinted">
              <p className="mono" style={{ wordBreak: 'break-all' }}>SHA-256: {receipt.sha256}</p>
              <p className="muted">Size {formatBytes(receipt.size_bytes)} · scan status {receipt.scan_status}</p>
            </Alert>
          )}
        </Panel>

        <Panel title="Evidence controls">
          <ul>
            <li><strong>Sealed original</strong> — immutable, never overwritten.</li>
            <li><strong>Working copy</strong> — sanitised and redactable for investigation.</li>
            <li><strong>Legal hold</strong> — preserves against deletion or retention expiry.</li>
            <li><strong>Manifest</strong> — links every export to its hash and redaction history.</li>
          </ul>
          <Alert tone="warn" title="Dangerous content isolation">
            <p>Documents are untrusted. Preview is sandboxed and AI never receives raw embedded instructions.</p>
          </Alert>
        </Panel>
      </div>

      <Panel title="Evidence register" subtitle={loading ? 'Loading…' : `${evidenceRecords.length} items`} padded={false}>
        <DataTable
          keyField="id"
          loading={loading}
          empty={<EmptyState title="No evidence yet" description="Uploads appear here with their hashes and copy status." />}
          columns={[
            { key: 'id', label: 'Evidence', render: (r) => <span className="mono">{r.id.slice(0, 10)}…</span> },
            { key: 'kind', label: 'Kind', render: (r) => <Badge tone="neutral">{r.kind.replace(/_/g, ' ')}</Badge> },
            { key: 'status', label: 'State', render: (r) => <StatusPill status={r.status} /> },
            { key: 'case', label: 'Case', render: (r) => <span className="muted">{(r.payload as Record<string, unknown>).case_id as string ? ((r.payload as Record<string, unknown>).case_id as string).slice(0, 8) : '—'}</span> },
            { key: 'hash', label: 'SHA-256', render: (r) => <span className="mono" style={{ fontSize: '0.72rem' }}>{(r.payload as Record<string, unknown>).sha256 as string ?? '—'}</span> },
            { key: 'legal_hold', label: 'Legal hold', render: (r) => (r.status === 'legal_hold' ? <Badge tone="danger">held</Badge> : (
              <Button variant="ghost" size="sm" onClick={() => applyHold(r.id)}>Apply hold</Button>
            )) },
            { key: 'created_at', label: 'Received', render: (r) => <span className="muted">{formatDate((r.payload as Record<string, unknown>).created_at as string)}</span> },
          ]}
          rows={evidenceRecords}
        />
      </Panel>
    </main>
  );
}
