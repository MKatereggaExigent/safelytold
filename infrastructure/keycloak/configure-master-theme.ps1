# Run after Keycloak starts to brand the infrastructure administration realm.
# This intentionally changes presentation only; it never redirects staff users
# into the privileged master realm.
$ErrorActionPreference = 'Stop'
$adminUser = if ($env:KEYCLOAK_ADMIN_USERNAME) { $env:KEYCLOAK_ADMIN_USERNAME } else { 'admin' }
$adminPassword = if ($env:KEYCLOAK_ADMIN_PASSWORD) { $env:KEYCLOAK_ADMIN_PASSWORD } else { 'admin_dev_only' }
docker compose exec -T keycloak /opt/keycloak/bin/kcadm.sh config credentials --server http://localhost:8080 --realm master --user $adminUser --password $adminPassword
docker compose exec -T keycloak /opt/keycloak/bin/kcadm.sh update realms/master -s loginTheme=safelytold -s displayName='SafelyTold Platform Administration' -s registrationAllowed=false
