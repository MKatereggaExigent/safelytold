import Link from 'next/link';
import { Badge, Panel } from '@safelytold/ui/components';

export default function Trust() {
  return (
    <main className="shell">
      <div className="hero">
        <h1>Trust must be inspectable.</h1>
        <p>
          The platform is designed to support fair process — not label people, predict guilt or automate employment
          decisions. Every claim below is backed by verifiable technical controls.
        </p>
      </div>

      <div className="grid">
        <Panel title="Full integrity lifecycle">
          <Badge>Beyond a hotline</Badge>
          <p>Prevention, four reporting modes, triage, fair case management, reporter protection, resolution and board-level organisational learning.</p>
        </Panel>
        <Panel title="Privacy">
          <Badge>Data minimisation</Badge>
          <p>Separate identity realms, case-level encryption, purpose-bound access and no raw case data on the blockchain.</p>
        </Panel>
        <Panel title="AI boundaries">
          <Badge>Human review</Badge>
          <p>No credibility, guilt, dismissal, promotion, reputation or mental-health scoring. Models draft, humans decide.</p>
        </Panel>
        <Panel title="Integrity proofs">
          <Badge>Hashes only</Badge>
          <p>Append-only audit chains and permissioned blockchain anchoring prove that evidence and audit manifests were not silently altered.</p>
        </Panel>
        <Panel title="Fair outcomes">
          <Badge>Neutral language</Badge>
          <p>Reports are “unverified” until tested through due process. Referral, not accusation, is the default for genuine reports.</p>
        </Panel>
      </div>

      <div className="split">
        <Panel title="What we publish">
          <ul>
            <li>Thresholded aggregate reporting rates and process timeliness.</li>
            <li>Substantiation categories, remediation completion and appeals.</li>
            <li>Small cohorts are never published below the minimum size.</li>
          </ul>
          <Link className="btn btn-primary" href="/reports">Read the transparency reports</Link>
        </Panel>
        <Panel title="How to verify">
          <ul>
            <li>Audit chains can be re-derived and checked end to end.</li>
            <li>Merkle proofs confirm a manifest is contained in an anchor.</li>
            <li>Independent parties can verify without seeing case content.</li>
          </ul>
          <Link className="btn btn-secondary" href="/integrity">See the integrity controls</Link>
        </Panel>
      </div>
    </main>
  );
}
