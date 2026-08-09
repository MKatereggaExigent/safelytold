# ADR 012: Jurisdiction Configuration

**Status:** Accepted for foundation

## Decision

Legal/process variations live in versioned reviewed packs rather than hard-coded branching.

## Consequences

This boundary must be enforced in code review, contracts, deployment identity and tests. Production implementation requires operational validation and may add provider-specific details without weakening the decision.
