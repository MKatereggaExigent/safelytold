# ADR 009: Postgres Rls

**Status:** Accepted for foundation

## Decision

Use PostgreSQL RLS as defence in depth, not as the only tenant-isolation control.

## Consequences

This boundary must be enforced in code review, contracts, deployment identity and tests. Production implementation requires operational validation and may add provider-specific details without weakening the decision.
