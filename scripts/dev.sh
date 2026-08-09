#!/usr/bin/env bash
set -euo pipefail
mode="${1:-core}"
case "$mode" in
  infra) docker compose up -d postgres-core postgres-vault postgres-audit rabbitmq temporal-postgres temporal temporal-ui minio keycloak opa ;;
  core) docker compose up --build api-gateway reporter-identity-service intake-service mailbox-service case-service evidence-service protection-service audit-service ;;
  all) docker compose up --build ;;
  down) docker compose down ;;
  *) echo "usage: $0 {infra|core|all|down}" >&2; exit 2 ;;
esac
