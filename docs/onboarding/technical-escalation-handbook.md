# SafelyTold technical escalation handbook

Audience: engineering, solution architecture, security, privacy, operations/SRE, technical product management and technical bid responders.

Purpose: provide the second-line team with enough context to answer escalated enquiries, demonstrate evidence, design customer deployments and prevent unsupported commitments.

## 1. Technical position

SafelyTold is a multi-application, bounded-context SaaS platform. Public reporter, protected staff and public trust experiences are separated at application and routing level. Backend capabilities are exposed through a single API gateway and implemented by tenant-aware services. Keycloak issues staff identities and roles; reporter access uses separate pseudonymous/recovery credentials.

The demo tenant uses the production application and service code. Its records are synthetic and its external providers must terminate at controlled sandboxes. A demo is not permitted to bypass authorization, state transitions, approval rules, privacy suppression or integrity logic.

## 2. Application topology and URLs

| Surface | Public path | Local path | Access |
| --- | --- | --- | --- |
| Reporter application | `/`, `/report`, `/case`, `/mailbox`, `/journal`, `/control-room/*`, `/support`, `/emergency`, `/pricing` | `http://localhost:8100/...` | Public entry plus reporter recovery/session controls. |
| Trust Centre | `/trust`, `/trust/governance`, `/trust/integrity`, `/trust/privacy`, `/trust/ai`, `/trust/reports`, `/trust/verify` | `http://localhost:8100/trust/...` | Public assurance information. |
| Staff application | `/staff/login`, `/staff/dashboard`, `/staff/cases`, `/staff/mailbox`, `/staff/evidence`, `/staff/protection`, `/staff/support`, `/staff/analytics`, `/staff/operations`, `/staff/privacy`, `/staff/ai`, `/staff/ledger`, `/staff/audit` | `http://localhost:8100/staff/...` | Keycloak authentication and role checks. |
| Restricted platform views | `/staff/admin`, `/staff/architecture`, `/staff/admin/assurance` | same local base | Verified `platform_super_admin`; backend also requires an allowlisted email outside development bypass. |
| Tenant IAM | `/staff/identity` | same local base | `tenant_admin` or platform super-administrator. |
| Security operations | `/staff/security` | same local base | `security_analyst` or platform super-administrator. |
| Demo tour | `/staff/demo` | `http://localhost:8100/staff/demo` | Fixed demo tenant only. |
| API gateway | not intended as a marketing/public API | `http://localhost:8101/v1/gateway/{service}/...` | Downstream service authorization remains authoritative. |
| Keycloak | deployment-specific identity hostname | `http://localhost:8080` | Administrative console is not a customer product page. |

Production origin currently documented as `https://safelytold.com`. Confirm DNS, TLS, reverse-proxy paths and Keycloak issuer for the actual environment before answering a customer.

## 3. Service map

| Service | Responsibility |
| --- | --- |
| tenancy | Tenant lifecycle, legal entities, organisational units, channel configuration, subscriptions and protected platform assurance. |
| identity | Tenant staff registry, invitations and scoped/time-bound grants. |
| reporter-identity | Recovery handles, reporter sessions and separately controlled identity-vault requests. |
| policy | Policy evaluation and jurisdiction/workflow decisions. |
| intake | Tenant-bound structured reports and privacy receipts. |
| mailbox | Reporter/staff messages, safe-contact settings, retaliation concerns and conflict challenges. |
| case | Case references, lifecycle, allegations, conflict checks and assignments. |
| investigation | Plans, findings, independent review and appeals. |
| evidence | Upload, malware scan integration, hashes, object storage, receipts and legal hold. |
| protection | Protection plans, scheduled check-ins and mandatory high-risk escalation references. |
| support | Verified support directory and consent-referenced referrals. |
| analytics | Tenant metrics, cohort aggregation, suppression threshold and management reports. |
| integration | Provider channels and operational records for awareness, training, QA, continuity, coverage, hotline and reporting. |
| notification | Neutral templates, queued delivery, provider results, retry state and manual send. |
| privacy | Consent receipts, statutory requests and breach assessment. |
| audit | Append-oriented audit entries and integrity verification. |
| security | Privacy-safe security alerts, triage, runbooks and containment evidence. |
| ai | Governed writing, translation and analysis use cases with human authority retained. |
| ledger | Hash/Merkle-root anchors and proof verification; no narratives or identities. |

