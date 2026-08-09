# Production Readiness & Go-to-Market Plan

Status: Active build plan. Source reference: `docs/reference/safelytold_feasibility_product_business_architecture_proposal.docx`.

## 1. Audit summary (Aug 2026)

The repository is a "foundation, not production release". A functional audit of every service and app
found three tiers of implementation:

| Tier | Services | Reality |
|---|---|---|
| Working | `ai_gateway`, `reporter_identity_service`, `audit_service`, `blockchain_ledger_service`, `evidence_service`, `policy_service`, `api`, `api_gateway`, outbox relay, Temporal state machines | Real endpoints, logic, tables |
| Scaffolding | `case`, `intake`, `investigation`, `mailbox`, `tenancy`, `analytics`, `protection`, `privacy`, `support`, `notification`, `integration`, `identity`, `security_monitor` | Generic JSON CRUD on one shared `domain_records` table; rich `domain.py` models are dead code |
| Stubs | `workers/event_consumer` (print only), `workflow_worker` activities (canned dicts), `prefect_flows` dev adapter, evidence sanitizer | "Production adapter calls..." comments |

Other facts:
- Only `services/api` has real Alembic migrations; every other service auto-creates tables via `create_all`.
- `reporter_identity_service` session returns a placeholder JWT.
- Emailing: zero capability anywhere (no SMTP/provider config, no library, no adapter, no mail container).
- Blockchain: ledger service + Solidity contract are real but orphaned; nothing feeds it; default `BLOCKCHAIN_MODE=database`.
- i18n: only `reporter-web` is translated (645 keys); `staff-web` and `trust-center-web` have 3 keys each.

## 2. Standing engineering rules

### 2.1 Internationalisation (i18n) — applies to every build
- No new page or feature text may be hardcoded in JSX. Every string must be a key in that app's
  `messages/en.json` (reporter-web, staff-web, trust-center-web each own a dictionary).
- New keys flow through the existing translation pipeline automatically:
  runtime `POST /ai/translate` (Azure for 138 locales, OpenAI fallback for non-Azure like `lg`),
  content-addressed Postgres cache + single-flight locks, client localStorage cache v2 with self-healing
  (values equal to English are never hash-locked).
- Non-Azure locales are pre-translated offline via `services/ai_gateway/scripts/pre_translate.py`
  (`--locale lg` and friends); new keys require a re-run of that script.
- Changes to a dictionary that alter existing source strings bump nothing manual: the content-addressed
  cache key derives from a SHA-256 of the canonical JSON, so the server cache re-seeds automatically;
  the client cache self-heals keys whose value equals the English source.

### 2.2 Integrity — applies to every state change
- No state-changing endpoint without an idempotency key where retries are likely.
- Domain events publish via the transactional outbox; consumers are idempotent by event id.
- Audit entries and evidence/verdicts are anchored to the integrity chain (see WS4).

## 3. Workstreams (in execution order)

### WS0 — Plan + governance artefacts
- This document; requirements matrix updates as work completes; i18n standard above.

### WS1 — Real two-way mailbox
- Real `mailbox_service` endpoints (threads, messages, read receipts, sealed transcripts, attachments)
  replacing generic CRUD; real short-lived reporter JWT in `reporter_identity_service`; message-body
  encryption; conflict-challenge + retaliation-concern actions on real endpoints.
- Reporter mailbox UI updated to the real API; staff-web mailbox/reply UI added.
- i18n: full mailbox key sets in both apps.

### WS2 — Emailing / notifications
- `notification_service`: template rendering + send endpoints over an outbound adapter
  (SMTP for dev/prod MVP; provider interface for SendGrid/SES later). Template text is neutral
  (no case content), localised per tenant locale.
- Dev stack: Mailpit container in `docker-compose.yml`; production config via env.
- `event_consumer` dispatches events to notification triggers; outbox relay added for the
  notification database; `integration_service/adapters/messaging` gets a real SMTP implementation.
- i18n: notification templates keyed from dictionaries.

### WS3 — Real domain services
- Replace generic CRUD with real tables + endpoints in `case` (triage, allegations, assignments),
  `investigation` (plans, interviews, findings, decisions, appeals), `evidence` (list, sanitise/redact),
  `protection` (plans, check-ins), `tenancy`, `analytics` (thresholded aggregates).
- Wire `workflow_worker` activities and `event_consumer` to real HTTP calls.
- Alembic migrations for every service (replace `create_all`).

### WS4 — End-to-end blockchain integrity
- Merkle batch builder feeding leaves (audit entries, evidence hashes, case milestones) to the ledger;
  publish `ledger.root_anchored.v1`.
- `anchor_case_milestone` + `record_audit_event` activities call the real services.
- Run the local anvil/Besu stack (`docker compose -f docker-compose.blockchain.yml up`) in dev;
  fix the staff ledger UI (batch_id + anchor history list).
- Default remains `BLOCKCHAIN_MODE=database` for cheap integrity; `evm` mode for assurance tiers.

### WS5 — Full i18n coverage
- Backfill `staff-web` and `trust-center-web` to full key sets (every page).
- Pre-translate non-Azure locales for the new key sets.

### WS6 — Phase 2 foundations + GtM
- SSO/SCIM adapter, HRIS relationship sync, legal-pack configuration, tenancy tiers, residency hooks.
- Design-partner recruitment, pilot evaluation, trust-centre content, procurement objection kit.

## 4. Definition of ready (each WS)
- Functional end-to-end (browser -> gateway -> service -> DB and back).
- i18n keys present in the relevant `messages/en.json`.
- No new `pass`/`NotImplemented`/placeholder in the changed code.
- Requirements matrix rows updated.

## 5. Launch sequence (per proposal §17.2)
1. WS1 + WS2 complete -> two-way comms works. 2. WS3 complete -> fair-process lifecycle works.
3. WS4 complete -> tamper-evident integrity works. 4. Pilot with 3 paid design partners.
5. Phase 2 (WS6) before general enterprise sale.

## 6. Progress log
- **2026-08-09 — WS1 complete.** `mailbox_service` now exposes real threaded endpoints
  (`/v1/mailbox/cases/{id}/messages`, `/threads/{id}/messages`, conflict challenges,
  retaliation concerns, safe-contact) backed by `mailbox_messages`,
  `mailbox_retaliation_concerns`, `mailbox_conflict_challenges`,
  `mailbox_safe_contact_preferences` tables with Fernet-encrypted bodies. Reporter access is
  gated by a short-lived HS256 JWT issued by `reporter_identity_service` (shared
  `REPORTER_JWT_SECRET`), bound to case + handle (invalid token -> 401, cross-case token -> 403).
  Handles now carry `tenant_id`; staff replies emit `mailbox.message.sent.v1` (new contract),
  concerns emit `retaliation.concern_reported.v1`. Reporter mailbox UI (`reporter-web`) uses the
  real API with session-expiry handling; new staff mailbox room (`staff-web/mailbox`) with
  thread + reply + concerns + challenges; staff case workbench updated to the thread API.
  Matrix rows PROD-02/PROD-03 updated. Deferred: evidence attachments, auto-escalation workflow,
  WS2 notifications (surfaces when a message needs human response).
