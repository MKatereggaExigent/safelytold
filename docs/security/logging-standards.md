# Logging & Observability Standards (ADR-009)

## Principles
- Never log narratives, attachments, reporter secrets, identity vault data.
- Prefer structured logs (JSON) with IDs/reference codes.
- Tag logs with tenant_id only after RLS enforcement to avoid cross-tenant leakage.
- Obfuscate IP addresses by default; store full IP only in security telemetry with retention policy.

## Required Fields
| Field | Description |
| --- | --- |
| `timestamp` | ISO8601 UTC |
| `level` | DEBUG/INFO/WARN/ERROR |
| `event` | Canonical event name (e.g., `case.assignment.updated`) |
| `tenant_id` | UUID (or null for public routes) |
| `actor_type` | reporter / staff / system |
| `resource_type`/`resource_id` | e.g., case, evidence |

## Forbidden Content
- Free-form user input (narratives, message bodies)
- Attachment blobs / base64
- Reporter handle secrets / recovery codes
- Identity vault attributes

## Tools Configuration
- Application loggers default to INFO; DEBUG allowed only locally.
- Observability pipelines (OpenTelemetry/Loki) configured to redact fields flagged `pii=true`.
- Error tracking (Sentry, etc.) must sample stack traces and scrub request bodies.

## Review & Testing
- Add unit tests ensuring logging helpers reject PII payloads.
- Run periodic log sampling audits to confirm compliance.
