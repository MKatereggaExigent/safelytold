# safelytold – Master Requirements & Traceability Matrix

Source reference: `C:\Users\michael.kateregga\Downloads\safelytold_feasibility_product_business_architecture_proposal.docx`.

This document enumerates every feature, control, or business rule described in the feasibility & architecture proposal and maps it to the current implementation state. Each requirement is uniquely identified, tagged with the originating section, classified per the MoSCoW priorities in Appendix A, and assigned an implementation status. Keep this matrix updated as work progresses; no requirement is “done” until the linked acceptance criteria and governance artefacts exist in the repository or operating procedures.

Status legend: **Done** – implemented & validated; **Partial** – some elements exist but gaps remain; **Not Started** – no implementation yet; **N/A** – explicitly out-of-scope per current phase.

## 1. Trust, Governance & Market Positioning

| ID | Requirement | Doc Ref | Priority | Status | Notes / Next Actions |
| --- | --- | --- | --- | --- | --- |
| TRUST-01 | Publish non-negotiable trust charter (no covert monitoring, no anonymous deanonymisation, no adverse AI, etc.) and tenant prohibitions | §19 (Final recommendation) | Must | Partial | Initial charter drafted in `/docs/trust/charter.md`; next steps: advisory review + tenant contract linkage. |
| TRUST-02 | Establish independent advisory group (employee voice, labour law, privacy, investigations, psychology, union, security) | Appendix F #1 | Must | Partial | Advisory charter drafted in `/docs/trust/advisory/charter.md`; membership recruitment + minutes pending. |
| TRUST-03 | Execute 90-day validation programme (interviews, prototypes, red-team privacy, legal packs, pilot commitments) | §18.4 | Must | Not Started | Requires research artefacts, usability studies, synthetic data. |
| TRUST-04 | Three paid design partners with independent escalation + anti-retaliation commitments | Appendix F #5 and §8.5 | Must | Not Started | Contract artefacts + onboarding checklist. |
| TRUST-05 | Personal journal entry point for employees | §19 + Appendix A (Must) | Partial | MVP journal exists (`/apps/reporter-web/app/journal`); needs encrypted storage hardening + trust copy updates from proposal. |
| TRUST-06 | Conflict-safe routing & recusal workflow + metrics | §§8.5, 12.3, 18.2 | Not Started | Needs policy engine + RLS + assignment UI. |
| TRUST-07 | Anti-retaliation protections (plans, check-ins, escalation routes) | §§8.5, 12.2, 13.3 | Not Started | No retaliation module yet; create Temporal workflow + UI. |
| TRUST-08 | Public trust centre with transparent governance, access logs, privacy commitments | §19, §8.5 | Partial | `/trust` pages exist but lack governance artefacts; add charter, access log disclosure, escalation instructions. |

## 2. Legal, Compliance & Policy Packs

| ID | Requirement | Doc Ref | Priority | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| LEGAL-01 | South African launch baseline mapped to PDA, EEA, LRA, POPIA, harassment Code | §10.2 | Must | Partial | Initial requirements documented in `legal-packs/za/requirements.md` (including remote-work contexts, case-law scenarios); counsel review pending. |
| LEGAL-02 | POPIA security compromise workflow (notify Regulator + data subjects promptly) | §10.2 | Must | Not Started | Requires incident runbook + automation. |
| LEGAL-03 | Global compliance architecture with configurable notices, retention, DSAR, lawful bases | §10.3 | Must | Not Started | Needs policy engine + configuration UI. |
| LEGAL-04 | Fair-process charter embedding neutrality, notice, separation of duties, appeal routes | §10.4 | Must | Not Started | Document + enforcement in workflows/audit. |
| LEGAL-05 | Anti-retaliation & independent escalation contract rider | §8.5, Appendix F | Must | Done | Template available at `/docs/legal-packs/common/anti-retaliation.md`; route for legal review + tenant adoption. |
| LEGAL-06 | Independent governance model (ethics board, tenant integrity committee, ombuds, security council, AI governance) | §10.5 | Should | Not Started | Document structure, membership, cadence. |
| LEGAL-07 | Jurisdictional packs for EU + common-law markets with local counsel review | §18.4 step 5 | Should | Not Started | Mirror ZA pack pattern. |

