# Blockchain reconciliation

1. Select anchor records in `pending` or inconsistent state.
2. Recompute the Merkle root from the immutable batch manifest.
3. Compare contract `RootAnchored` event, transaction receipt, chain ID and block hash.
4. Confirm contract address and deployment receipt against the approved registry.
5. If no transaction exists, safely resubmit the identical root using the idempotency key.
6. If a different root exists for the same batch commitment, raise a critical integrity incident.
7. Store reconciliation evidence off-chain and append an audit event.
