'use client';

import { useState } from 'react';
import { Alert, Badge, Button, Field, Input, Panel } from '@safelytold/ui/components';
import { verifyLedgerProof, type MerkleProofStep } from '@safelytold/ui/api';
import { useToast } from '@safelytold/ui/context';

export default function IntegrityPage() {
  const { push } = useToast();
  const [leafHash, setLeafHash] = useState('');
  const [root, setRoot] = useState('');
  const [proofText, setProofText] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<boolean | null>(null);

  async function verify() {
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
    setBusy(true);
    setResult(null);
    try {
      const res = await verifyLedgerProof(leafHash.trim(), root.trim(), proof);
      setResult(res.valid);
    } catch {
      setResult(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell">
      <div className="hero">
        <h1>Integrity</h1>
        <p>The technical controls that make it possible to trust the process without trusting the reader.</p>
      </div>

      <div className="split">
        <div className="stack">
          <Panel title="Sealed records">
            <Badge>Envelope encryption</Badge>
            <p>
              Case data is encrypted with per-case keys, wrapped by a key-management realm and only unwrapped for an
              approved, purpose-bound session. The database cannot be read meaningfully by a backup, a breach or an
              administrator.
            </p>
          </Panel>
          <Panel title="Append-only audit chain">
            <Badge>Tamper-evident</Badge>
            <p>
              Each audit entry is hashed together with the previous entry and signed. Re-ordering, deleting or editing
              any entry breaks the chain — verifiable by anyone with the first hash.
            </p>
          </Panel>
          <Panel title="Cryptographic anchoring">
            <Badge>Hashes only</Badge>
            <p>
              Batches of evidence manifests, audit records and policy versions are merkle-rooted and anchored. Anchors
              carry hashes only — never case content — so they can be public.
            </p>
          </Panel>
        </div>

        <Panel title="Verify a merkle proof">
          <p className="muted">
            Anyone can confirm that a leaf hash is genuinely contained in an anchored merkle root, using only the proof
            path. This is the same check the platform performs internally.
          </p>
          <Field label="Leaf hash" required>
            <Input value={leafHash} onChange={(e) => setLeafHash(e.target.value)} placeholder="hex…" className="mono" autoComplete="off" />
          </Field>
          <Field label="Merkle root" required>
            <Input value={root} onChange={(e) => setRoot(e.target.value)} placeholder="hex…" className="mono" autoComplete="off" />
          </Field>
          <Field label="Proof steps (JSON)" hint='e.g. [{ "index": 0, "sibling": "hex…" }]'>
            <Input value={proofText} onChange={(e) => setProofText(e.target.value)} placeholder='[{"index":0,"sibling":"…"}]' className="mono" autoComplete="off" />
          </Field>
          <Button variant="secondary" onClick={verify} loading={busy}>Verify proof</Button>
          {result !== null && (
            <Alert tone={result ? 'ok' : 'danger'} title={result ? 'Proof valid' : 'Proof invalid'}>
              {result ? 'The leaf is genuinely contained in the anchored root.' : 'The leaf is not covered by this root and proof.'}
            </Alert>
          )}
        </Panel>
      </div>
    </main>
  );
}
