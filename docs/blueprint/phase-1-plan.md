# Phase 1 – Discovery & Design Partner Foundations

Source reference: Feasibility/Product/Architecture proposal (§17 Discovery phase, §18 validation, Appendix F). This plan spans the first ~3 months and covers non-negotiable discovery tasks before locking the production build.

## Objectives

1. Validate problem/solution fit with employees, handlers, investigators and legal/privacy stakeholders (per §18.4).
2. Establish trust/governance artefacts: trust charter, prohibited uses, independent advisory group, anti-retaliation commitments.
3. Produce the South African legal/privacy pack (baseline jurisdiction) and templates for additional markets.
4. Recruit and contract 3+ paid design partners with independent escalation and governance commitments.
5. Prototype the anonymous/intake journey, conflict routing and mailbox flow for usability tests.
6. Deliver initial threat model, DPIA, and architecture decision records to support Phase 2 engineering.

## Workstreams & Tasks

### Stage 0 – Secondary Evidence Discovery (Weeks 0–2)

| ID | Task | Owner | Timing | Deliverable |
| --- | --- | --- | --- | --- |
| R0.1 | Harvest published benchmarks (ILO/Gallup, NAVEX, ACFE, TI, regulator data) | Research lead | Week 1 | `docs/research/secondary-evidence.md` |
| R0.2 | Compile case-law scenarios (Kunene, Modika, Pillay, etc.) | Research lead | Week 1 | `docs/research/case-scenarios.md` |
| R0.3 | Map harassment Code remote-work contexts + taxonomy implications | Legal + Product | Week 1 | Update `legal-packs/za/requirements.md` + taxonomy backlog |

### 1. Research & Validation (Primary)

| ID | Task | Owner | Timing | Deliverable |
| --- | --- | --- | --- | --- |
| R1 | Interview ≥15 employees/reporters who raised workplace harm | Research lead | Weeks 3–6 | Interview notes + anonymised insights in `/docs/research/interviews-employees.md` |
| R2 | Interview ≥10 corporate handlers/compliance officers | Research lead | Weeks 3–6 | `/docs/research/interviews-handlers.md` |
| R3 | Interview ≥5 investigators/ombuds + ≥5 labour/privacy lawyers + ≥5 employee representatives | Research lead | Weeks 4–7 | Separate notes per cohort |
| R4 | Prototype anonymous intake, conflict challenge, mailbox + run usability tests across languages/disabilities | Product + Design | Weeks 5–8 | Prototype screens + usability findings (`/docs/research/prototype-testing.md`) |
| R5 | Conduct privacy red-team exercise: attempt deanonymisation from metadata/logs | Security lead | Weeks 6–7 | Findings + mitigations (`/docs/security/redteam-intake.md`) |

### 2. Trust & Governance

| ID | Task | Owner | Timing | Deliverable |
| --- | --- | --- | --- | --- |
| T1 | Draft trust charter + tenant prohibited-use addendum (no deanonymisation, no retaliation, etc.) | Product + Legal | Week 2 | `/docs/trust/charter.md` |
| T2 | Form independent advisory group (employee voice, labour law, privacy, investigations, psychology, union, security) | Founder | Week 3 | `/docs/trust/advisory/charter.md` + member bios |
| T3 | Schedule monthly advisory sessions; record minutes + decisions | Founder | Ongoing | `/docs/trust/advisory/minutes-YYYYMM.md` |
| T4 | Draft anti-retaliation commitments + independent escalation clauses for pilots | Legal | Week 4 | Template rider in `/legal-packs/common/anti-retaliation.md` |
| T5 | Publish trust-centre content plan (access logs, governance, escalation) | Product Marketing | Week 6 | `/docs/trust/centre-content.md` |

### 3. Legal, Privacy & Compliance

| ID | Task | Owner | Timing | Deliverable |
| --- | --- | --- | --- | --- |
| L1 | Map South African laws (PDA, EEA, LRA, POPIA, harassment Code) to product requirements | Legal (ZA counsel) | Weeks 2–5 | `/legal-packs/za/requirements.md` |
| L2 | Draft POPIA security compromise workflow + notification templates | Legal + Security | Week 5 | `/docs/security/ir/popia-breach.md` |
| L3 | Prepare DPIA / privacy impact assessment for MVP | DPO | Week 6 | `/docs/privacy/dpia-mvp.md` |
| L4 | Outline EU + common-law legal-pack template for Phase 2 localisation | Legal | Week 7 | `/legal-packs/template/` |
| L5 | Document fair-process charter (notice, neutrality, appeal) | Legal + Product | Week 5 | `/docs/trust/fair-process-charter.md` |

