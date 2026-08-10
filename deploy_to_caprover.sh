#!/usr/bin/env bash
# SafelyTold deployment script for the SafelyTold CapRover server.
#
# Run this ON THE SERVER after `git pull`. It assumes .env already exists
# (copy .env.example to .env and set your real secrets first - no values are
# written by this script). Steps:
#   1. Builds + starts the full stack via docker compose.
#   2. Health-checks the API, frontend and Keycloak.
#   3. Deploys two nginx proxy apps to CapRover:
#        - <DOMAIN>      (frontend + /v1 API)  -> host ports 8100 / 8101
#        - <AUTH_DOMAIN> (Keycloak)            -> host port 8080
#
# This server is the same CapRover host as CryptoSqan (aidoc-server).
# Override anything via environment variables, e.g.:
#   BACKEND_HOST=1.2.3.4 CAPROVER_PASSWORD='...' ./deploy_to_caprover.sh

set -euo pipefail

# ---- Configuration (override via environment) ----
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

log()  { printf '\033[1;34m[deploy]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m[deploy]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[deploy]\033[0m %s\n' "$*"; }
fail() { printf '\033[1;31m[deploy]\033[0m ERROR: %s\n' "$*" >&2; exit 1; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

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
command_exists caprover    || fail "caprover CLI not installed - install it and re-run this script"
if ! docker compose version >/dev/null 2>&1; then
  fail "docker compose (v2) is not available"
fi
[ -f .env ] || fail "No .env found - copy .env.example to .env and set your real secrets first"
ok "Preflight complete"

# --- Step 1: build and start the stack -------------------------------------
log "Building and starting the SafelyTold stack (this can take several minutes)"
docker compose up -d --build

health_check "http://localhost:${API_PORT}/health"         "api-gateway"
health_check "http://localhost:${FRONTEND_PORT}/"          "frontend-proxy"
health_check "http://localhost:${KEYCLOAK_PORT}/realms/safelytold/.well-known/openid-configuration" "keycloak"
ok "Stack is up"

# --- Step 2: deploy CapRover proxy apps ------------------------------------
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
map \$http_x_forwarded_proto \$safelytold_proto {
    default \$http_x_forwarded_proto;
    ""      \$scheme;
}

server {
    listen 80;
    server_name _;

    access_log off;

    client_max_body_size 12m;

    gzip on;
    gzip_types text/plain text/css application/javascript application/json image/svg+xml;
    gzip_min_length 512;

    location /v1/ {
        proxy_pass http://${BACKEND_HOST}:${API_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-Proto \$safelytold_proto;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
    }

    location / {
        proxy_pass http://${BACKEND_HOST}:${FRONTEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-Proto \$safelytold_proto;
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
map \$http_x_forwarded_proto \$safelytold_proto {
    default \$http_x_forwarded_proto;
    ""      \$scheme;
}

server {
    listen 80;
    server_name _;

    access_log off;

    client_max_body_size 12m;

    location / {
        proxy_pass http://${BACKEND_HOST}:${KEYCLOAK_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-Proto \$safelytold_proto;
        proxy_read_timeout 120;
        proxy_connect_timeout 120;
    }
}
EOF

( cd "$TMPDIR_MAIN" && tar -czf /tmp/safelytold-main.tar.gz ./* )
( cd "$TMPDIR_AUTH" && tar -czf /tmp/safelytold-auth.tar.gz ./* )

log "Authenticating with CapRover (${CAPROVER_URL})"
caprover login \
  --caproverUrl "$CAPROVER_URL" \
  --caproverPassword "$CAPROVER_PASSWORD" \
  --caproverName "$CAPROVER_NAME" \
  --default >/dev/null 2>&1 || log "CapRover machine '${CAPROVER_NAME}' already known - using stored session"

log "Deploying ${CAPROVER_APP} to CapRover"
caprover deploy \
  --caproverName "$CAPROVER_NAME" \
  --caproverApp "$CAPROVER_APP" \
  --tarFile /tmp/safelytold-main.tar.gz \
  || fail "deploy of ${CAPROVER_APP} failed (is the app created in CapRover?)"

log "Deploying ${CAPROVER_AUTH_APP} to CapRover"
caprover deploy \
  --caproverName "$CAPROVER_NAME" \
  --caproverApp "$CAPROVER_AUTH_APP" \
  --tarFile /tmp/safelytold-auth.tar.gz \
  || fail "deploy of ${CAPROVER_AUTH_APP} failed (is the app created in CapRover?)"

rm -rf "$TMPDIR_MAIN" "$TMPDIR_AUTH"

# --- Step 3: summary ---------------------------------------------------------
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
