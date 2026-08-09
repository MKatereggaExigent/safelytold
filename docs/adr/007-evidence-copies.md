# ADR 007: Evidence Copies

**Status:** Accepted for foundation

## Decision

Preserve sealed originals and generate working/redacted derivatives; never overwrite evidence.

## Consequences

This boundary must be enforced in code review, contracts, deployment identity and tests. Production implementation requires operational validation and may add provider-specific details without weakening the decision.
