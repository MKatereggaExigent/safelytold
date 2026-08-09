# Key management hierarchy

Production keys belong in managed KMS/HSM, never environment files or databases.

- Root/platform key encrypts only regional or service key-encryption keys.
- Tenant KEK is region-bound and rotatable.
- Case DEK encrypts restricted case fields and evidence metadata.
- Evidence object DEK is unique per object or version.
- Identity-vault DEKs use a separate KMS account/project and administrator group.
- Audit signing key and blockchain writer key live in separate HSM partitions.
- Search indexes use tokenisation or isolated encrypted indexes; never reuse encryption keys.

Key access emits a privacy-safe audit event. Crypto-erasure requires deleting the applicable wrapped DEK after retention and legal-hold checks, while preserving non-identifying integrity receipts where legally justified.
