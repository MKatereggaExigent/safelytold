'use client';

import Link from 'next/link';
import { useSession } from '@safelytold/ui/context';
import { DEMO_TENANT_ID } from '@safelytold/ui/api';

const journeys = [
  ['Reporting choices', '/report', 'Anonymous, Verified Anonymous, Confidential and Identified intake paths.'],
  ['Case lifecycle', '/cases', 'Triage, assignment, investigation, decision and closure.'],
  ['Protected mailbox', '/mailbox', 'Two-way communication without exposing an anonymous reporter.'],
  ['Evidence integrity', '/evidence', 'Malware scanning, immutable receipts, legal hold and verification.'],
  ['Protection', '/protection', 'Anti-retaliation measures, check-ins and risk escalation.'],
  ['Privacy', '/privacy', 'Consent, data-subject requests and breach handling.'],
  ['Support', '/support', 'Consent-linked referral to a verified provider directory.'],
  ['Operations', '/operations', 'Hotline, 24/7 coverage, training, QA and continuity evidence.'],
  ['Management reporting', '/analytics', 'Privacy-thresholded trends and management metrics.'],
  ['Security and audit', '/security', 'Alert triage, containment evidence and immutable audit history.'],
];

const personas = [
  ['demo.owner', 'Tenant configuration and access administration'],
  ['demo.case-manager', 'Triage, cases, assignments and escalation'],
  ['demo.investigator', 'Investigation plans and evidence-balanced findings'],
  ['demo.reviewer', 'Independent review, decisions and appeals'],
  ['demo.privacy', 'Privacy requests, consent and breach assessment'],
  ['demo.protection', 'Protection plans and retaliation monitoring'],
  ['demo.support', 'Consent-governed support referrals'],
  ['demo.security', 'Security monitoring and response'],
  ['demo.auditor', 'Read-only assurance and audit review'],
];

export default function DemoTourPage() {
  const { session } = useSession();
  if (session.tenantId !== DEMO_TENANT_ID) {
    return <main className="staff-page"><div className="empty-state"><h1>Not available</h1><p>The guided tour is restricted to the synthetic demonstration tenant.</p></div></main>;
  }
  return (
    <main className="staff-page" data-no-translate>
      <div className="page-heading"><div><span className="eyebrow">Production-equivalent tenant</span><h1>Explore the complete SafelyTold lifecycle</h1><p>Every record is fictional, but every workflow and control is the same implementation used in production. External deliveries terminate at controlled sandbox providers.</p></div></div>
      <section className="panel"><h2>Suggested walkthrough</h2><div className="demo-grid">
        {journeys.map(([title, href, detail], index) => <Link className="demo-card" href={href} key={title}><span className="demo-step">{String(index + 1).padStart(2, '0')}</span><strong>{title}</strong><p>{detail}</p></Link>)}
      </div></section>
      <section className="panel"><h2>Persona accounts</h2><p className="muted">Use the credentials supplied through the secure demo invitation. MFA enrollment and account expiry remain enforced.</p><div className="demo-personas">
        {personas.map(([name, purpose]) => <div key={name}><code>{name}</code><span>{purpose}</span></div>)}
      </div></section>
      <section className="panel demo-safety"><h2>Production equivalence</h2><p>Approvals, role checks, tenant isolation, identity disclosure controls, exports, notification state transitions and ledger integrity execute normally. Only the final external destination is sandboxed. No demo persona receives platform-super-admin privileges.</p></section>
    </main>
  );
}
