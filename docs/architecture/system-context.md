# System context

```mermaid
flowchart LR
  Reporter[Reporter / family supporter] --> RP[Reporter Portal]
  Staff[Ethics, investigator, legal, privacy, ombuds] --> SP[Staff Portal]
  Public[Public / board / regulator] --> TC[Trust Centre]
  RP --> GW[API Gateway]
  SP --> GW
  TC --> Analytics[Thresholded aggregate API]
  GW --> Domains[Domain Microservices]
  Domains --> PG[(Service-owned PostgreSQL)]
  Domains --> Vault[(Separate Identity Vault)]
  Domains --> Evidence[(Immutable Object Storage)]
  Domains --> Temporal[Temporal]
  Domains --> MQ[RabbitMQ]
  Domains --> Audit[(Append-only Audit Store)]
  Audit --> Ledger[Blockchain Ledger Service]
  Ledger --> Besu[(Optional Besu QBFT Network)]
  Domains --> AI[Governed AI Gateway]
  AI --> Prefect[Prefect Flows]
  Domains --> IdP[Enterprise IdP / SCIM]
  Domains --> External[HRIS / EAP / SIEM / regulators]
```

The reporter portal and identity vault form a distinct privacy realm. Staff cannot derive anonymous reporter identity from normal case APIs. Platform operators do not receive blanket case-content access.
