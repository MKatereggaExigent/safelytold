# ADR 005: Separate Identity Vault

**Status:** Accepted for foundation

## Decision

Reporter identity is physically and logically separated with different credentials, keys, administrators and approvals.

## Consequences

This boundary must be enforced in code review, contracts, deployment identity and tests. Production implementation requires operational validation and may add provider-specific details without weakening the decision.
