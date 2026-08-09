#!/usr/bin/env bash
set -euo pipefail
IFS=',' read -ra DBS <<< "${POSTGRES_MULTIPLE_DATABASES:-safelytold_gateway}"
for db in "${DBS[@]}"; do
  db="$(echo "$db" | xargs)"
  echo "Creating database: $db"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE "$db"' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db')\gexec
EOSQL
done
