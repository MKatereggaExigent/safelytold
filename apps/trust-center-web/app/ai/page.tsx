'use client';

import { useEffect, useState } from 'react';
import { Badge, Panel } from '@safelytold/ui/components';
import { getAiGovernance, type AiGovernance } from '@safelytold/ui/api';

export default function AiPage() {
  const [governance, setGovernance] = useState<AiGovernance | null>(null);

  useEffect(() => {
    getAiGovernance().then(setGovernance).catch(() => setGovernance(null));
  }, []);

  const capabilities = governance?.capabilities ?? [];
  const prohibited = governance?.prohibited_purposes ?? [];

  return (
    <main className="shell">
      <div className="hero">
        <h1>AI, kept in its lane</h1>
        <p>Models draft, humans decide. Here are the boundaries in force, published live from the AI governance service.</p>
      </div>

      <div className="split">
        <Panel title="What AI may do">
          {capabilities.length === 0 ? (
            <p className="muted">Loading capabilities…</p>
          ) : (
            <ul>
              {capabilities.map((c) => (
                <li key={c.name}>
                  <Badge tone="info">{c.name.replace(/_/g, ' ')}</Badge>
                  {c.description ? <span className="muted"> — {c.description}</span> : null}
                </li>
              ))}
            </ul>
          )}
          <p className="muted" style={{ marginTop: 8 }}>
            Raw evidence allowed: <strong>{String(governance?.raw_evidence_allowed)}</strong> · Human approval default:{' '}
            <strong>{String(governance?.human_approval_default)}</strong>
          </p>
        </Panel>
        <Panel title="What AI never does">
          {prohibited.length === 0 ? (
            <p className="muted">Loading prohibited purposes…</p>
          ) : (
            <ul>
              {prohibited.map((p) => (
                <li key={p}><Badge tone="warn">{p.replace(/_/g, ' ')}</Badge></li>
              ))}
            </ul>
          )}
          <p className="muted" style={{ marginTop: 8 }}>
            No credibility scores. No guilt predictions. No dismissal, promotion, reputation or mental-health scoring.
          </p>
        </Panel>
      </div>
    </main>
  );
}
