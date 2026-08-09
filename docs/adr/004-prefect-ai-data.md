# ADR 004: Prefect Ai Data

**Status:** Accepted for foundation

## Decision

Prefect coordinates AI/data/retention pipelines; it cannot approve findings or mutate authoritative lifecycle state.

## Consequences

This boundary must be enforced in code review, contracts, deployment identity and tests. Production implementation requires operational validation and may add provider-specific details without weakening the decision.
