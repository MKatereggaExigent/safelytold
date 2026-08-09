# Non-functional requirements

- Privacy: minimisation, purpose limitation, separate identity vault, regional processing, retention/hold and tenant exit.
- Security: OWASP ASVS target, FIDO2 MFA, zero trust, JIT, HSM/KMS, secure SDLC, SBOM and external tests.
- Accessibility: WCAG 2.2 AA, keyboard, screen reader, contrast, low-literacy, low-bandwidth and assisted reporting.
- Internationalisation: Unicode, locale-aware dates, RTL support, translation review and language-specific legal notices.
- Performance: public intake first contentful load target under 2.5 seconds on typical mobile; normal API p95 target under 500 ms excluding file/AI jobs.
- Reliability: idempotent APIs/consumers, durable workflows, multi-zone operation, tested restore and graceful AI degradation.
- Auditability: immutable access/decision records, policy versions, AI provenance and signed export manifests.
- Maintainability: typed contracts, migrations, tests, ADRs, feature flags and bounded ownership.
- Portability: containers, IaC, provider adapters and complete tenant export/exit.
