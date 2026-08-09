# Initial SLO and resilience targets

| Capability | Target after production readiness |
|---|---|
| Reporter intake availability | 99.95% monthly, excluding announced maintenance |
| Protected mailbox availability | 99.9% |
| Staff case operations | 99.9% |
| RPO restricted case databases | <= 5 minutes |
| RTO regional service restoration | <= 4 hours |
| Evidence durability | provider multi-zone durability plus tested manifests |
| Event delivery | at-least-once, idempotent consumers, DLQ reviewed |
| Temporal workflow recovery | replay tested during release qualification |
| Blockchain anchoring | non-blocking; catch-up within 24 hours |

Backups are encrypted, access-controlled and restored quarterly. Identity vault and audit store have independent backup credentials. Evidence manifests are reconciled against object inventory and ledger commitments.
