# ADR 011: Observability Privacy

**Status:** Accepted for foundation

## Decision

Telemetry must delete bodies, identity and SQL content; security value does not justify unrestricted case logging.

## Consequences

This boundary must be enforced in code review, contracts, deployment identity and tests. Production implementation requires operational validation and may add provider-specific details without weakening the decision.
