# Assurance evidence register

| Control | Evidence | State | Verification needed |
|---|---|---|---|
| Staff authentication/MFA | `infrastructure/keycloak/safelytold-realm.json`, identity tests | Implemented | Production IdP configuration and MFA sample |
| Staff provisioning | Registration disabled, direct grants disabled, admin/IdP/SCIM process | Implemented foundation | Joiner/mover/leaver and access-review evidence |
| Super-admin dual control | Keycloak role plus `ADMIN_SUPERUSER_EMAILS` check | Implemented | Secret/config change approvals and quarterly review |
| Tenant isolation | tenant-scoped queries, `safelytold_common/rls.py`, RLS reference | Implemented foundation | Non-superuser production DB and cross-tenant pen test |
| Identity separation | reporter identity service and separate vault database | Implemented | Cloud account/KMS/backup separation proof |
| Audit integrity | audit service, hash-chain tests, ledger service | Implemented | Retention/WORM and reconciliation evidence |
| Evidence integrity | evidence service, scanner, sanitizer, manifests | Implemented foundation | Object lock, restore and malware/CDR acceptance tests |
| Privacy-safe events/logs | event contracts, privacy validators, logging standard | Implemented foundation | Production log sampling and DLP test |
| Analytics privacy | cohort-thresholded analytics and tests | Implemented | Production report sample and governance approval |
| AI controls | AI gateway, governance policy, human-review UI | Implemented foundation | Model/supplier evaluation and impact assessment |
| Incident response | runbooks and incident event contracts | Documented/implemented foundation | Tabletop and after-action evidence |
| Resilience | SLO/BCP, IaC, readiness workflow | Partial | Two successful restores and failover exercise |
| GDPR/POPIA | This mapping, DPIA draft, privacy services | Partial | Counsel/DPO approval, RoPA, DPA and transfer records |
| SOC 2 | Readiness matrix and technical controls | Readiness only | Independent readiness/Type I/Type II report |
| Hotline/email | Signed provider adapter and channel readiness endpoint | Software implemented | Contract, number/address ownership and synthetic tests |

The strict machine-readable launch status is `config/production-readiness.yaml`. Status changes require an
evidence link, owner and approval; documentation alone does not convert a control to verified.

