# Multi-tenancy tiers

| Tier | Compute | Database | Keys | Typical customer |
|---|---|---|---|---|
| Shared foundation | shared cluster | service DB with tenant RLS | provider-managed tenant key | small organisations/pilots |
| Dedicated database | shared or isolated compute | dedicated service databases | dedicated tenant KEK | enterprise |
| Dedicated environment | dedicated namespace/cluster and network | dedicated managed databases | customer-managed or dedicated KMS | regulated enterprise |
| Sovereign/private | customer/sovereign cloud | locally operated stores | customer HSM | government/high sensitivity |

A tenant can move upward through an export/import process with signed manifests. Product code must not assume one tenancy tier. Reporter identity vault and audit storage remain separately administered even in shared tiers.