### 4. Design Partner Recruitment

| ID | Task | Owner | Timing | Deliverable |
| --- | --- | --- | --- | --- |
| P1 | Define ideal customer profile (sector, size, risk profile) for design partners | GTM lead | Week 2 | `/docs/gTM/design-partner-ICP.md` |
| P2 | Develop pilot offer deck + selection criteria | GTM + Founder | Week 3 | `/docs/gTM/design-partner-offer.pdf` |
| P3 | Secure 3 paid design partners with signed anti-retaliation + independent escalation commitments | Founder | Weeks 4–8 | Executed agreements (stored securely) + summary in `/docs/gTM/design-partner-register.md` |
| P4 | Define evaluation plan + anonymised lessons report template | Product | Week 6 | `/docs/gTM/pilot-evaluation-template.md` |

### 5. Technical Foundations & Threat Modelling

| ID | Task | Owner | Timing | Deliverable |
| --- | --- | --- | --- | --- |
| A1 | Produce high-level architecture map (React/Next + FastAPI monolith + Temporal + Postgres + S3 + RabbitMQ + Prefect) | Tech lead | Week 2 | `/docs/blueprint/architecture-overview.svg` |
| A2 | Draft ADRs 001–010 (from Appendix D) with current decisions | Tech lead | Weeks 2–4 | `/docs/adr/ADR-001.md` … `/docs/adr/ADR-010.md` |
| A3 | Conduct initial threat model (LINDDUN + STRIDE) for intake/case workflow | Security lead | Week 5 | `/docs/security/threat-model-phase1.md` |
| A4 | Define logging/observability guardrails (no raw narratives) | Security + Backend | Week 6 | `/docs/security/logging-standards.md` |
| A5 | Plan data architecture & entity model (table relationships per §16) | Backend | Week 6 | `/docs/blueprint/data-model.md` |

### 6. Metrics & KPIs

| ID | Task | Owner | Timing | Deliverable |
| --- | --- | --- | --- | --- |
| M1 | Define measurement plan for §18.2 metrics (completion rate, recusal, etc.) | Product Analytics | Week 7 | `/docs/metrics/kpi-plan.md` |
| M2 | Document safeguards against misusing metrics (§18.3) | Product Analytics | Week 7 | `/docs/metrics/anti-misuse.md` |

## Milestones

| Milestone | Target date | Criteria |
| --- | --- | --- |
| M0 – Kickoff | Week 0 | Requirements matrix + phase plan approved |
| M1 – Trust charter & advisory | Week 3 | TRUST-01/02/03 deliverables published |
| M2 – Research complete | Week 6 | R1–R5 finished; usability report + red-team findings logged |
| M3 – Legal pack & DPIA | Week 7 | L1–L5 deliverables in repo; DPIA signed off |
| M4 – Design partners signed | Week 8 | ≥3 pilot contracts executed (summary logged) |
| M5 – Architecture & threat model | Week 8 | ADRs drafted, architecture diagram, threat model, data model docs |
| M6 – Phase 1 closure | Week 12 | All phase tasks done + retrospective doc |

## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Access to sensitive interviewees is limited | Medium | Leverage advisory network, offer anonymity, provide informed-consent forms |
| Legal/dpo reviews delayed | High | Pre-book counsel, prioritise legal pack tasks early |
| Design partners hesitant without demo | Medium | Use prototype and trust charter to build confidence, include independent escalation promises |
| Advisory board formation delayed | Medium | Start outreach in Week 1, use interim advisors if needed |
| Security/privacy docs lack detail | Medium | Assign dedicated security lead, use LINDDUN/STRIDE templates |

## Reporting & Updates

- Weekly status update in `/docs/blueprint/status-weekNN.md` summarising progress, blockers and next steps.
- Requirements matrix (`docs/blueprint/requirements-matrix.md`) updated as tasks complete.
- Retrospective at end of Phase 1: what validated, what pivoted, readiness for Phase 2.
