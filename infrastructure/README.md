# Infrastructure

The local environment demonstrates the trust boundaries; production should replace local credentials and containers with managed or hardened equivalents.

- PostgreSQL databases per service, with a physically separate reporter identity vault and audit store.
- RabbitMQ quorum queues for privacy-safe integration events.
- Temporal for authoritative long-running case workflows.
- Prefect for governed AI, data quality and retention pipelines.
- MinIO as S3-compatible development evidence storage; Object Lock/WORM is required in production.
- Keycloak for local OIDC only; production requires enterprise IdP, phishing-resistant MFA and SCIM.
- OPA reference policies for central policy decisions.
- OpenTelemetry Collector, Prometheus, Grafana, Loki and Tempo examples.
- ClamAV for development malware scanning.
- Optional permissioned-chain profile under `docker-compose.blockchain.yml`.
