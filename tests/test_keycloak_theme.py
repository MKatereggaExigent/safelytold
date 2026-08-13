import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_safelytold_identity_theme_is_enabled() -> None:
    realm = json.loads((ROOT / 'infrastructure/keycloak/safelytold-realm.json').read_text())
    assert realm['loginTheme'] == 'safelytold'
    assert realm['displayName'] == 'SafelyTold'
    theme = ROOT / 'infrastructure/keycloak/themes/safelytold/login'
    assert (theme / 'theme.properties').exists()
    assert (theme / 'resources/css/safelytold.css').exists()


def test_staff_logout_uses_oidc_logout_hint() -> None:
    auth = (ROOT / 'apps/staff-web/lib/auth.ts').read_text(encoding='utf-8')
    shell = (ROOT / 'apps/staff-web/app/StaffShell.tsx').read_text(encoding='utf-8')
    assert 'post_logout_redirect_uri' in auth
    assert "params.set('id_token_hint'" in auth
    assert 'logoutUrl(session.idToken)' in shell


def test_master_theme_script_does_not_mix_staff_and_admin_realms() -> None:
    script = (ROOT / 'infrastructure/keycloak/configure-master-theme.ps1').read_text(encoding='utf-8')
    assert 'realms/master' in script
    assert 'loginTheme=safelytold' in script
    assert 'security-admin-console' not in (ROOT / 'apps/staff-web/lib/auth.ts').read_text(encoding='utf-8')
