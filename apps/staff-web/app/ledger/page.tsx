'use client';

import { useState } from 'react';
import { Alert, Badge, Button, CodeBlock, DataTable, EmptyState, Field, Input, PageHeader, Panel, Select, StatusPill } from '@safelytold/ui/components';
import { createAnchor, verifyLedgerProof, type MerkleProofStep, type RecordView } from '@safelytold/ui/api';
import { useSession } from '@safelytold/ui/context';
import { useToast } from '@safelytold/ui/context';
import { formatDate, useRecords } from '@safelytold/ui/hooks';
import { sha256Hex } from '@safelytold/ui/crypto';
import { latestCaseRecords, summarizeCase } from '../../lib/staff';

const ANCHOR_KINDS = ['audit_batch', 'evidence_manifest', 'disclosure_package', 'policy_version'] as const;

export default function LedgerPage() {
  const { session } = useSession();
  const { push } = useToast();
  const { records: anchors, loading, refresh } = useRecords('ledger');
  const { records: caseRecords } = useRecords('case');

  const [kind, setKind] = useState<typeof ANCHOR_KINDS[number]>('audit_batch');
  const [leafCount, setLeafCount] = useState('3');
  const [busy, setBusy] = useState(false);
  const [anchor, setAnchor] = useState<Record<string, unknown> | null>(null);

  const [leafHash, setLeafHash] = useState('');
  const [root, setRoot] = useState('');
  const [proofText, setProofText] = useState('');
  const [proofResult, setProofResult] = useState<boolean | null>(null);
  const [verifying, setVerifying] = useState(false);

  const cases = latestCaseRecords(caseRecords).map(summarizeCase);

  async function anchorBatch() {
    const count = Math.max(1, Math.min(32, Number.parseInt(leafCount, 10) || 1));
    setBusy(true);
    try {
      const leafHashes: string[] = [];
      for (let i = 0; i < count; i += 1) leafHashes.push(await sha256Hex(`dev-sample-${i + 1}-${Date.now()}`));
      const res = await createAnchor({
        tenant_hash: await sha256Hex(session.tenantId),
        kind,
        leaf_hashes: leafHashes,
        metadata: { mode: 'demo', cases: cases.slice(0, 3).map((c) => c.id.slice(0, 8)) },
      }, session);
      setAnchor(res as unknown as Record<string, unknown>);
      push(`Anchor ${res.mode} — root ${res.merkle_root.slice(0, 16)}…`, 'ok');
      refresh();
    } catch (err) {
      push(err instanceof Error ? err.message : 'Anchoring failed', 'danger');
    } finally {
      setBusy(false);
    }
  }

  async function verifyProof() {
    let proof: MerkleProofStep[];
    try {
      proof = JSON.parse(proofText || '[]') as MerkleProofStep[];
    } catch {
      push('Proof must be valid JSON', 'warn');
      return;
    }
    if (!leafHash.trim() || !root.trim()) {
      push('Provide the leaf hash and merkle root', 'warn');
      return;
    }
    setVerifying(true);
    setProofResult(null);
    try {
      const res = await verifyLedgerProof(leafHash.trim(), root.trim(), proof);
      setProofResult(res.valid);
    } catch (err) {
      setProofResult(false);
    } finally {
      setVerifying(false);
    }
  }

  return (
    <main className="shell">
      <PageHeader
        eyebrow="Integrity ledger"
        title="Cryptographic anchoring"
        subtitle="Batches of evidence manifests, audit records and policy versions are anchored to an append-only merkle ledger."
      />

      <div className="split">
        <Panel title="Anchor a batch">
          <Field label="Batch kind">
            <Select value={kind} onChange={(e) => setKind(e.target.value as typeof ANCHOR_KINDS[number])}>
              {ANCHOR_KINDS.map((k) => <option key={k} value={k}>{k.replace(/_/g, ' ')}</option>)}
            </Select>
          </Field>
          <Field label="Number of leaves" hint="Demo leaves are generated deterministically for this environment.">
            <Input type="number" min={1} max={32} value={leafCount} onChange={(e) => setLeafCount(e.target.value)} autoComplete="off" />
          </Field>
          <Button onClick={anchorBatch} loading={busy} size="lg">Anchor batch</Button>
        </Panel>

        <Panel title="Verify a merkle proof">
          <Field label="Leaf hash" required>
            <Input value={leafHash} onChange={(e) => setLeafHash(e.target.value)} placeholder="hex…" className="mono" autoComplete="off" />
          </Field>
          <Field label="Merkle root" required>
            <Input value={root} onChange={(e) => setRoot(e.target.value)} placeholder="hex…" className="mono" autoComplete="off" />
          </Field>
          <Field label="Proof steps (JSON)" hint='e.g. [{ "index": 0, "sibling": "hex…" }]'>
            <Input value={proofText} onChange={(e) => setProofText(e.target.value)} placeholder='[{"index":0,"sibling":"…"}]' className="mono" autoComplete="off" />
          </Field>
          <Button variant="secondary" onClick={verifyProof} loading={verifying}>Verify proof</Button>
          {proofResult !== null && (
            <Alert tone={proofResult ? 'ok' : 'danger'} title={proofResult ? 'Proof valid' : 'Proof invalid'}>
              {proofResult ? 'The leaf is genuinely contained in the anchored root.' : 'The leaf is not covered by this root and proof.'}
            </Alert>
          )}
        </Panel>
      </div>

      {anchor && (
        <Panel title="Last anchor">
          <CodeBlock
            compact
            text={JSON.stringify(anchor, null, 2)}
            tone="violet"
          />
        </Panel>
      )}

      <Panel title="Anchor history" subtitle={loading ? 'Loading…' : `${anchors.length} anchored batches`} padded={false}>
        <DataTable
          keyField="id"
          loading={loading}
          empty={<EmptyState title="No anchors yet" description="Anchored batches appear here." />}
          columns={[
            { key: 'kind', label: 'Kind', render: (r) => <Badge tone="accent">{(r as RecordView).kind.replace(/_/g, ' ')}</Badge> },
            { key: 'root', label: 'Merkle root', render: (r) => <span className="mono">{(r as RecordView).payload.merkle_root as string ?? '—'}</span> },
            { key: 'leaves', label: 'Leaves', render: (r) => <span className="muted">{(r as RecordView).payload.leaf_count as number ?? 0}</span> },
            { key: 'tx', label: 'Transaction', render: (r) => <Badge tone="neutral">{(r as RecordView).payload.transaction_hash as string ? 'anchored' : 'database mode'}</Badge> },
            { key: 'created', label: 'Anchored', render: (r) => <span className="muted">{formatDate((r as RecordView).payload.created_at as string | undefined)}</span> },
          ]}
          rows={anchors}
        />
      </Panel>
    </main>
  );
}
