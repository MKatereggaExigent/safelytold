# SaaS tenancy and customer overlays

SafelyTold is a multi-tenant SaaS platform. Its product architecture, security baseline, production gates,
workflows and assurance controls are customer-neutral. No prospective customer, tender or pilot defines
the platform-wide standard or appears as a hard-coded tenant in source configuration.

## Platform baseline versus tenant configuration

| Platform-owned SaaS baseline | Tenant-specific overlay |
|---|---|
| Authentication, tenant isolation, evidence integrity, audit, privacy-safe logging, secure workflow engine | Organisation name, branding, business units, authorised staff and identity provider |
| Global neutral case lifecycle and role model | Taxonomy additions, routing rules, SLA thresholds and escalation contacts |
| Reporter modes, mailbox, reference generation and evidence handling | Published channels, dedicated email/telephone details and supported languages |
| Security/privacy control framework | Controller/responsible-party decisions, lawful basis, notices, retention and jurisdiction pack |
| Generic training and awareness templates | Approved tenant copy, learner assignments, attendance and local policy content |
| Shared infrastructure/dedicated deployment patterns | Contracted tier, region, data residency, keys and integration providers |

## Customer requirement mappings

A procurement requirement or customer control questionnaire may be mapped to the SaaS baseline, but that
mapping is an account artefact—not a platform requirement namespace. Customer-specific documents should
live in the controlled customer implementation repository, CRM/contract workspace or a clearly named
`docs/customer-overlays/<tenant>/` area excluded from generic product claims as appropriate.

Mappings may reference generic IDs from `config/production-readiness.yaml` (for example `SAAS-01`) and add
customer IDs externally. They must not rename generic controls, insert customer brands into shared UI or
templates, or imply that another tenant inherits that customer's legal, operational or contractual choices.

## Isolation of configuration

- Every tenant has a stable UUID used by token claims, service records and database isolation.
- Tenant configuration is stored as data or deployment configuration, never embedded in shared business
  logic.
- Staff identities and roles are tenant scoped; seniority in one tenant grants no access to another.
- Dedicated database/stack tiers may be selected for residency or sensitivity without forking product
  behaviour.
- Cross-tenant administration is restricted to approved platform metadata operations and does not grant
  standing case-content access.

## Commercial assurance language

Use: “SafelyTold maps customer requirements onto a common, independently governed SaaS control baseline.”

Do not say: “The platform was built for [customer]” unless describing a separately contracted custom
deployment. Avoid embedding prospects in production-readiness IDs, demo seeds or global documentation.