## 4. Identity, tenancy and authorization

### Staff authentication

- Keycloak realm: `safelytold`.
- Staff client: `safelytold-staff`.
- OAuth/OIDC Authorization Code flow with PKCE S256.
- Implicit flow, service accounts and resource-owner password grants are disabled for the staff browser client.
- Public registration is disabled.
- MFA uses TOTP and is a default required action.
- Access tokens require issuer, signature, audience, expiry, issued-at and subject validation.
- The `tenant_id` user attribute is emitted as an ID/access/userinfo claim.
- Backend context derives roles from realm and client role claims.
- Production requests require a declared purpose.

### Tenant isolation

The token tenant claim is the primary tenant context. Services set tenant context and filter records by tenant. PostgreSQL RLS references exist as defence in depth, but technical responders must verify the deployed database role does not bypass RLS before claiming database-enforced isolation for a particular environment.

Never accept an arbitrary browser `x-tenant-id` header as production authority. Development bypass headers are permitted only when `DEV_AUTH_BYPASS=true`, which must be false in production.

### Authorization layers

1. Authenticated identity or reporter credential.
2. Tenant binding.
3. Realm/client role.
4. Declared purpose.
5. Resource/case assignment where applicable.
6. Conflict check, approval, expiry or state-machine condition.
7. Service-side tenant ownership check.

Frontend visibility is not an authorization boundary. Every sensitive backend route must enforce the relevant layer independently.

### Role families

Operational roles include tenant owner/admin, ethics administration, triage, case management, investigation, review, decision, legal, privacy, ombuds, audit, protection, support and security. Platform roles include super-administration, operations, security and support. Additional specialist roles cover billing, residency, configuration, hotline, safeguarding, QA, training, reporting, records, compliance, continuity, integration, notification, AI governance, policy and evidence.

A role existing in Keycloak does not automatically authorize a service action. The service permission must be implemented and tested. Treat unconsumed future roles as catalogue entries, not working permissions.

## 5. Keycloak production baseline

The realm configuration enforces:

- registration disabled and duplicate email disabled;
- verified email and non-editable username;
- TOTP required action;
- minimum 14-character complex passwords, 12-password history and 90-day expiry;
- brute-force protection and progressive temporary lockout;
- 300-second access tokens;
- refresh-token revocation and zero reuse;
- bounded SSO, client and offline sessions;
- authentication and admin event recording;
- PKCE authorization code flow;
- explicit governed attributes for tenant ID, demo classification and expiry.

Generate a deployment artifact with:

```powershell
python scripts/build_production_keycloak_realm.py `
  --public-origin https://safelytold.com `
  --output safelytold-realm.production.json
```

The generator requires a non-local HTTPS origin, sets `sslRequired=all`, removes embedded users and credentials, and removes localhost redirect/origin entries. Bootstrap administrators must be created through the deployment secret process, not committed realm exports.

For an already-running realm, the demo provisioner synchronises the approved hardening fields, governed user-profile attributes and role catalogue through the Admin API.

## 6. Reporting-mode implementation

Canonical values are:

```text
anonymous
verified_anonymous
confidential
identified
```

They are shared by intake and operational/provider validation. `external_referral` may exist as an internal intake classification but is not one of the four reporter choices.

### Anonymous

No reporter identity should be required. The reporter receives a recovery handle/secret and exchanges it for a short-lived reporter session. Metadata, logs, events and attachments must be reviewed for indirect identifiers.

### Verified Anonymous

Requires an eligibility requirement of `privacy-pass` or `anonymous-credential`. Do not implement it by authenticating with ordinary staff SSO and then deleting the subject identifier; that is linkable. Before customer activation, test issuer/verifier separation and collusion/linkability properties.

### Confidential

Contact/identity may be collected into the protected identity path. Access requests, independent approval and purpose/expiry controls apply. Case content should reference the vault record rather than duplicate identity data.

### Identified

The reporter knowingly places identity on record, subject to the configured notice, lawful basis, access and retention controls. Identified does not mean unrestricted internal publication.

## 7. Core state machines and invariants

### Case lifecycle

```text
unverified → triage → open → investigating → decision_pending → closed
                    ↘ on_hold ↗
