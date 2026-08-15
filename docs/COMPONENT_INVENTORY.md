# Proposal-to-repository component inventory

This inventory maps every major component in the product and architecture proposal to a repository location. A checked item means a foundation or reference implementation exists; it does not mean production completion.

## Experience layer

| Proposal component | Repository |
|---|---|
| Anonymous/verified-anonymous/confidential/identified reporting | `apps/reporter-web`, `services/intake_service` |
| Private journal / save-before-submit concept | `services/intake_service` extension point |
| Protected two-way mailbox | `apps/reporter-web/app/mailbox`, `services/mailbox_service` |
| Staff triage and case workbench | `apps/staff-web`, `services/case_service` |
| Investigation, interviews, findings, remedies, appeals | `services/investigation_service` |
| Protection plans and retaliation check-ins | `services/protection_service`, Temporal workflow |
| Support circle and referrals | `services/support_service` |
| Aggregate executive/board reporting | `services/analytics_service`, staff analytics page |
| Public trust and transparency centre | `apps/trust-center-web` |
| Multilingual/accessibility extension | Web app i18n/accessibility backlog and AI translation capability |

## Identity and authorisation

| Component | Repository |
|---|---|
| Anonymous reporter realm | `services/reporter_identity_service` |
| Confidential identity vault | physically separate `postgres-vault`, reporter identity service |
| Staff identity and SCIM linkage | `services/identity_service`, Keycloak reference |
| External investigator/ombuds realm | staff roles and policy contracts |
| Platform operations realm | platform role and production IAM ADR |
| RBAC | Keycloak roles and policy service |
| ABAC / purpose binding | policy service and OPA policy |
| ReBAC / assignment / conflict graph | policy service and Temporal assignment gate |
| Dual approval for identity access | policy service, OPA and privacy console |
| Just-in-time and break-glass | policy service extension and runbook |
| Separation of duties / recusal | policy service and role matrix |

## Domain services

| Bounded context | Service |
|---|---|
| Tenancy, legal entities, regions, organisational units | `tenancy_service` |
| Staff identity, roles and invitations | `identity_service` |
| Pseudonymous reporter handle / identity vault | `reporter_identity_service` |
| Policy and authorisation | `policy_service` |
| Report intake | `intake_service` |
| Reporter mailbox | `mailbox_service` |
| Cases, allegations, parties, triage and assignment | `case_service` |
| Investigation plans, interviews, findings, decisions and appeals | `investigation_service` |
| Evidence, sealed originals, copies, holds and manifests | `evidence_service` |
| Protection and retaliation | `protection_service` |
| Support/referral consent | `support_service` |
| De-identified analytics | `analytics_service` |
| HRIS, SCIM, EAP, regulator and webhook adapters | `integration_service` |
| Privacy-safe outbound notices | `notification_service` |
| Consent, DSAR, retention, residency and breach handling | `privacy_service` |
| Append-only audit | `audit_service` |
| Security alerting and privacy incidents | `security_monitor_service` |
| Governed model/provider boundary | `ai_gateway` |
| Merkle batching and integrity anchoring | `blockchain_ledger_service`, `blockchain/` |

## Platform components

| Component | Repository |
|---|---|
| API gateway / façade | `api_gateway` |
| PostgreSQL database per service | Compose and Terraform module interfaces |
| PostgreSQL RLS | `infrastructure/postgres/rls_reference.sql` |
| S3-compatible evidence storage | MinIO in Compose; object-storage Terraform interface |
| Malware scanning | ClamAV container and evidence pipeline extension |
| Temporal | `workers/workflow_worker`, Compose |
| RabbitMQ quorum queues | `workers/outbox_relay`, event consumer, RabbitMQ config |
| Transactional outbox | shared `OutboxEvent`, relay worker |
| Prefect | `workers/prefect_flows`, optional Compose profile |
| OpenTelemetry, Prometheus, Tempo, Loki, Grafana | `infrastructure/observability` |
| OIDC and SCIM | Keycloak reference and integration service |
| OPA policy decision point | `infrastructure/opa` |
| Kubernetes/Helm | `helm/safelytold` |
| Terraform/IaC | `terraform/` |
| CI security and contract validation | `.github/workflows`, `scripts/validate_foundation.py` |
| Jurisdiction policy packs | `legal-packs/` |

## Event contracts

All proposal events are present under `contracts/events`, including case reporting, conflict detection, acknowledgement, evidence receipt/sanitisation, assignment change, finding, closure, retaliation concern and privacy/security incident. Additional support, delivery-failure and ledger-anchor events are included.

## AI capabilities and exclusions

The nine bounded capabilities appear in `ai_gateway` and Prefect governance: reporter writing, anonymity scan, triage copilot, chronology, policy retrieval, investigation summary, translation, pattern analytics and SLA/remediation support. Prohibited scoring and automated employment decisions are encoded in the gateway and trust charter.

## Evidence and security

The foundation includes SHA-256 evidence receipts, sealed/working/redacted copy types, legal-hold state, append-only audit hashing, privacy-safe logs/events, data classification, HSM/KMS architecture, incident and break-glass runbooks, STRIDE/LINDDUN starter model, and optional Merkle-root blockchain anchoring.
