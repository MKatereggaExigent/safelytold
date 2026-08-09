param([ValidateSet('infra','core','all','down')][string]$Mode='core')
$ErrorActionPreference='Stop'
if ($Mode -eq 'infra') { docker compose up -d postgres-core postgres-vault postgres-audit rabbitmq temporal-postgres temporal temporal-ui minio keycloak opa }
elseif ($Mode -eq 'core') { docker compose up --build api-gateway reporter-identity-service intake-service mailbox-service case-service evidence-service protection-service audit-service }
elseif ($Mode -eq 'all') { docker compose up --build }
elseif ($Mode -eq 'down') { docker compose down }