triage → referred → closed
```

The service rejects invalid transitions. Every transition requires a reason and emits an event. Assignments require a matching clear conflict check, supported role and future expiry.

### Investigation

- Plan requires a case, at least one issue, scope and optional evidence sources/milestones.
- Findings distinguish substantiated, unsubstantiated, inconclusive and referred outcomes.
- A reviewer approval is separate from investigator authorship.
- Appeal creation requires an approved finding.
- Appeal decisions are upheld, varied or dismissed.

### Protection

- Approved measures must be a subset of requested measures.
- Review/check-in dates must be future dates when scheduled.
- A high or critical completed check-in requires an escalation identifier.

### Evidence

- Uploads pass through scanning and controlled object storage.
- Integrity metadata uses cryptographic hashes.
- Legal hold prevents ordinary disposal paths.
- Do not claim immutable storage unless object-lock/versioning settings have been verified in the target environment.

### Privacy

- Consent decisions are recorded.
- Access, correction, deletion, restriction, objection and portability requests are tracked with deadlines.
- Decisions record fulfilment/restriction reasoning.
- Breaches capture jurisdiction and affected data classes.
- Legal/privacy owners determine notification duties; the application record does not replace counsel assessment.

### Analytics

- Management analytics aggregate tenant observations.
- Cohorts below the minimum threshold of five return a suppressed value.
- Narratives are not included in the management-report response.
- Do not work around suppression by issuing overlapping queries or joining external data.

### Operational readiness

The operations service enforces separate state machines and evidence requirements for awareness, training, QA, continuity, coverage, hotline and management reporting. Examples include minimum training score/critical questions, zero critical QA defects for approval, measured RTO/RPO for a passed continuity test, dual responders for active coverage, and reporting periods for generated reports.

## 8. Evidence, audit and blockchain explanation

The ledger accepts hashes and Merkle roots, records batch/kind/chain/mode metadata and verifies proofs. In database mode an anchor is durable in the ledger database but is not a public-chain transaction. In EVM mode the service submits the anchor and records chain ID, transaction hash and block metadata.

Qualification language:

- Correct: “The system can provide tamper-evident integrity anchors and proof verification.”
- Incorrect: “All reports are stored on blockchain.”
- Incorrect in database mode: “This transaction is independently public-chain notarised.”

Before answering an end-to-end blockchain question, verify `BLOCKCHAIN_MODE`, chain ID, RPC connectivity, contract address, signer custody/funding, confirmations, retry/reconciliation, explorer visibility and proof reconstruction.

## 9. Notifications, hotline and 24/7 coverage

Notification records use neutral templates and destination references; provider delivery is asynchronous/trackable and records success or failure. Sandbox providers must exercise the same request, rendering, queue, send and result lifecycle as production providers.

The hotline operational record intentionally excludes caller ID, phone number, recording URL, reporter name and narrative. It requires provider call ID, reporting mode, language and start time. A submitted/escalated hotline call must link to a case created through normal intake.

Production readiness for a customer requires more than the software record:

- contracted operator and escalation matrix;
- provisioned and tested country-specific number;
- 24/7/365 staffing evidence and service levels;
- language coverage;
- approved scripts and notices;
- recording/consent decision;
- identity and metadata minimisation;
- outage/overflow routes;
- test calls, reconciliation and incident procedure.

Never mark a customer hotline “live” based only on `coverage/status` or synthetic demo data.

## 10. AI and translation

AI use cases are bounded by purpose. Permitted examples include writing assistance, translation and privacy-safe aggregate analysis. Human reviewers remain authoritative.

Prohibited claims/actions include:

- credibility or deception scoring;
- automated guilt or disciplinary decisions;
- deanonymisation or identity inference;
- bypass of suppressed analytics;
- training on customer content without explicit lawful governance;
- sending unredacted case data to an unapproved model endpoint.

The staff translation mechanism excludes marked evidence/user content from automatic interface translation. Verify the chosen model/provider, regional processing, retention, logging and DPA before enabling production AI.

## 11. Demo environment runbook

Configuration: `config/demo-environment.yaml`

Provisioner: `scripts/provision_demo_environment.py`

Supported actions:

```powershell
python scripts/provision_demo_environment.py keycloak
python scripts/provision_demo_environment.py tenant
python scripts/provision_demo_environment.py seed
python scripts/provision_demo_environment.py all
python scripts/provision_demo_environment.py disable-expired
```

Required secrets are environment variables and must not be committed:

- `KEYCLOAK_ADMIN_USERNAME`
- `KEYCLOAK_ADMIN_PASSWORD`
- `DEMO_USER_PASSWORD`
- `DEMO_ADMIN_ACCESS_TOKEN` for production tenant creation
- `DEMO_SEED_ACCESS_TOKEN` for production-equivalent API seeding
- `DEMO_ACCOUNT_EXPIRES_AT`

`--dev-auth` is local-only and requires service-side development bypass. It must never be used against production.

Seed data is idempotently identified by workflow `synthetic-demo-v1`. Current seed coverage includes cases at different lifecycle states, allegations, conflict-cleared assignments, investigation/finding/review/appeal, protection/check-in, consent/DSR/breach, support referral, privacy-thresholded analytics, security response and all operational-readiness areas.

Demo accounts:

- are bound to tenant `d3a00000-0000-4000-8000-000000000001`;
- have `.invalid` email addresses;
- require temporary-password replacement and TOTP;
- carry synthetic classification and expiry attributes;
- never receive platform super-administrator roles.

Schedule `disable-expired` through the deployment scheduler. Rotate demo credentials after external demonstrations and whenever attendance changes.

## 12. Production deployment gate

Do not approve production launch until evidence exists for all applicable items:

### Identity and access

- Production realm generated without users/local origins.
- Bootstrap credentials held in a secret manager and rotated.
- MFA, password, lockout, events and session settings verified through the live Admin API.
- Exact redirect URIs, origins, issuer and audience verified.
- Demo/development bypass disabled.
- Tenant attributes and role mappings tested in actual tokens.
- Joiner/mover/leaver and break-glass processes approved.

### Data and isolation

- Tenant IDs align across tenancy database and Keycloak claims.
- Cross-tenant API tests and database/RLS tests pass.
- Production database roles cannot bypass intended RLS.
- Encryption in transit/at rest and key ownership verified.
- Backups, restore test, retention and legal hold verified.
- Object-store versioning/object lock and malware scanning verified.

### Operations

- Gateway/service readiness passes.
- Monitoring, alerting and privacy-safe logs reach the approved operations stack.
- Incident, breach and continuity exercises completed.
- Measured RTO/RPO meet the contractual values.
- On-call coverage and support escalation are staffed.
- Provider delivery and retry/reconciliation tests pass.

### Customer configuration

- Contract, DPA, privacy notice, controller/processor roles and subprocessor list approved.
- Jurisdictions, categories, workflows, retention and escalation approved.
- Staff roles, conflict rules and approval authorities loaded.
- Reporting channels, email and hotline verified end to end.
- Training and awareness materials delivered.
- Management-report recipients and privacy threshold approved.

## 13. Technical due-diligence response rules

For each answer label the status:

| Label | Meaning |
| --- | --- |
| Implemented | Code and automated tests exist. |
| Verified in environment | Live configuration and an end-to-end check were observed in the named environment/date. |
| Customer configuration required | Product support exists but tenant-specific choices or data are required. |
| External dependency required | Provider, DNS, number, certificate, contract or external infrastructure is required. |
| Readiness programme | Policies/evidence exist but an independent certification or operating history is not claimed. |
| Roadmap | Not available for contractual reliance. |

Attach evidence rather than relying on adjectives. Suitable evidence includes test results, redacted live configuration, architecture decision records, runbooks, restore-test reports, provider acceptance tests and current third-party reports approved for disclosure.

## 14. Escalation intake and response

### Required ticket fields

- requester organisation and authorised contact;
- commercial owner and deadline;
- exact question and requested response format;
- environment and tenant, where applicable;
- countries, languages, users and estimated volume;
- data classifications and retention expectation;
- SSO, API, provider and network dependencies;
- certification, legal or contractual implications;
- disclosure classification of the response;
- evidence reviewed, owner, conclusion and expiry/review date.

Do not copy case content, reporter identity, secrets, access tokens, evidence or sensitive architecture into a general-purpose ticket.

### Severity routing

| Severity | Example | Response |
| --- | --- | --- |
| Critical | Active breach, identity exposure, loss of access controls, immediate safety issue | Invoke incident process immediately; stop sales handling. |
| High | Bid blocker involving security architecture, residency, legal deadline or 24/7 service | Assign named technical/security/privacy owner and deadline. |
| Normal | Integration design, workflow configuration, volume sizing | Solution-design backlog with commercial due date. |
| Informational | Standard capability explanation with current approved evidence | Technical responder validates and returns reusable answer. |

## 15. Troubleshooting guide

### User sees “Create an account”

Check Keycloak realm registration, client/realm URL and whether an old theme/page is cached. `registrationAllowed` must be false. Do not hide registration only with CSS.

### Staff pages appear accessible without login

Check both sides of the boundary. `NEXT_PUBLIC_DEV_AUTH` must be false in the built staff image and `DEV_AUTH_BYPASS` must be false in every backend service. Rebuild the frontend because public environment values are compiled into its JavaScript; recreate backend containers because service settings load at startup. Test a protected API with forged `x-dev-*` headers and require HTTP 401. Clear any stale `wpc:session` browser storage and confirm a protected path redirects to `/staff/login`.

### Login succeeds but tenant pages are empty or forbidden

Inspect the verified token for issuer, audience, realm roles and `tenant_id`; compare the tenant database UUID; confirm purpose; then inspect assignment/role requirements. Do not compensate by trusting a browser tenant header.

### Logout shows a Keycloak confirmation page

Verify the OIDC end-session request, `id_token_hint`, client ID and exact post-logout redirect URI registered in Keycloak. A stale session/tab URL is not a stable redirect target.

### Staff page returns 404

Confirm the `/staff` base path, reverse proxy rule, deployed image route inventory and whether the link accidentally included `/staff` twice inside the Next.js application.

### DNS/MX works on a phone but not a workstation

Compare DNS resolver, VPN/proxy, hosts file, corporate DNS cache, split-horizon records and TLS interception. MX controls mail routing, not web-page resolution. Capture `Resolve-DnsName`, effective resolver and proxy state; do not change public DNS based on one corporate workstation alone.

### Demo user logs in but has no tenant claim

Confirm Keycloak’s declarative user-profile schema includes governed `tenant_id`, the user attribute is present, and the client mapper emits it into access tokens. Existing tokens must be refreshed after attribute changes.

### Management metrics are missing

Confirm observation period/tenant/metric and whether the cohort is intentionally suppressed below five. Never disable suppression merely to make a demonstration look populated.

### Ledger has no transaction hash

Check the anchor mode. Database mode intentionally has no public-chain transaction. For EVM mode inspect provider connectivity, signer, funding, contract configuration and receipt processing.

## 16. Technical do and do not list

### Do

- Reproduce questions against the named version/environment.
- Validate live Keycloak settings rather than assuming realm import updated an existing database.
- Test with two tenants for isolation claims.
- Preserve synthetic/production data separation.
- Keep provider sandbox behavior contract-compatible with production behavior.
- Cite exact controls and known residual risks.
- Time-bound technical answers where infrastructure or certification can change.

### Do not

- treat frontend route hiding as authorization;
- use development bypass in production;
- grant broad roles to solve missing permission logic;
- claim every Keycloak catalogue role is already consumed by backend policy;
- store secrets in documentation, source, CRM or test fixtures;
- expose internal architecture/security material without approval;
- call readiness a certification;
- equate encryption with anonymity;
- put narratives or identities in events, logs, analytics or blockchain metadata;
- approve go-live based solely on unit tests or synthetic demo status.

## 17. Supporting technical documents

- `docs/security/role-matrix.md`
- `docs/security/threat-model.md`
- `docs/security/data-classification.md`
- `docs/security/key-management.md`
- `docs/assurance/security-and-trust-architecture.md`
- `docs/assurance/privacy-gdpr-popia.md`
- `docs/assurance/shared-responsibility.md`
- `docs/assurance/soc2-readiness.md`
- `docs/architecture/system-context.md`
- `docs/architecture/container-view.md`
- `docs/architecture/report-sequence.md`
- `docs/architecture/blockchain-security.md`
- `docs/operations/hotline-operating-model.md`
- `docs/operations/business-continuity.md`
- `docs/operations/quality-assurance.md`
- `docs/operations/training-programme.md`
- `docs/operations/management-reporting.md`
- `docs/api/API_CATALOG.md`

Historical feasibility/proposal material is not authoritative for current implementation status. Validate it against code, tests and the running release before using it in due diligence.
