# Production hardening checklist

- Replace all development passwords, bypasses and local identity configuration.
- Use private subnets, egress allowlists, service mesh or workload mTLS, WAF and DDoS controls.
- Separate cloud accounts/projects for identity vault, audit, production workloads and security logs.
- Use managed PostgreSQL with PITR, TLS, RLS migrations, non-owner application roles and connection pooling.
- Use immutable object storage with retention lock and legal-hold APIs.
- Sign images, generate SBOMs, enforce provenance, scan IaC, dependencies and containers.
- Apply Kubernetes restricted pod security, default-deny network policies and read-only filesystems.
- Enforce FIDO2 MFA, short sessions, device posture where lawful, PAM and JIT elevation.
- Run accessibility, localisation, privacy, penetration, red-team and disaster-recovery tests.
- Complete DPIA, records schedule, transfer assessment and jurisdiction legal sign-off.
