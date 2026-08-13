# Security, privacy and operational risk register

Scoring: likelihood and impact 1–5; inherent score is L×I before controls. Residual ratings require formal
owner approval and production evidence.

| Risk | Inherent | Principal controls | Residual/evidence status | Owner |
|---|---:|---|---|---|
| Reporter deanonymisation | 25 | Optional identity, separate realm/vault, metadata minimisation, sanitisation, notices | High until external privacy red-team | DPO |
| Cross-tenant disclosure | 25 | Tenant claims, scoped queries, RLS/FORCE RLS, policy checks | Medium design; production negative tests required | Security Engineering |
| Privileged insider access | 25 | No standing case access, purpose, assignments, dual approval, break glass, audit | High until PAM/JIT and review evidence | CISO |
| Evidence tampering/loss | 20 | Sealed originals, SHA-256, scan, legal hold, manifests, audit/Merkle | Medium; WORM/restore proof required | Evidence Custodian |
| Credential compromise | 20 | OIDC, MFA, PKCE, short sessions, verified email, no self-registration | Medium; phishing-resistant MFA/PAM planned | Identity Owner |
| Retaliation following report | 25 | Conflict routing, protection plans, secure mailbox, escalation, independent channels | High human/organisational residual | Tenant Ethics Owner |
| Sensitive data in logs/events | 20 | Forbidden-field validators, metadata-only contracts, disabled proxy access logs | Medium; production log audit/DLP required | SRE/Privacy |
| Malicious uploads | 16 | Size/type controls, ClamAV, sealed quarantine, sanitised copies | Medium; sandbox/CDR supplier review required | Security Engineering |
| AI leakage/adverse decision | 20 | Redacted input, prohibited purposes, provider gateway, provenance, human approval | Medium; model evaluations and supplier terms required | AI Governance Owner |
| Availability/DoS | 16 | Stateless services, queues, workflow replay, monitoring, continuity plans | High until multi-zone/load/failover tests | SRE |
| Supplier/call-centre compromise | 20 | DPA, signed webhook, replay window, least privilege, deletion/audit clauses | High until supplier contracted/tested | Procurement/DPO |
| Regulatory non-compliance | 20 | Legal packs, DPIA, notices, DSAR, retention, breach workflow | High until local counsel/DPO approval | Legal/DPO |

Risk acceptance cannot be performed by engineering alone. High residual risks require the named owner and
executive/governance approval, with expiry and treatment plan.

