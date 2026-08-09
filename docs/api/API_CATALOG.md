# API catalogue

The foundation implements representative endpoints and supplies the target surface below for fleshing out. Public endpoints use pseudonymous reporter sessions; staff endpoints require OIDC plus policy decisions. All mutating endpoints require idempotency keys in production.

## Public/reporting

- `POST /public/tenants/{slug}/journal` — create encrypted private journal
- `POST /public/tenants/{slug}/cases` — submit anonymous/confidential/identified report
- `POST /public/cases/{handle}/events` — add structured event
- `POST /public/cases/{handle}/evidence` — upload sealed evidence
- `POST /public/mailbox/session` — exchange case code/secret for short session
- `GET|POST /public/mailbox/{case}/messages`
- `POST /public/mailbox/{case}/conflict-challenge`
- `POST /public/mailbox/{case}/retaliation-concerns`
- `POST /public/cases/{case}/supporters`

## Staff case lifecycle

- `GET|PATCH /cases/{id}`
- `POST /cases/{id}/allegations`
- `POST /cases/{id}/conflict-checks`
- `POST /cases/{id}/assignments`
- `POST /cases/{id}/recusals`
- `POST /cases/{id}/investigation-plans`
- `POST /cases/{id}/interviews`
- `POST /allegations/{id}/findings`
- `POST /cases/{id}/decisions`
- `POST /cases/{id}/remedies`
- `POST /cases/{id}/appeals`
- `POST /cases/{id}/close`

## Evidence

- multipart upload/init/finalise and scan status
- metadata preview/sanitise/content-disarm
- create working/redacted derivative
- legal hold/release
- disclosure package and signed manifest
- hash/Merkle proof verification

## Protection/support

- protection plan, safe contact, baseline, scheduled check-ins and escalation
- support invitation, consent, revoke and referral

## Tenant/admin/privacy

- tenants, legal entities, organisational units, taxonomy, policies, routing and retention
- staff roles, scoped invitations, JIT grants and break-glass approvals
- consent receipts, DSAR/correction/export/restriction/deletion review and breach cases
- OIDC/SAML/SCIM/HRIS/EAP/voice/webhook/regulator connector configuration

## Analytics and integrity

- thresholded aggregates, board report generation and regulatory export
- audit append/verify/batch
- ledger anchor/proof/verify/reconcile
- AI run/evaluate/review/approve with source and model provenance
