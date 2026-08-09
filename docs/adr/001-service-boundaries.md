# ADR 001: Service Boundaries

**Status:** Accepted for foundation

## Decision

Use bounded-context microservices with separate data ownership; early deployments may consolidate runtimes without sharing schemas.

## Consequences

This boundary must be enforced in code review, contracts, deployment identity and tests. Production implementation requires operational validation and may add provider-specific details without weakening the decision.
