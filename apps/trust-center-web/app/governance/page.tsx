import { Badge, Panel } from '@safelytold/ui/components';

const PRINCIPLES = [
  {
    title: 'Fair process before labels',
    body: 'A report is unverified until tested. Status moves to substantiated or unsubstantiated only after an investigation with evidence, not suspicion.',
  },
  {
    title: 'Least privilege',
    body: 'Access requires an assignment, a declared purpose and a conflict check. Nobody reads a case by default — including administrators.',
  },
  {
    title: 'Human accountability',
    body: 'Every significant action is tied to an audited identity. AI output is advisory and always requires a human decision.',
  },
  {
    title: 'Data minimisation',
    body: 'Only the minimum personal data needed for the process is collected, and it is deleted when the purpose is complete.',
  },
  {
    title: 'Transparent by default',
    body: 'Aggregates and integrity proofs are public. Individual facts are private and revocable.',
  },
];

export default function GovernancePage() {
  return (
    <main className="shell">
      <div className="hero">
        <h1>Governance</h1>
        <p>Who decides what, and under what rules. The platform encodes guardrails so that power is never unchecked.</p>
      </div>

      <div className="grid">
        {PRINCIPLES.map((p) => (
          <Panel key={p.title} title={p.title}>
            <p>{p.body}</p>
          </Panel>
        ))}
      </div>

      <div className="split">
        <Panel title="Separation of duties">
          <Badge>Configure ≠ read</Badge>
          <p>
            Tenant owners configure policies and integrations but cannot read cases. Raw case access requires a
            separate assignment, purpose and conflict check. Breaking separation is a recorded, approvable event.
          </p>
        </Panel>
        <Panel title="Oversight">
          <Badge>Audited</Badge>
          <p>
            Approvals, reveals, exports and decisions are written to an append-only audit chain. Regulators and
            employee representatives can re-derive and verify the chain without seeing case content.
          </p>
        </Panel>
      </div>
    </main>
  );
}
