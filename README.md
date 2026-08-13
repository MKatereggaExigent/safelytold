# safelytold — foundational platform

A privacy-first, multi-tenant workplace integrity platform for safe reporting, fair investigation, anti-retaliation safeguards, evidence integrity and accountable remediation.

> **Foundation, not a production release.** This repository supplies deployable service boundaries, representative APIs, contracts, workflows, security controls, infrastructure templates and tests. Legal rules, production cryptography, identity integration, data residency, accessibility, threat-model validation and operational controls require qualified specialists before real people or reports are onboarded.

## Product boundaries

The platform supports fair process. It does **not** determine truth, guilt, credibility, employability, promotion, dismissal, mental health or reputation. AI output is advisory, redacted, source-linked and human-reviewed. Blockchain is used only for integrity commitments—never as a case or identity store.

## Architecture at a glance

- Three Next.js applications: reporter portal, staff operations and public trust centre.
- FastAPI microservices, each with its own data ownership boundary. A new modular monolith (`services/api`) now hosts the SafelyTold intake and core domain model as described in `docs/blueprint/architecture-overview.md`.
- Separate reporter identity vault and separate append-only audit store.
- PostgreSQL row-level security as defence in depth within tenant-bearing databases.
- Temporal for authoritative long-running case workflows.
- RabbitMQ for privacy-safe events, integration fan-out and notifications.
- Prefect for governed AI/data/retention pipelines, never authoritative case state.
- S3-compatible immutable evidence storage, malware scanning and derivative-copy workflow.
- RBAC + ABAC + relationship/conflict rules + purpose binding + dual approval.
- OpenTelemetry observability with privacy filters.
- Optional Hyperledger Besu/QBFT integrity anchoring using Merkle roots only.

See [`docs/COMPONENT_INVENTORY.md`](docs/COMPONENT_INVENTORY.md) for proposal-to-code traceability.

The source proposal is retained at [`docs/reference/safelytold_feasibility_product_business_architecture_proposal.docx`](docs/reference/safelytold_feasibility_product_business_architecture_proposal.docx). Generation-time checks and explicit validation limitations are recorded in [`BUILD_VALIDATION.md`](BUILD_VALIDATION.md).

## Start locally

Prerequisites: Docker Compose v2, 16 GB+ RAM recommended, or run a reduced subset.

```bash
cp .env.example .env
docker compose up --build postgres-core postgres-vault postgres-audit rabbitmq temporal-postgres temporal temporal-ui minio keycloak opa
docker compose up --build api-gateway tenancy-service reporter-identity-service intake-service case-service evidence-service audit-service
```

Then open:

- Reporter portal: `http://localhost:3000`
- Staff portal: `http://localhost:3001`
- Trust centre: `http://localhost:3002`
- API gateway docs: `http://localhost:8000/docs`
- Temporal UI: `http://localhost:28088`
- RabbitMQ: `http://localhost:25673`
- MinIO: `http://localhost:29011`

Infrastructure services use a dedicated high port range (`2xxxx`) so the stack can run alongside other apps (e.g. CryptoSqan) on the same server. The only fixed entry ports are `8100` (frontend), `8101` (API) and `8080` (Keycloak).

The Compose default is secure: `DEV_AUTH_BYPASS=false` and `NEXT_PUBLIC_DEV_AUTH=false` (verified OIDC/JWKS required). Set them to `true` **only** for local development — they bypass authentication entirely and must never be enabled outside a trusted dev environment.

Optional local blockchain:

```bash
docker compose -f docker-compose.blockchain.yml up --build
```

## Repository map

```text
apps/                    Reporter, staff and trust-centre web applications
services/                Independently deployable FastAPI bounded contexts
    api/                 SafelyTold platform monolith (Phase 1 scaffolding, Alembic, public intake)
workers/                 Temporal, outbox, RabbitMQ and Prefect workers
packages/                 Narrow shared Python and TypeScript packages
contracts/                JSON Schema and AsyncAPI event contracts
blockchain/               Solidity integrity contract and Besu reference
infrastructure/           Docker, PostgreSQL, OPA, Keycloak and observability
helm/                     Kubernetes umbrella chart
terraform/                Cloud-neutral module interfaces and environments
docs/                     Architecture, security, governance and decisions
legal-packs/              Jurisdiction configuration scaffolds
runbooks/                 Operational and security response procedures
tests/                    Unit, privacy-contract and architecture tests
scripts/                  Validation, development and integrity utilities
```

## Development checks

```bash
python -m compileall packages services workers scripts tests
python scripts/validate_foundation.py
python scripts/check_production_readiness.py
pytest
```

Before approving production, run `make production-ready`. This strict gate intentionally fails until
every SafelyTold SaaS operational and external dependency in `config/production-readiness.yaml` has verified
evidence; source-code presence alone is not production sign-off.

For the web applications and contract:

```bash
corepack enable
pnpm install
pnpm build:web
cd blockchain && npm install && npm test
```

## Non-negotiable production work

Client and investor due diligence starts at [`docs/assurance/README.md`](docs/assurance/README.md), which
records implemented controls, GDPR/POPIA mapping, SOC 2 readiness, residual risk and shared responsibility
without claiming certifications that have not been awarded.

1. Independent privacy, labour-law, whistleblowing, evidence and security review in every jurisdiction.
2. Phishing-resistant MFA, verified JWT/JWKS, SCIM lifecycle and privileged access management.
3. KMS/HSM envelope encryption, tenant/case key hierarchy and tested crypto-erasure.
4. Object Lock/WORM, malware/CDR pipeline, legal holds and defensible export tooling.
5. Formal STRIDE/LINDDUN assessment, penetration testing and abuse-case testing.
6. WCAG 2.2 AA, localisation, trauma-informed content design and assisted reporting channels.
7. Model/provider due diligence, red-team evaluations and documented human approval.
8. Backup, restore, regional failover, incident simulation and regulatory notification procedures.
