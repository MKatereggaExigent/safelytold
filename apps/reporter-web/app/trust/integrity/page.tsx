'use client';

import { useState } from 'react';
import { Alert, Badge, Button, Field, Input, Panel } from '@safelytold/ui/components';
import { verifyLedgerProof, type MerkleProofStep } from '@safelytold/ui/api';
import { useI18n, useToast } from '@safelytold/ui/context';
import { TrustNav } from '../TrustNav';

export default function IntegrityPage() {
  const { t } = useI18n();
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
      push(t('integ_proof_invalid_json'), 'warn');
      return;
    }
    if (!leafHash.trim() || !root.trim()) {
      push(t('integ_provide_hash_root'), 'warn');
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
      <TrustNav />
      <div className="hero">
        <h1>{t('integ_title')}</h1>
        <p>{t('integ_subtitle')}</p>
      </div>

      <div className="split">
        <div className="stack">
          <Panel title={t('integ_sealed_title')}>
            <Badge>{t('integ_sealed_badge')}</Badge>
            <p>
              {t('integ_sealed_body')}
            </p>
          </Panel>
          <Panel title={t('integ_audit_title')}>
            <Badge>{t('integ_audit_badge')}</Badge>
            <p>
              {t('integ_audit_body')}
            </p>
          </Panel>
          <Panel title={t('integ_anchor_title')}>
            <Badge>{t('integ_anchor_badge')}</Badge>
            <p>
              {t('integ_anchor_body')}
            </p>
          </Panel>
        </div>

        <Panel title={t('integ_verify_title')}>
          <p className="muted">
            {t('integ_verify_body')}
          </p>
          <Field label={t('integ_leaf_hash_label')} required>
            <Input value={leafHash} onChange={(e) => setLeafHash(e.target.value)} placeholder={t('integ_hex_placeholder')} className="mono" autoComplete="off" />
          </Field>
          <Field label={t('integ_merkle_root_label')} required>
            <Input value={root} onChange={(e) => setRoot(e.target.value)} placeholder={t('integ_hex_placeholder')} className="mono" autoComplete="off" />
          </Field>
          <Field label={t('integ_proof_steps_label')} hint={t('integ_proof_steps_hint')}>
            <Input value={proofText} onChange={(e) => setProofText(e.target.value)} placeholder={t('integ_proof_placeholder')} className="mono" autoComplete="off" />
          </Field>
          <Button variant="secondary" onClick={verify} loading={busy}>{t('integ_verify_button')}</Button>
          {result !== null && (
            <Alert tone={result ? 'ok' : 'danger'} title={result ? t('integ_result_valid_title') : t('integ_result_invalid_title')}>
              {result ? t('integ_result_valid_body') : t('integ_result_invalid_body')}
            </Alert>
          )}
        </Panel>
      </div>
    </main>
  );
}
