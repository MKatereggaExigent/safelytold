# ADR-013: Tenant-bound reporter plane and privacy-preserving eligibility

Status: Accepted (foundation implemented; advanced privacy phases planned)

## Decision

SafelyTold has two product surfaces with separate trust and publication rules:

- Public-interest reporting, moderated before any publication.
- Private tenant reporting, routed only into the selected organisation's data plane.

Private reporter journeys begin by resolving an active organisation and reporting channel in the tenancy service. The server issues a short-lived signed reporting context containing the immutable tenant, channel, permitted modes and eligibility class. Intake, reporter-handle creation and confidential identity storage require this context. Client-supplied `tenant_id` values are discarded and never establish tenancy.

Reporter modes are distinct:

1. Anonymous: identity is not requested; eligibility is not proven.
2. Verified anonymous: eligibility is proven using an unlinkable credential; no identity link is retained.
3. Confidential: identity is held only in the separate vault and hidden from investigators by default.
4. Identified: identity is available only to authorised participants under policy.

Staff authentication remains in the staff trust zone. It must not become the anonymous reporter session.

## Implemented foundation

- Server-side organisation resolution by stable slug.
- Short-lived, signed, purpose-specific reporter-access token.
- Tenant-bound intake endpoint that rejects unsupported modes and removes any submitted tenant identifier.
- Tenant-bound recovery-handle and identity-vault writes.
- Generic anonymous intake fallback disabled.
- Reporter UI blocks the form until an active organisation is resolved and prominently names the recipient.
- Persisted tenant channel policies define audience, eligibility requirement, enabled modes and availability.

## Required next phases

- Tenant-managed reporting-channel configuration and restricted audience policies.
- Separate eligibility issuer and one-time token redeemer using Privacy Pass-style blinded tokens.
- Batch/periodic credential issuance to reduce timing correlation.
- Spent-token store with no identifier join to cases.
- Privacy ingress that strips network metadata; Tor onion service for high-assurance anonymity; OHTTP evaluation.
- Host-only `__Host-` reporter cookies on a reporter registrable domain separate from staff.
- Immutable evidence originals plus sanitised working copies.
- Public-interest moderation service and database separate from private tenant cases.
- Control-plane/data-cell deployment tiers and tenant-specific keys.
- Delayed, opaque Merkle batch anchoring.

Until blinded eligibility issuance and privacy ingress are deployed, the UI and documentation must not describe an ordinary browser or direct SSO journey as cryptographically anonymous.

## Security invariants

- The browser never establishes tenant context with a raw tenant UUID.
- Reporter-access tokens contain no person identifier.
- Anonymous reporter sessions are independent of Keycloak staff sessions.
- AI receives no identity-vault data.
- Private reports can never enter the public publication workflow.
- Anti-abuse controls must not create cross-tenant device or identity tracking.
