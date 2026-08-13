# SOC 2 readiness matrix

SafelyTold has not received a SOC 2 report. This matrix supports readiness and evidence collection; it is
not an attestation. A licensed independent CPA/audit firm determines scope and issues Type I/Type II reports.

| Trust Services area | Control family | Repository evidence | Current gap |
|---|---|---|---|
| Security (CC1–CC2) | Ethics, governance, roles, communication | Trust charter, role matrix, governance model | Approved policies, board oversight records, training evidence |
| Security (CC3) | Risk assessment | STRIDE/LINDDUN models, risk register, DPIA | Independent review and periodic operational assessment |
| Security (CC4) | Monitoring | Security monitor, OpenTelemetry, Prometheus/Loki/Grafana | Production alerts, review tickets and retained evidence |
| Security (CC5) | Control activities | Policy service, approvals, separation of duties | Sampled operating-effectiveness evidence |
| Security (CC6) | Logical/physical access | Keycloak MFA/OIDC, RBAC+ABAC, vault approvals, RLS | IdP/PAM production evidence and quarterly access review |
| Security (CC7) | System operations | Malware scanning, audit, incident runbooks | Vulnerability SLAs, incident exercise and response records |
| Security (CC8) | Change management | Git, CI checks, tests, ADRs, IaC | Protected branches, approvals, deployment evidence, SBOM/signing |
| Security (CC9) | Risk mitigation/vendors | Supplier requirements and shared responsibility | Vendor inventory, due diligence, DPAs, SOC reports, exit tests |
| Availability (A1) | Capacity, resilience, recovery | SLOs, IaC, backups/recovery design, continuity workflow | Load tests, multi-zone proof, restore/failover evidence |
| Confidentiality (C1) | Classification, access, encryption, disposal | Classification, vault, keys, retention/legal hold | KMS/HSM proof, disposal/crypto-erasure evidence |
| Privacy (P1–P8) | Notice, choice, collection, use, retention, access, disclosure, quality, monitoring | Trust centre, intake modes, DPIA, DSAR/privacy services | Approved notices, RoPA, request exercise, complaint/monitoring evidence |

## Audit preparation sequence

1. Define system description, boundaries, services, people, locations and subservice organisations.
2. Approve policies and control owners; map controls to criteria with IDs.
3. Complete risk assessment, vendor due diligence, data inventory and information asset register.
4. Remediate production hardening, pen-test and recovery findings.
5. Operate controls and retain evidence: access reviews, changes, incidents, alerts, training, backups,
   vendor reviews and policy approvals.
6. Conduct readiness assessment, then Type I design assessment if desired.
7. Establish Type II observation period only when controls consistently operate.

Evidence must be timestamped, attributable, protected from alteration and sampled across the audit period.

