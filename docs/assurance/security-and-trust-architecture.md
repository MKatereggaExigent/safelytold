# Security and trust architecture

## Identity and administrative separation

Keycloak is the identity provider. It authenticates staff, enforces MFA, issues signed OIDC tokens and
manages session lifecycle and realm roles. Authentication is necessary but not sufficient for case access.

SafelyTold separates two administrative domains:

| Domain | Authority | Permitted scope |
|---|---|---|
| Keycloak master administration | Dedicated master-realm infrastructure administrators | Identity server, realms, clients, authentication flows and identity-provider configuration |
| SafelyTold platform administration | Verified user in `safelytold` realm with `platform_super_admin`, plus controlled application allow-list | Tenant/platform configuration and approved metadata operations |

Platform super-admin is deliberately not standing case-content access. The default role matrix grants
infrastructure scope only; case or identity access requires a separate purpose-bound, audited break-glass
or approval workflow. The application superuser check requires both a verified Keycloak role and membership
in `ADMIN_SUPERUSER_EMAILS`. This dual condition mitigates accidental/malicious role assignment. Keycloak
remains authoritative for identity; SafelyTold remains authoritative for business authorisation.

Staff self-registration is disabled. Direct password grants are disabled for the staff client. Accounts
must be administrator/IdP/SCIM provisioned, email verified and MFA enrolled. Staff login and logout use
PKCE and RP-initiated logout with an ID-token hint and allow-listed redirect.

## Reporter anonymity and identity vault

- Anonymous reporting requires no corporate SSO or employer-linked account.
- A random public case code and recovery secret establish a pseudonymous reporter session.
- Confidential/identified attributes are stored in a separate identity-vault database.
- Identity reveal requires an authorised purpose and approval workflow and is audited.
- Identity fields, reporter secrets and raw case text are forbidden in integration events, logs,
  analytics and blockchain commitments.
- The platform never promises absolute anonymity: narrative facts, attachment metadata, workplace
  context or lawful process may enable inference outside technical controls.

## Authorisation model

Access is the conjunction of:

1. Verified identity and MFA;
2. Tenant claim;
3. Role;
4. Declared purpose;
5. Case assignment/scope;
6. Relationship and conflict/recusal state;
7. Time-bound approval where required; and
8. Audit obligations.

Role alone cannot grant reporter-identity or unrestricted case access. The policy service supports
allow, deny, approval and recusal decisions. See `docs/security/role-matrix.md` and
`infrastructure/opa/safelytold.rego`.

## Data isolation

| Boundary | Design |
|---|---|
| Tenant | Every domain row carries `tenant_id`; authenticated requests establish tenant context; repository queries filter by tenant. |
| Database | PostgreSQL RLS policies are applied to tenant tables and use transaction-local `app.tenant_id`; production must use a non-superuser/non-bypass application role. |
| Reporter identity | Separate database, credentials and cryptographic boundary from ordinary case services. |
| Audit | Separate audit database and credentials; append-only hash chain and optional Merkle anchoring. |
| Evidence | Sealed original, SHA-256 receipt, malware scanning, sanitised working copies, legal hold and signed manifests. |
| Deployment tiers | Shared database, dedicated database and dedicated stack/residency patterns are defined; selected tier is contractual. |

Important limitation: the local Docker database role is a PostgreSQL superuser and therefore can bypass
RLS. Local development is not tenant-isolation certification. Production evidence must show non-superuser
roles, FORCE RLS where applicable and negative cross-tenant tests.

## Encryption and key separation

- TLS is required at external boundaries in production.
- Restricted case and identity fields use application encryption where implemented.
- Production design requires KMS/HSM-managed hierarchy: platform/regional KEK, tenant KEK, case/object
  DEKs, separate identity-vault keys, separate audit-signing and blockchain keys.
- Secrets must be stored in a managed secret store and rotated; development defaults are prohibited.
- Customer-managed keys are a later assurance-tier option and must not be claimed as operational until
  a provider-specific lifecycle is implemented and tested.

## Secure records, events and audit

- Raw narratives, attachments and identity attributes remain in authoritative restricted stores.
- Transactional outbox events contain references and classifications, not allegation text.
- Consumers are at-least-once and must be idempotent by event ID.
- Audit entries are hash chained and independently verifiable; hashes/Merkle roots may be anchored without
  publishing case data.
- Evidence originals are never silently overwritten by sanitisation/redaction.

## Availability and incident response

Target SLOs, RTO/RPO and recovery order are in `docs/operations/slo-and-resilience.md` and
`docs/operations/business-continuity.md`. These are targets, not achieved SLAs, until production monitoring,
restore exercises, multi-zone configuration and signed test evidence exist. Incident, privacy breach,
break-glass and evidence-export runbooks are version controlled under `runbooks/`.

