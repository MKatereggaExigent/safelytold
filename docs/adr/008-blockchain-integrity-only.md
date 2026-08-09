# ADR 008: Blockchain Integrity Only

**Status:** Accepted for foundation

## Decision

Use permissioned ledger only for opaque commitments and Merkle roots; no PII or case data on-chain.

## Consequences

This boundary must be enforced in code review, contracts, deployment identity and tests. Production implementation requires operational validation and may add provider-specific details without weakening the decision.
