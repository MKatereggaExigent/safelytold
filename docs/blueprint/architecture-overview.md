# Target Architecture Overview

Derived from proposal §§11–16. This document complements ADRs 001–010.

## High-Level Components

1. **Frontends (Next.js / React)**
   - Anonymous Reporter Portal (`apps/reporter-web`), with journal, HELP ME intake, mailbox, trust centre.
   - Staff Workspace (`apps/staff-web`) for triage, investigations, evidence, protection.
   - Strict separation of identity realms, assets, telemetry.

2. **API Layer (FastAPI modular monolith)**
   - Domain packages: tenancy, identity, policy, intake, case, investigation, evidence, protection, analytics, integration.
   - REST + Webhooks; future GraphQL considered later.
   - RLS-enforced PostgreSQL, outbox table, Temporal worker integration.
   - Phase 1 scaffolding lives in `services/api` with Alembic migrations and public intake endpoint.

3. **Workflow & Tasks**
   - Temporal for durable human workflows (report intake, triage SLA, retaliation check-ins).
   - Prefect for derived pipelines (redaction, translation, analytics).
   - RabbitMQ optional event bus fed by transactional outbox.

4. **Storage**
   - PostgreSQL cluster with tenant_id, FORCE RLS, row/page encryption.
   - Object storage (S3-compatible) with immutable originals + working copies for evidence.
   - Separate identity vault database/schema for confidential reporters.

5. **Security & Governance**
   - Zero-trust access, OIDC/SAML for staff, reporter secrets for anonymous, SCIM for lifecycle.
   - Policy engine enforcing RBAC+ABAC+conflict graph.
   - Audit subsystem (hash-chained events, break-glass log).

6. **AI Gateway**
   - Bounded agents (writer, translation, chronology) behind policy enforcement.
   - Provider-agnostic; no raw case data leaves boundary without redaction.

## Data Flow Summary

1. Reporter submits HELP ME form → Next.js encrypts sealed narrative → FastAPI intake stores data + triggers Temporal workflow.
2. Intake writes case + allegations → outbox emits `case.reported` → RabbitMQ (optional) + Prefect.
3. Staff actions via workspace hit FastAPI, which checks policy service (RBAC/ABAC) + RLS → updates Postgres.
4. Evidence upload pipeline writes sealed original to object storage, working copy to sanitized bucket, metadata to Postgres.
5. Retaliation plan + check-ins scheduled via Temporal timers.
6. Analytics/reporting use Prefect to process de-identified aggregates, respecting thresholds.

## Infrastructure Considerations

- Environment parity: local (docker compose), staging, prod (per-tenant tier selection).
- Secrets via managed KMS + secrets manager; per-tenant keys tracked in control plane.
- Observability stack (OpenTelemetry, Loki/Tempo/Prometheus) configured per ADR-009 (no raw content).
- Deployment automation via IaC (Terraform/Kubernetes) – separate backlog item.

_Diagrams to be added once tooling selected._
