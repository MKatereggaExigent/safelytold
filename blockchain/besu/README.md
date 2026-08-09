# Besu production reference

This directory intentionally does not ship validator private keys or a ready-to-use production genesis. Generate keys independently in each validator's HSM or secret-management boundary.

Controls:

1. QBFT network with at least four validators across independent administrative owners.
2. Node allowlist and account allowlist enabled; expose no public peer discovery.
3. RPC limited to `ETH`, `NET` and `WEB3` methods required by the ledger adapter. Disable personal/admin/debug methods.
4. Private connectivity, mTLS reverse proxy, WAF/rate limiting and workload identity.
5. Dedicated anchor-writer account in an HSM; contract administrator and pauser are separate accounts.
6. Contract upgrade requires formal migration rather than a hidden proxy upgrade. Preserve old contracts permanently.
7. Monitor validator liveness, permissioning changes, role changes, failed transactions and chain reorganisation alerts.
8. Back up genesis, node identities, permissioning lists and contract deployment receipts. Do not back up HSM private keys as files.