## 3. Product Capabilities & Workflows

| ID | Requirement | Doc Ref | Priority | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| PROD-01 | Multi-mode intake (anonymous, confidential, identified) with structured fact capture | Appendix A (Must) | Partial | Anonymous flow exists; confidential/identified flows need backend + policy tie-in. |
| PROD-02 | Conflict challenge for reporters to flag unsafe handlers | §13.3, event `retaliation.concern_reported` | Not Started | Build mailbox action + workflow. |
| PROD-03 | Reporter mailbox with secure messaging, retaliation concern hook | Appendix A Must | Partial | Encrypted threaded mailbox live (at-rest encryption, real reporter JWT auth, read receipts, retaliation concerns, conflict challenges, staff mailbox room). Next: evidence attachments + auto-escalation workflow. |
| PROD-04 | Case lifecycle in Temporal (triage, plan, assignments, findings, decisions, closure) | §13.1, Appendix A Must | Not Started | Temporal not yet adopted; needs backend service rewrite. |
| PROD-05 | Evidence vault (immutable originals, hashes, malware scanning, sanitised working copies, legal hold) | §11.5, §13.2 | Not Started | Implement storage layer + UI. |
| PROD-06 | Protection/safety plans and retaliation follow-up workflow | Appendix A Should | Not Started | No module yet. |
| PROD-07 | Support circle (invite supporters with scoped permissions) | Appendix A Should | Partial | Support invitation UI exists but lacks scoped access enforcement + consent flows. |
| PROD-08 | Board/oversight summaries & regulatory exports | Appendix A Should | Not Started | Build analytics + export engine. |
| PROD-09 | Voice intake / phone channel | Appendix A Could | Not Started | Requires telephony integration. |
| PROD-10 | On-device encrypted journal (opt-in) | Appendix A Could | Not Started | Requires PWA storage redesign. |

## 4. Architecture & Infrastructure

| ID | Requirement | Doc Ref | Priority | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| ARCH-01 | Modular FastAPI monolith with domain packages (intake, cases, evidence, policy, etc.) | §11, Appendix C | Must | Partial | Architecture overview + ADRs drafted; initial service + Alembic scaffolding live under `services/api`. |
| ARCH-02 | PostgreSQL with tenant_id columns, RLS, FORCE ROW LEVEL SECURITY, per-tenant keys | §11.5, §12.1 | Must | Not Started | Implement schema + migrations. |
| ARCH-03 | Temporal for durable workflows | §13.1, ADR-002 | Must | Not Started | Deploy Temporal cluster or cloud, define workflows. |
| ARCH-04 | RabbitMQ for integration events via transactional outbox (optional) | §13.2, §13.4 | Should | Not Started | Set up outbox pattern + event schemas. |
| ARCH-05 | Prefect for AI/data pipelines (redaction, translation, analytics) | §13.3 | Could | Not Started | Add only after core workflows stable. |
| ARCH-06 | Object storage with WORM, versioning, legal hold for evidence | §11.5 | Must | Not Started | Likely S3-compatible with object lock. |
| ARCH-07 | Multi-tier tenancy (shared, dedicated DB, dedicated stack) with per-tenant keys | §12.1 | Should | Not Started | Document design + infra automation. |
| ARCH-08 | Separate identity realms (anonymous, staff, external investigators, platform ops) | §12.2 | Must | Partial | Frontend separation exists; still need separate auth services & vault. |
| ARCH-09 | RBAC + ABAC/ReBAC + conflict graph enforcement | §12.3 | Must | Not Started | Requires policy service + graph DB or adjacency modelling. |
| ARCH-10 | Break-glass workflow with approvals + audit | §12.4 | Must | Not Started | Document + implement. |

## 5. Security, Privacy & Resilience

