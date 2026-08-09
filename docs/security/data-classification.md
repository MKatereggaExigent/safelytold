# Data classification and handling

| Class | Examples | Permitted locations | Forbidden locations |
|---|---|---|---|
| Restricted identity | reporter identity, contact details, identity-vault approvals | identity vault, encrypted authorised exports | events, logs, analytics, blockchain |
| Restricted case content | allegations, interview notes, findings, evidence | service DB, encrypted evidence store, authorised case UI | events, general telemetry, blockchain |
| Sensitive operational | case UUID, assignment, severity band, SLA state | service DB, privacy-safe events, audit | public analytics, blockchain unless committed/hash-only |
| Integrity commitment | SHA-256, Merkle root, opaque tenant/batch commitment | audit registry, permissioned chain | public chain when correlation risk is unacceptable |
| Aggregate public | thresholded metrics and published policies | trust centre | raw small-cell data |

Default rules: collect less, separate identity, encrypt by envelope, log metadata only, bind every access to purpose, suppress small cohorts, and expire data unless legal hold or documented legal duty applies.
