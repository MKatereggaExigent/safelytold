# ADR 003: Rabbitmq Events

**Status:** Accepted for foundation

## Decision

RabbitMQ carries privacy-safe integration events using transactional outbox and idempotent consumers; it does not own case state.

## Consequences

This boundary must be enforced in code review, contracts, deployment identity and tests. Production implementation requires operational validation and may add provider-specific details without weakening the decision.
