# Logical data model

Each bounded context owns its tables. Cross-service identifiers are opaque UUIDs or commitments; there are no cross-database foreign keys.

```mermaid
erDiagram
  TENANT ||--o{ ORG_UNIT : contains
  TENANT ||--o{ CASE : owns
  REPORTER_HANDLE ||--o{ REPORT : submits
  REPORT ||--|| CASE : becomes
  CASE ||--o{ ALLEGATION : contains
  CASE ||--o{ PARTY_RELATIONSHIP : scopes
  CASE ||--o{ ASSIGNMENT : grants
  ASSIGNMENT ||--o{ CONFLICT_CHECK : requires
  CASE ||--o{ EVIDENCE_OBJECT : references
  EVIDENCE_OBJECT ||--o{ EVIDENCE_DERIVATIVE : produces
  CASE ||--o{ INTERVIEW : plans
  CASE ||--o{ FINDING : concludes
  CASE ||--o{ REMEDY : tracks
  CASE ||--o{ APPEAL : permits
  CASE ||--o{ PROTECTION_PLAN : protects
  PROTECTION_PLAN ||--o{ RETALIATION_CHECK : schedules
  CASE ||--o{ MAILBOX_MESSAGE : communicates
  CASE ||--o{ AUDIT_ENTRY : records
  AUDIT_BATCH ||--|| BLOCKCHAIN_ANCHOR : commits
```

Identity-vault records are linked through independently generated opaque references and are not joinable by ordinary service credentials.
