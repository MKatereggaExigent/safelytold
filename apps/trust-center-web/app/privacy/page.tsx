import { Badge, Panel } from '@safelytold/ui/components';

const CONTROLS = [
  {
    title: 'Separate identity realms',
    body: 'The reporter identity vault is a different database from the case store. Opening it requires a purpose, approvals and a time limit.',
  },
  {
    title: 'Purpose-bound access',
    body: 'Every read carries a declared purpose that is logged. Access without a purpose is rejected.',
  },
  {
    title: 'What the reporter keeps',
    body: 'Case codes and recovery secrets stay with the reporter. Supporters get only the permissions the reporter chooses.',
  },
  {
    title: 'Retention and erasure',
    body: 'Records are retained only for the lawful purpose, then purged — including from backups, which are encrypted.',
  },
];

export default function PrivacyPage() {
  return (
    <main className="shell">
      <div className="hero">
        <h1>Privacy</h1>
        <p>Protection is engineered, not promised. Here is exactly how your data is held and who can ever touch it.</p>
      </div>

      <div className="grid">
        {CONTROLS.map((c) => (
          <Panel key={c.title} title={c.title}>
            <p>{c.body}</p>
          </Panel>
        ))}
      </div>

      <div className="split">
        <Panel title="Anonymity levels">
          <ul>
            <li><Badge>Anonymous</Badge> — no identity stored at all; only the report text.</li>
            <li><Badge>Confidential</Badge> — identity sealed in the vault, released only with approval.</li>
            <li><Badge>Identified</Badge> — identity known to the team, still encrypted at rest.</li>
          </ul>
        </Panel>
        <Panel title="What we never do">
          <ul>
            <li>Never label a person as risky, guilty or dangerous.</li>
            <li>Never infer identity from writing style.</li>
            <li>Never sell or share personal data.</li>
            <li>Never feed case data to public AI models.</li>
          </ul>
        </Panel>
      </div>
    </main>
  );
}
