# Core Data Model (Draft)

Reference §16, Figure 7.

## Entities & Relationships

- **Tenant** (`tenants`)
  - `id`, `name`, `legal_entity_id`, `tier`, `region`
  - One-to-many with `legal_entities`, `users`, `cases`.

- **LegalEntity / OrgUnit**
  - Supports routing, conflict graph, jurisdiction packs.

- **User / Identity**
  - Staff accounts (OIDC) with roles, purposes.
  - Reporter handles stored separately (see Identity Vault).

- **ReporterHandle** (pseudonymous)
  - `handle_id`, `case_id`, `secret_hash`, `mode`, `vault_ref`.

- **Case** (`cases`)
  - `id`, `tenant_id`, `status`, `mode`, `created_at`, `reported_at`, `jurisdiction_code`.
  - Has many `allegations`, `case_parties`, `assignments`, `events`.

- **Allegation / Incident**
  - `id`, `case_id`, `taxonomy_code`, `description`, `related_entity`, `created_at`.

- **CaseParty**
  - `id`, `case_id`, `person_ref`, `role` (reporter, subject, witness, supporter), `relationship_metadata`.

- **Assignment**
  - `id`, `case_id`, `assignee_user_id`, `role`, `scope`, `assigned_at`, `expires_at`.

- **ConflictDeclaration**
  - `user_id`, `person_ref`, `relationship_type`, `effective_dates`.

- **Event / Timeline Entry**
  - `id`, `case_id`, `type` (triage, finding, decision, note), `payload` (JSONB), `actor`, `created_at`.

- **Evidence**
  - `id`, `case_id`, `submitted_by`, `hash`, `sealed_object_key`, `working_copy_key`, `scan_status`, `legal_hold`.

- **MailboxMessage**
  - `id`, `case_id`, `direction`, `body_ciphertext`, `created_at`, `attachments`.

- **ProtectionPlan / RetaliationCheck**
  - `id`, `case_id`, `risk_level`, `checkin_schedule`, `status`.

- **AuditLog**
  - `id`, `tenant_id`, `actor`, `action`, `resource_type`, `resource_id`, `hash`, `prev_hash`, `created_at`.

- **AI Run**
  - `id`, `case_id` (optional), `capability`, `input_ref`, `output_ref`, `human_reviewer`, `status`.

## Notes

- Every tenant-owned table includes `tenant_id` (part of primary/unique indexes) and RLS policies.
- Identity vault tables live in separate schema/database with stricter encryption & purpose checks.
- JSONB columns (`event.payload`, `ai_run.metadata`) must be schema-versioned.
- Outbox table (`integration_outbox`) captures committed events with `event_type`, `payload`, `retry_count`.

_Detailed ERD to follow once backend scaffolding starts._
