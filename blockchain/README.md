# Permissioned integrity ledger

The blockchain is an optional tamper-evidence layer, not a database of workplace reports.

## On-chain data

Only these values may be anchored:

- opaque `bytes32` tenant commitment (salted/HMAC-derived, never a tenant name),
- opaque batch commitment,
- Merkle root of already-hashed audit/evidence manifest leaves,
- root type, leaf count and timestamp,
- contract event and transaction metadata.

No names, email addresses, case references, allegations, evidence, report text, IP addresses, device fingerprints, legal findings, employment decisions or encryption keys may be placed on-chain.

## Recommended production network

Use a private Hyperledger Besu network with QBFT consensus, node and account permissioning, TLS/mTLS at ingress, independent validator ownership, HSM-backed transaction signing and restricted JSON-RPC. Run at least four validators across independent administrative domains so that one corporate team cannot silently rewrite integrity history. The application remains operational if the chain is unavailable: roots queue for later anchoring and authoritative records remain in PostgreSQL/Object Storage.

## Development

`docker-compose.blockchain.yml` starts Anvil and deploys `IntegrityAnchor.sol`. It is strictly local; its deterministic development accounts must never be used outside local testing.
