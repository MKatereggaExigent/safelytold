# Phase 1 Threat Model – HELP ME Intake & Case Workflow

Methodology: LINDDUN for privacy threats + STRIDE for security threats. Scope limited to reporter portal, API intake, storage, Temporal workflow, staff access.

## Assets
- Reporter identity (optional) + sealed narratives
- Case metadata, evidence files
- Assignment/conflict graph
- Break-glass logs

## Adversaries
- Malicious insider (tenant staff)
- Compromised platform admin / operator
- External attacker (credential stuffing, injection)
- Malicious reporter/subject (false reports, retaliation)

## LINDDUN Summary
| Threat | Example | Mitigations |
| --- | --- | --- |
| Linkability | Correlate two anonymous reports via IP/device | Use separate domains, drop long-lived cookies, rate-limit per reporter handle |
| Identifiability | Metadata (EXIF, email headers) reveals reporter | Strip metadata on upload, preview risk indicators |
| Non-repudiation | Logs tie report to shared workstation | Neutral UI, minimal logging, opt-in local journal |
| Detectability | Employer knows user accessed HELP ME | Provide external access, encourage personal devices, disable trackers |
| Disclosure | Tenant admin browses unrelated cases | Enforce RLS + policy engine, audit + alerts |
| Unawareness | Reporter doesn’t know who sees identity | Layered notices, mode comparison, consent receipts |
| Non-compliance | Retention/export breaches | Configurable retention + legal packs |

## STRIDE Summary
| Threat | Example | Mitigation |
| --- | --- | --- |
| Spoofing | Attacker impersonates investigator | MFA, SCIM-driven provisioning, signed invitations |
| Tampering | Evidence altered | Hashes, sealed originals, object lock |
| Repudiation | Handler denies viewing case | Tamper-evident audit chain |
| Information Disclosure | Cross-tenant access, log leaks | FORCE RLS, encryption, ADR-009 logging rules |
| DoS | Flood anonymous intake | Privacy-preserving rate limits, CAPTCHA alternative |
| Elevation of Privilege | Tenant admin grants self access | Separation of duties, JIT approvals |

## Open Questions
- Threat modeling of AI gateway interactions (Phase 2).
- Additional jurisdictions with stricter metadata rules.
