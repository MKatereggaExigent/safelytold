#!/usr/bin/env bash
# SafelyTold deployment script for a CapRover server.
#
# Run this ON THE SERVER after `git pull`. It:
#   1. Generates .env locally with strong random secrets (never committed).
#   2. Builds + starts the full stack via docker compose.
#   3. Deploys two nginx proxy apps to CapRover:
#        - <DOMAIN>      (frontend + /v1 API)  -> host ports 8100 / 8101
#        - <AUTH_DOMAIN> (Keycloak)            -> host port 8080
#
# Override anything via environment variables, e.g.:
#   BACKEND_HOST=1.2.3.4 CAPROVER_PASSWORD='...' ./deploy_to_caprover.sh
#
# This server is the same CapRover host as CryptoSqan (aidoc-server).
# All config below already matches it; the only interactive prompts are the
# OpenAI key and SMTP credentials (required once, on first run).

set -euo pipefail

# ---- Configuration (override via environment) ----
# Same server / CapRover instance as CryptoSqan.
DOMAIN="${SAFELYTOLD_DOMAIN:-safelytold.com}"
AUTH_DOMAIN="${SAFELYTOLD_AUTH_DOMAIN:-auth.safelytold.com}"
BACKEND_HOST="${BACKEND_HOST:-154.66.199.105}"             # public IP of this server
CAPROVER_NAME="${CAPROVER_NAME:-aidoc-server}"             # CapRover server name (same as CryptoSqan)
CAPROVER_URL="${CAPROVER_URL:-https://captain.apps.datasqan.com}"
CAPROVER_APP="${CAPROVER_APP:-safelytold}"                # main web app
CAPROVER_AUTH_APP="${CAPROVER_AUTH_APP:-safelytold-auth}" # keycloak app
CAPROVER_PASSWORD="${CAPROVER_PASSWORD:-Micho#25}"        # same CapRover password as CryptoSqan

FRONTEND_PORT=8100
API_PORT=8101
KEYCLOAK_PORT=8080

ENV_FILE=".env"

