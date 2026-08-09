# Default role matrix

| Role | Tenant config | Case list | Assigned case | Identity vault | Findings/decision | Audit |
|---|---:|---:|---:|---:|---:|---:|
| Platform super-admin | infrastructure only | no | break-glass only | no standing access | no | platform metadata |
| Tenant owner | yes | no by default | separately assigned | no | no | configuration |
| Ethics administrator | policy/taxonomy | aggregate/queue | separately assigned | no by default | oversight | tenant controls |
| Triage officer | limited | new queue | triage scope | mode/purpose only | no final decision | own access |
| Case manager | no | assigned queue | process/communication | normally masked | workflow only | case audit |
| Investigator | no | assigned only | evidence/interviews | minimum necessary | findings, not discipline | case audit |
| Legal counsel | legal config | purpose scoped | privilege scope | exceptional | legal review | purpose scoped |
| Privacy officer | privacy config | privacy cases | DSAR/incident scope | dual-control role | no routine finding | privacy audit |
| Ombuds/audit committee | no | escalated only | fixed-term scope | minimum necessary | oversight/review | relevant audit |
| Auditor | controls only | no raw list | no raw content | prohibited | no | read-only audit |

Every access also depends on tenant, case assignment, relationship/conflict state, declared purpose, jurisdiction, time window, device/session policy and approval obligations.
