'use client';

import { useState } from 'react';
import { Alert, Button, Field, Input, PageHeader, Panel } from '@safelytold/ui/components';
import { DEFAULT_SESSION, verifyAuditChain, verifyLedgerProof } from '@safelytold/ui/api';
import { useI18n, useToast } from '@safelytold/ui/context';
import { TrustNav } from '../TrustNav';

export default function VerifyPage() {
  const { t } = useI18n();
  const { push } = useToast();
  const [tenantId, setTenantId] = useState(DEFAULT_SESSION.tenantId);
  const [chainResult, setChainResult] = useState<string | null>(null);
  const [chainOk, setChainOk] = useState(false);
  const [verifyingChain, setVerifyingChain] = useState(false);

  const [leafHash, setLeafHash] = useState('');
  const [root, setRoot] = useState('');
  const [proofText, setProofText] = useState('');
  const [proofResult, setProofResult] = useState<string | null>(null);
  const [proofOk, setProofOk] = useState(false);
  const [verifyingProof, setVerifyingProof] = useState(false);

  async function verifyChain() {
    setVerifyingChain(true);
    try {
      const result = await verifyAuditChain(tenantId.trim(), DEFAULT_SESSION);
      setChainOk(result.valid);
      setChainResult(result.valid
        ? t('verify_chain_valid', { entries: String(result.entries), head: String(result.head?.slice(0, 16)) })
        : t('verify_chain_invalid', { sequence: String(result.failed_sequence) }));
    } catch (err) {
      setChainOk(false);
      setChainResult(err instanceof Error ? err.message : t('verify_chain_failed'));
    } finally {
      setVerifyingChain(false);
    }
  }

  async function verifyProof() {
    setVerifyingProof(true);
    try {
      const steps = proofText.trim()
        .split('\n')
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => {
          const [index, sibling] = line.split(/\s+/);
          return { index: Number(index), sibling };
        });
      const result = await verifyLedgerProof(leafHash.trim(), root.trim(), steps);
      setProofOk(result.valid);
      setProofResult(result.valid ? t('verify_proof_valid') : t('verify_proof_invalid'));
    } catch (err) {
      setProofOk(false);
      setProofResult(err instanceof Error ? err.message : t('verify_proof_failed'));
    } finally {
      setVerifyingProof(false);
    }
  }

  return (
    <main className="shell">
      <TrustNav />
      <PageHeader
        eyebrow={t('verify_eyebrow')}
        title={t('verify_title')}
        subtitle={t('verify_subtitle')}
      />

      <div className="split">
        <Panel title={t('verify_chain_title')}>
          <p className="muted">
            {t('verify_chain_body')}
          </p>
          <Field label={t('verify_tenant_label')} required>
            <Input value={tenantId} onChange={(e) => setTenantId(e.target.value)} className="mono" />
          </Field>
          <Button onClick={verifyChain} loading={verifyingChain}>{t('verify_chain_button')}</Button>
          {chainResult && (
            <Alert tone={chainOk ? 'ok' : 'danger'} title={t('verify_chain_result_title')}>
              {chainResult}
            </Alert>
          )}
        </Panel>

        <Panel title={t('verify_proof_title')}>
          <p className="muted">
            {t('verify_proof_body_prefix')}<code className="mono">index sibling</code>.
          </p>
          <Field label={t('verify_leaf_label')} required>
            <Input value={leafHash} onChange={(e) => setLeafHash(e.target.value)} className="mono" />
          </Field>
          <Field label={t('verify_root_label')} required>
            <Input value={root} onChange={(e) => setRoot(e.target.value)} className="mono" />
          </Field>
          <Field label={t('verify_proof_label')}>
            <Input
              value={proofText}
              onChange={(e) => setProofText(e.target.value)}
              placeholder={t('verify_proof_placeholder')}
              className="mono"
            />
          </Field>
          <Button onClick={verifyProof} loading={verifyingProof}>{t('verify_proof_button')}</Button>
          {proofResult && (
            <Alert tone={proofOk ? 'ok' : 'danger'} title={t('verify_proof_result_title')}>
              {proofResult}
            </Alert>
          )}
        </Panel>
      </div>
    </main>
  );
}
