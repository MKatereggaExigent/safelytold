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

## Production deployment (public EVM L2)

1. Fund two accounts with native gas: a deployer/administrator and a dedicated anchor-writer (the signer the ledger service uses).
2. Deploy the contract:

   ```bash
   cd blockchain && npm install
   LEDGER_RPC_URL=https://<hosted-rpc-provider> \
   LEDGER_SIGNER_PRIVATE_KEY=0x<deployer-key> \
   LEDGER_ADMIN_ADDRESS=0x<admin-address> \
   LEDGER_WRITER_ADDRESS=0x<anchor-writer-address> \
   npx hardhat run scripts/deploy.ts --network base
   ```

   The script writes `deployment.local.json` with `address` and `chainId`.
3. Configure the ledger service (server `.env`, never commit the key):

   ```env
   BLOCKCHAIN_MODE=evm
   BLOCKCHAIN_RPC_URL=https://<hosted-rpc-provider>
   BLOCKCHAIN_CHAIN_ID=8453
   BLOCKCHAIN_CONTRACT_ADDRESS=<address from deployment.local.json>
   BLOCKCHAIN_SIGNER_PRIVATE_KEY=0x<anchor-writer-key>
   ```

   The anchor-writer account must hold native gas for every anchor transaction; monitor its balance. Keep the key in a secret manager/HSM in production.
4. Redeploy the stack: `git pull && ./deploy_to_caprover.sh`.
