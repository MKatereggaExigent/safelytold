# Proposal implementation audit

Source: `work_politics_cop_feasibility_product_business_architecture_proposal.docx`, version 1.0,
5 August 2026. Audit date: 12 August 2026.

Status meanings: **Implemented** has executable code and tests; **Partial** has a working subset;
**External** requires people, contracts or independent assurance; **Later phase** is explicitly Could/
Phase 2–3 in the proposal and is not an MVP launch claim.

## Product and MVP

| Proposal capability | Status | Executable evidence / remaining gap |
|---|---|---|
| Private journal | Partial | Reporter journal UI exists; durable on-device encrypted storage is later phase. |
| Anonymous/confidential/identified intake | Implemented | Reporter intake, separate vault identity and pseudonymous recovery session. |
| Reporter mailbox | Implemented | Encrypted two-way mailbox, read state, conflict and retaliation actions. |
| Conflict-safe routing | Implemented | Policy decisions, conflict events, assignment/recusal case logic. |
| Case and investigation lifecycle | Implemented | Case service, investigation service surface and Temporal workflows. |
| Evidence vault | Implemented | Sealed uploads, hashes, scanning, sanitised copies, legal holds and manifests. |
| Anti-retaliation | Implemented | Protection workflow, mailbox concerns and escalation events. |
| Support circle | Partial | Support service and UI exist; all invitation/consent/revocation paths need end-to-end acceptance tests. |
| Audit and integrity | Implemented | Append-only hash chain, Merkle batches and optional EVM anchoring. |
| Policy notices/legal packs | Partial | Versioned packs and policy service exist; local counsel approval is external. |
| Basic exports/board reporting | Implemented | Thresholded analytics and management-report endpoints. |
| Security monitoring | Implemented | Security monitor service, privacy-safe telemetry stack and runbooks. |

## Enterprise and responsible-AI scope

| Proposal capability | Status | Executable evidence / remaining gap |
|---|---|---|
| Staff OIDC/MFA | Implemented | Keycloak realm and verified JWKS access tokens. Production identity-provider configuration is external. |
| SCIM and HRIS relationship sync | Partial | Connector configuration/domain surface exists; provider-specific adapters are not implemented. |
| Dedicated database/stack and residency | Partial | Terraform tenancy tiers and deployment modules exist; multi-region production proof is external. |
| Voice/hotline | Partial | Hotline lifecycle, privacy rules, coverage and continuity logic plus staff console exist; carrier adapter/number is external. |
| External investigator/ombuds access | Partial | Scoped invitation model exists; complete invitation identity flow remains. |
| Multilingual UI | Partial | Reporter portal has broad translation; staff/trust coverage remains incomplete. |
| AI gateway and human approval | Implemented | Bounded capabilities, prohibited purposes, provenance and explicit review. |
| Translation/redaction/chronology/policy retrieval/summaries | Implemented | AI gateway capabilities and Prefect flows. Production model evaluation is external. |
| Differential privacy | Later phase | Minimum cohort suppression is enforced; formal DP noise/accounting is not implemented. |
| Customer-managed keys/sovereign deployment | Later phase | Key-management and Terraform abstractions exist; provider-specific CMK lifecycle remains. |
| Ombuds marketplace | Later phase | Not implemented; explicitly Could/Phase 3. |

## Non-functional requirements

| Requirement | Status | Remaining proof |
|---|---|---|
| Tenant isolation/RLS | Implemented | RLS application and tenant-scoped queries; independent penetration test remains external. |
| Identity separation | Implemented | Separate reporter vault database and staff realm. |
| Idempotency/durable workflows/outbox | Implemented | Idempotency keys, Temporal and transactional outbox. |
| Accessibility WCAG 2.2 AA | Partial | Semantic/component foundation exists; independent audit and remediation remain. |
| Performance p95/FCP targets | External | Requires production-like load and mobile tests. |
| Backup/restore/multi-AZ | Partial | IaC and drill workflow exist; successful target-environment drills are external. |
| SBOM/ASVS/penetration testing | Partial | Secure-SDLC artefacts exist; independent test and signed closure are external. |
| Migrations for every service | Partial | Several services still rely on development `create_all`; production migrations are required. |

## Non-software exit criteria

These cannot be truthfully implemented in source code: research participant interviews; three paid design
partners; advisory-group membership; local-counsel approval; carrier/call-centre contracts; staffed 24/7
rotas; SOC 2/ISO certification; independent accessibility/privacy/security testing; and completed live
continuity exercises. Their evidence is enforced by `config/production-readiness.yaml` and the strict
`make production-ready` gate.

## Audit conclusion

The protected reporter intake, mailbox, evidence, audit and identity-vault foundations are implemented,
but the entire MVP and 24-month proposal are **not** complete. As of 12 August 2026, case, investigation,
protection, support, privacy, identity and security-monitoring domains still include generic record
scaffolding and lack versioned production migrations. They must not be represented as completed merely
because domain models or target API catalogues exist. The executable gate
`scripts/check_implementation_readiness.py` fails until those scaffolds and migration gaps are removed.

Other gaps include provider-specific SCIM/HRIS/voice adapters, complete external-investigator identity
flows, full staff/trust i18n, WCAG remediation and later-phase differential privacy/CMK/marketplace
capabilities. Production deployment remains gated until software and external exit criteria have evidence.
# Implementation status update — 13 August 2026

All services designated as proposal-critical in `config/implementation-readiness.yaml` now use explicit domain models and workflows rather than the shared generic record router. Versioned executable migrations exist for case management, investigations, protection, support, privacy, identity, security monitoring, analytics and integration operations. The implementation gate reports zero code blockers.

This does not constitute permission to launch. The strict production gate remains authoritative for provider activation, production-environment exercises and independent/accountable-person evidence, including the live toll-free and mailbox channels, 24/7 staffing, penetration testing, recovery exercises, training and formal approvals.
