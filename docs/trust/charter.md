# SafelyTold Trust & Safety Charter

Source: Feasibility/Product/Architecture Proposal §§8–10, §14, §15, §19, Appendix F.

This charter codifies the non-negotiable commitments that govern the SafelyTold platform (reporter portal, staff workspace, operations, AI services). It binds the product team and every subscribing tenant; deviations require independent advisory review and public disclosure.

## 1. Purpose

SafelyTold exists to let people raise workplace harm without retaliation while enabling fair, lawful investigations. Neutrality, privacy and safety outrank feature velocity or revenue.

## 2. Platform Commitments

1. **Separation of realms** – Anonymous reporters authenticate only with case code + secret. Their identity (if provided) resides in a separate encrypted vault with purpose-bound access.
2. **No deanonymisation** – The platform will not build covert identity correlation, behavioural fingerprinting or “trust scores”. Metadata is minimised, logs are scrubbed and deanonymisation requests are rejected unless legally compelled and vetted by the advisory board.
3. **No adverse AI decisions** – AI may assist with drafting, translation or chronology but may not make credibility findings, discipline recommendations or surveillance.
4. **Conflict-aware routing** – Case assignment is always filtered through declared relationships, organisational hierarchy, jurisdiction restrictions and recusal policies.
5. **Immutable evidence** – Every submission is hashed, sealed and preserved with chain-of-custody records. Edits occur in distinct working copies.
6. **Right to fair process** – Reporters, subjects and witnesses receive notice, opportunity to respond and appeal routes consistent with local law, subject to safety/legal holds.
7. **Transparency & escalation** – The public trust centre always explains access logging, governance structure, independent escalation and ombuds contacts.
8. **Breach handling** – Suspected privacy/security incidents trigger dual notification (tenant + regulator) “as soon as reasonably possible”, with full timeline disclosure.
9. **Data minimisation** – Only the minimum personal data necessary for a case is processed; retention defaults to the shortest legally permissible period.
10. **Righteous refusal** – The platform declines features or tenants that would weaponise data (e.g., loyalty scores, mass surveillance, union busting).

## 3. Tenant Obligations

Tenants must agree—in contract and policy—to:

1. Prohibit retaliation, discrimination or disadvantage against any reporter, witness, supporter or handler acting in good faith.
2. Honour independent escalation: cases implicating executives or unsafe chains route to external ombuds/integrity committee.
3. Publish staff-facing policies covering confidentiality, conflict declarations, retaliation consequences and appeal rights.
4. Consult employee representatives / works councils before deployment and provide plain-language privacy notices.
5. Assign accountable roles: Tenant Owner (commercial), Integrity Committee, DPO/Privacy Officer, Case Operations Lead.
6. Provide access logs to employee representatives on request (aggregated/cohorted to preserve privacy).
7. Fund required legal packs and translations for each jurisdiction where cases will run.
8. Notify the platform of regulatory investigations or data subject requests that involve HELP ME data.
9. Undergo annual governance review with the platform’s advisory board.

## 4. Prohibited Uses

The following are disallowed and will lead to termination:

- Using platform data to build employee loyalty, productivity or “risk” scores.
- Attempting to identify anonymous reporters for convenience, curiosity or discipline.
- Uploading evidence harvested via illegal surveillance.
- Training general-purpose AI models on allegation content without explicit lawful basis and advisory approval.
- Granting blanket executive access or ignoring conflict recusal rules.
- Suppressing lawful external whistleblowing or labour-rights activity.

## 5. Governance & Oversight

1. **Independent Advisory Group** (see `docs/trust/advisory/charter.md`) reviews policy changes, AI proposals, security incidents and tenant escalations.
2. **Trust Centre Publication** – Access log practices, advisory members, ombuds contacts and recent improvements are published at /trust.
3. **Change Management** – Material policy or feature changes require risk assessment, advisory sign-off and 30 days’ notice to tenants.
4. **Audit & Evidence** – All access requests, break-glass events, AI outputs and exports are logged in append-only tables and reviewed quarterly.

## 6. Incident Response Principles

1. **Rapid containment** – Disable affected access paths, rotate secrets, preserve forensic snapshots.
2. **Dual notification** – Inform both tenant leadership and regulatory bodies per local law; provide reporters with non-retaliatory guidance.
3. **Root cause transparency** – Publish post-incident report (scope, impact, remediation, follow-up tasks) and track in backlog.
4. **Remediation with empathy** – Ensure impacted reporters or witnesses receive additional protection/check-ins.

## 7. Review Cycle

- Charter reviewed quarterly by the advisory group.
- Amendments logged in `docs/trust/charter.md` with version history and summary of changes.
