import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_staff_self_registration_is_disabled() -> None:
    realm = json.loads((ROOT / 'infrastructure/keycloak/safelytold-realm.json').read_text())
    assert realm['registrationAllowed'] is False
    assert realm['verifyEmail'] is True
    staff = next(client for client in realm['clients'] if client['clientId'] == 'safelytold-staff')
    assert staff['directAccessGrantsEnabled'] is False
    login = (ROOT / 'apps/staff-web/app/LoginScreen.tsx').read_text()
    assert 'Create an account' not in login
    assert 'Continue in development mode' not in login
    assert 'DEV_SESSION' not in login
    assert "kc_action', 'register" not in (ROOT / 'apps/staff-web/lib/auth.ts').read_text()