| ID | Requirement | Doc Ref | Priority | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| SEC-01 | Zero trust posture, OWASP ASVS-aligned SDLC, MFA, PAM | §15.1 | Must | Not Started | Establish SDLC policies + gates. |
| SEC-02 | Privacy threat model (LINDDUN) + STRIDE security model | §§15.2–15.3 | Must | Partial | Draft recorded in `docs/security/threat-model-phase1.md`; expand with diagrams & advisory review. |
| SEC-03 | Incident response playbooks (vendor outage, privacy breach, retaliation) with RTO/RPO targets | §15.4 | Must | Not Started | Add runbooks to `/docs/security/ir`. |
| SEC-04 | Metadata minimisation (no raw narratives in logs/events) | §13.4, ADR-009 | Must | Partial | Logging standards published in `docs/security/logging-standards.md`; tooling enforcement pending. |
| SEC-05 | Encryption envelope (per tenant, per case for highest sensitivity) + customer-managed key option | §11.5, §12.1 | Should | Not Started | Define KMS integration. |
| SEC-06 | Immutable audit log (hash chain, append-only, tamper-evident) | §11.5, §15.1 | Must | Not Started | Could use PostgreSQL + Temporal history + external log store. |
| SEC-07 | Malware scanning / sandbox for uploads | §§11.5, 15.1 | Must | Not Started | Evaluate ClamAV + CDR service. |
| SEC-08 | Privacy notices, consent flows, DSAR tooling | §10.3 | Must | Not Started | Build UI + process. |

## 6. AI, Data & Analytics

| ID | Requirement | Doc Ref | Priority | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| AI-01 | Bound AI gateway with per-use-case controls (writer, anonymity assistant, triage copilot, etc.) | §14.1 | Could (Phase 3) | Not Started | Defer until core architecture ready. |
| AI-02 | Prohibited uses enforced (no credibility scores, discipline, deanonymisation) | §14.2 | Must (policy) | Not Started | Bake into trust charter + AI gateway. |
| AI-03 | NIST AI RMF-aligned governance (impact assessments, model cards, evals) | §14.3 | Should | Not Started | Document process. |
| AI-04 | Prompt-injection and data-leakage guardrails per OWASP GenAI | §14.4 | Should | Not Started | To be implemented with redaction + sandboxing. |
| DATA-01 | Privacy-safe analytics, cohort thresholds, retaliation metrics | §§8.5, 14.1, 18.2 | Should | Not Started | Build analytics service with DP thresholds. |

## 7. KPIs, Validation & GTM

| ID | Requirement | Doc Ref | Priority | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| KPI-01 | Track metrics listed in §18.2 (completion rate, re-engagement, SLA, conflict recusal, retaliation concerns, access violations, etc.) | §18.2 | Should | Partial | Measurement plan in `docs/metrics/kpi-plan.md`; instrumentation + dashboards outstanding. |
| KPI-02 | Avoid misuse metrics listed in §18.3 | §18.3 | Must | Done | Safeguards documented in `docs/metrics/anti-misuse.md`; integrate checks in analytics reviews. |
| KPI-03 | Publish validation reports from pilots (anonymised learnings) | §18.4 | Should | Not Started | Template for future. |
| GTM-01 | Design partner cohort → trust-centred pilot → partnerships → content → regional expansion | §8.5 | Should | Partial | ICP, offer + register templates drafted in `docs/gtm/`; outreach & contracts pending. |
| GTM-02 | Prepare procurement objection responses | §8.6 | Should | Not Started | Sales toolkit referencing platform features. |

## 8. Delivery Plan & Team

| ID | Requirement | Doc Ref | Priority | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| DELIV-01 | Follow 24-month roadmap phases (Discovery, MVP, Enterprise, Responsible AI) | §17.2 | Must | Not Started | Align project plan to phases. |
| DELIV-02 | Staff team roles per §17.3 as funding allows | §17.3 | Should | Not Started | Document hiring plan. |
| DELIV-03 | Track development budget ranges + justification | §17.4 | Informational | Not Started | Use for investor comms. |
| DELIV-04 | Build-vs-buy decisions respected (e.g., use managed OIDC, Temporal, etc.) | §17.5 | Must | Partial | ADR-001…010 drafted; integrate into engineering backlog + infra automation. |

## Maintenance Instructions

1. **Update cadence**: Every feature branch that touches a requirement must update this matrix (status, notes, links). Use PR checklist to enforce.
2. **Traceability**: Reference requirement IDs in commit messages, PR descriptions and ADRs.
3. **Artefact storage**: Legal packs, governance charters, DPIAs, threat models, advisory minutes, etc., belong under `docs/` with matching IDs.
4. **Validation**: Before any pilot/launch milestone, produce a compliance report exporting this table filtered to `Status != Done`.



