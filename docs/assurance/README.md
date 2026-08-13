# SafelyTold security, privacy and compliance assurance pack

Document owner: Security & Privacy Lead  
Approval owners: DPO, CISO/technical security owner, Head of Operations  
Review cadence: quarterly and after material architecture, supplier or legal change  
Last updated: 12 August 2026

This pack is the due-diligence entry point for clients, investors, auditors and partners. It explains
SafelyTold's control design, implemented evidence, shared responsibilities and remaining assurance work.
It is not legal advice and does not claim certification where none has been awarded.

## Assurance position

| Topic | Current position |
|---|---|
| GDPR | Control architecture supports core GDPR obligations; controller/processor roles, lawful basis, records schedule, transfer assessment and DPO approval remain tenant/jurisdiction-specific. SafelyTold is not described as “GDPR certified.” |
| POPIA | South African privacy baseline and draft DPIA exist; Information Officer/DPO approval, operator agreements and production evidence remain required before processing real allegations. |
| SOC 2 | Controls are being designed and evidenced against Security, Availability, Confidentiality and Privacy criteria. No SOC 2 Type I or Type II report has yet been issued. |
| ISO 27001 | Architecture and policies support an ISMS roadmap. SafelyTold is not currently represented as ISO 27001 certified. |
| Penetration testing | Independent production-scope test and closure of high-severity findings remain launch gates. |
| Production readiness | Source validation passes, but the strict evidence gate remains authoritative: run `make production-ready`. |

## Documents

1. [Security and trust architecture](security-and-trust-architecture.md)
2. [Privacy: GDPR and POPIA mapping](privacy-gdpr-popia.md)
3. [SOC 2 readiness matrix](soc2-readiness.md)
4. [Risk register and treatment](risk-register.md)
5. [Client shared-responsibility model](shared-responsibility.md)
6. [Evidence register](evidence-register.md)
7. [SaaS tenancy and customer overlays](saas-tenancy-and-customer-overlays.md)

Supporting technical sources include `docs/security/`, `docs/privacy/`, `docs/operations/`, ADRs,
event contracts, infrastructure configuration and automated tests. Evidence marked **implemented** means
the control exists in source and has local automated validation. **Verified** is reserved for approved
production-environment evidence. **External** requires independent assurance, a supplier or a human
operating record.

## Safe claims for commercial use

- “SafelyTold uses a separate reporter identity vault and purpose-bound staff access.”
- “Tenant isolation is enforced in application queries and designed for PostgreSQL row-level security.”
- “Raw allegations and reporter identities are prohibited from logs, events, analytics and blockchain.”
- “Staff authentication uses OIDC, MFA and role claims; case access additionally depends on tenant,
  assignment, purpose, conflict state and approvals.”
- “SafelyTold maintains a GDPR/POPIA control mapping and SOC 2 readiness programme.”

Do not say “GDPR compliant,” “POPIA certified,” “SOC 2 compliant,” “ISO certified,” “unhackable,” or
“guaranteed anonymous” without current legal or independent assurance evidence approving that exact claim.