log()  { printf '\033[1;34m[deploy]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m[deploy]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[deploy]\033[0m %s\n' "$*"; }
fail() { printf '\033[1;31m[deploy]\033[0m ERROR: %s\n' "$*" >&2; exit 1; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

gen_secret() { openssl rand -hex 24; }

set_env() {
  local key="$1" value="$2"
  if grep -q "^${key}=" "$ENV_FILE"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
  else
    printf '%s=%s\n' "$key" "$value" >> "$ENV_FILE"
  fi
}

# Replace a known dev-only secret with a strong random one (idempotent).
harden() {
  local key="$1" dev_default="$2"
  local current
  current=$(grep -E "^${key}=" "$ENV_FILE" | head -n1 | cut -d= -f2- || true)
  if [ -z "$current" ] || [ "$current" = "$dev_default" ]; then
    set_env "$key" "$(gen_secret)"
    log "Generated a strong secret for ${key}"
  fi
}

prompt_value() {
  local key="$1" label="$2" default="${3:-}" secret="${4:-no}"
  local current
  current=$(grep -E "^${key}=" "$ENV_FILE" | head -n1 | cut -d= -f2- || true)
  [ -n "$current" ] && return 0
  local answer
  if [ "$secret" = "yes" ]; then
    read -rsp "${label}: " answer; echo
  else
    read -rp "${label} [${default}]: " answer
  fi
  answer="${answer:-$default}"
  [ -z "$answer" ] && fail "${label} is required"
  set_env "$key" "$answer"
}

health_check() {
  local url="$1" name="$2" tries="${3:-40}"
  log "Waiting for ${name} to become healthy... ${url}"
  for _ in $(seq 1 "$tries"); do
    if curl -fsS -o /dev/null --max-time 5 "$url" 2>/dev/null; then
      ok "${name} is healthy"
      return 0
    fi
    sleep 5
  done
  fail "${name} did not become healthy in time (${url})"
}

# --- Step 0: preflight ------------------------------------------------------
log "Preflight checks"
command_exists docker      || fail "docker is not installed"
command_exists curl        || fail "curl is not installed"
command_exists openssl     || fail "openssl is not installed"
command_exists caprover    || warn "caprover CLI not found - install it before the deploy step"
if ! docker compose version >/dev/null 2>&1; then
  fail "docker compose (v2) is not available"
fi
ok "Preflight complete"

# --- Step 1: .env provisioning ---------------------------------------------
if [ ! -f "$ENV_FILE" ]; then
  cp .env.example "$ENV_FILE"
  log "Created ${ENV_FILE} from .env.example"
else
  log "${ENV_FILE} already exists - preserving existing secrets"
fi

log "Applying production configuration to ${ENV_FILE}"
set_env ENVIRONMENT production
set_env AI_PROVIDER openai
set_env DEV_AUTH_BYPASS false
set_env NEXT_PUBLIC_DEV_AUTH false
set_env NEXT_PUBLIC_API_BASE_URL "https://${DOMAIN}"
set_env NEXT_PUBLIC_KEYCLOAK_URL "https://${AUTH_DOMAIN}"
set_env KEYCLOAK_PUBLIC_URL "https://${AUTH_DOMAIN}"
set_env KEYCLOAK_PROXY_HEADERS xforwarded
set_env JWT_ISSUER "https://${AUTH_DOMAIN}/realms/safelytold"
set_env CORS_ORIGINS "https://${DOMAIN}"
set_env MESSAGING_PROVIDER smtp
set_env SMTP_USE_TLS true

harden POSTGRES_PASSWORD      safelytold_dev_only
harden VAULT_DB_PASSWORD      vault_dev_only
harden AUDIT_DB_PASSWORD      audit_dev_only
harden RABBITMQ_PASSWORD      safelytold_dev_only
harden S3_SECRET_KEY          safelytold_dev_only_change_me
harden KEYCLOAK_ADMIN_PASSWORD admin_dev_only
harden GRAFANA_ADMIN_PASSWORD admin_dev_only
harden AUDIT_SIGNING_KEY      development-only-change-me
harden REPORTER_PEPPER        development-only-change-me

prompt_value OPENAI_API_KEY       "OpenAI API key (required)"          "" yes
prompt_value SMTP_HOST            "SMTP host"                          "smtp.gmail.com"
prompt_value SMTP_PORT            "SMTP port"                          "587"
prompt_value SMTP_USERNAME        "SMTP username"                      ""
prompt_value SMTP_PASSWORD        "SMTP password"                      "" yes
prompt_value SMTP_FROM            "SMTP from address"                  "no-reply@${DOMAIN}"
prompt_value ADMIN_SUPERUSER_EMAILS "Superuser emails (comma separated)" "michael.kateregga@datasqan.com"

ok "${ENV_FILE} is production-ready"

# --- Step 2: build and start the stack -------------------------------------
log "Building and starting the SafelyTold stack (this can take several minutes)"
docker compose up -d --build

health_check "http://localhost:${API_PORT}/health"         "api-gateway"
health_check "http://localhost:${FRONTEND_PORT}/"          "frontend-proxy"
health_check "http://localhost:${KEYCLOAK_PORT}/realms/safelytold/.well-known/openid-configuration" "keycloak"
ok "Stack is up"

# --- Step 3: deploy CapRover proxy apps ------------------------------------
command_exists caprover || fail "caprover CLI not installed - install it and re-run this step"

TMPDIR_MAIN="$(mktemp -d)"
TMPDIR_AUTH="$(mktemp -d)"

log "Packaging main app (${CAPROVER_APP}) for ${DOMAIN}"
cat > "$TMPDIR_MAIN/captain-definition" <<'EOF'
{"schemaVersion": 2, "dockerfilePath": "./Dockerfile"}
EOF
cat > "$TMPDIR_MAIN/Dockerfile" <<'EOF'
FROM nginx:stable-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF
cat > "$TMPDIR_MAIN/nginx.conf" <<EOF
server {
    listen 80;
    server_name _;

    client_max_body_size 12m;

    gzip on;
    gzip_types text/plain text/css application/javascript application/json image/svg+xml;
    gzip_min_length 512;

    location /v1/ {
        proxy_pass http://${BACKEND_HOST}:${API_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
    }

    location / {
        proxy_pass http://${BACKEND_HOST}:${FRONTEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
    }
}
EOF

log "Packaging auth app (${CAPROVER_AUTH_APP}) for ${AUTH_DOMAIN}"
cat > "$TMPDIR_AUTH/captain-definition" <<'EOF'
{"schemaVersion": 2, "dockerfilePath": "./Dockerfile"}
EOF
cat > "$TMPDIR_AUTH/Dockerfile" <<'EOF'
FROM nginx:stable-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF
cat > "$TMPDIR_AUTH/nginx.conf" <<EOF
server {
    listen 80;
    server_name _;

    client_max_body_size 12m;

    location / {
        proxy_pass http://${BACKEND_HOST}:${KEYCLOAK_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120;
        proxy_connect_timeout 120;
    }
}
EOF

( cd "$TMPDIR_MAIN" && tar -czf /tmp/safelytold-main.tar.gz ./* )
( cd "$TMPDIR_AUTH" && tar -czf /tmp/safelytold-auth.tar.gz ./* )

log "Deploying ${CAPROVER_APP} to CapRover"
caprover deploy \
  --caproverName "$CAPROVER_NAME" \
  --caproverApp "$CAPROVER_APP" \
  --caproverUrl "$CAPROVER_URL" \
  --caproverPassword "$CAPROVER_PASSWORD" \
  --tarFile /tmp/safelytold-main.tar.gz

log "Deploying ${CAPROVER_AUTH_APP} to CapRover"
caprover deploy \
  --caproverName "$CAPROVER_NAME" \
  --caproverApp "$CAPROVER_AUTH_APP" \
  --caproverUrl "$CAPROVER_URL" \
  --caproverPassword "$CAPROVER_PASSWORD" \
  --tarFile /tmp/safelytold-auth.tar.gz

rm -rf "$TMPDIR_MAIN" "$TMPDIR_AUTH"

# --- Step 4: summary ---------------------------------------------------------
cat <<EOF

==============================================================
 SafelyTold deployed
==============================================================
 Reporter portal : https://${DOMAIN}
 Staff portal    : https://${DOMAIN}/staff
 Trust centre    : https://${DOMAIN}/trust
 Keycloak admin  : https://${AUTH_DOMAIN}
 API gateway     : https://${DOMAIN}/v1/

 Point DNS at ${BACKEND_HOST}:
   ${DOMAIN}       A  ${BACKEND_HOST}
   ${AUTH_DOMAIN}  A  ${BACKEND_HOST}

 Attach those domains to the CapRover apps (${CAPROVER_APP}
 and ${CAPROVER_AUTH_APP}) with "Enable HTTPS" enabled.
==============================================================
EOF
