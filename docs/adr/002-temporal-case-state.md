# ADR 002: Temporal Case State

**Status:** Accepted for foundation

## Decision

Temporal owns long-running case lifecycle because timers, signals, retries and auditability must survive process failure.

## Consequences

This boundary must be enforced in code review, contracts, deployment identity and tests. Production implementation requires operational validation and may add provider-specific details without weakening the decision.
