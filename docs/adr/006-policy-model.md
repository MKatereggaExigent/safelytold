# ADR 006: Policy Model

**Status:** Accepted for foundation

## Decision

Combine RBAC, ABAC, assignment relationships, conflicts, purpose binding and obligations; default deny.

## Consequences

This boundary must be enforced in code review, contracts, deployment identity and tests. Production implementation requires operational validation and may add provider-specific details without weakening the decision.
