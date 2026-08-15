import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def realm() -> dict:
    return json.loads((ROOT / 'infrastructure/keycloak/safelytold-realm.json').read_text())


def test_realm_enforces_core_authentication_controls() -> None:
    value = realm()
    assert value['registrationAllowed'] is False
    assert value['bruteForceProtected'] is True
    assert value['revokeRefreshToken'] is True
    assert value['refreshTokenMaxReuse'] == 0
    assert value['accessTokenLifespan'] <= 300
    assert 'length(14)' in value['passwordPolicy']
    assert value['adminEventsEnabled'] is True
    assert next(action for action in value['requiredActions'] if action['alias'] == 'CONFIGURE_TOTP')['defaultAction'] is True


def test_staff_client_uses_authorization_code_pkce_only() -> None:
    client = next(item for item in realm()['clients'] if item['clientId'] == 'safelytold-staff')
    assert client['standardFlowEnabled'] is True
    assert client['implicitFlowEnabled'] is False
    assert client['directAccessGrantsEnabled'] is False
    assert client['serviceAccountsEnabled'] is False
    assert client['attributes']['pkce.code.challenge.method'] == 'S256'


def test_production_builder_removes_users_and_local_origins() -> None:
    path = ROOT / 'scripts' / 'build_production_keycloak_realm.py'
    spec = importlib.util.spec_from_file_location('build_production_keycloak_realm', path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    value = module.build('https://safelytold.com')
    assert value['sslRequired'] == 'all'
    assert value['users'] == []
    rendered = json.dumps(value)
    assert 'localhost' not in rendered
    assert 'change-me-local-only' not in rendered


def test_demo_personas_never_receive_platform_super_admin() -> None:
    config = (ROOT / 'config' / 'demo-environment.yaml').read_text()
    assert 'platform_super_admin' not in config
