from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_architecture_is_not_a_public_trust_route() -> None:
    assert not (ROOT / 'apps/trust-center-web/app/architecture/page.tsx').exists()
    header = (ROOT / 'apps/trust-center-web/app/TrustHeader.tsx').read_text(encoding='utf-8')
    home = (ROOT / 'apps/trust-center-web/app/page.tsx').read_text(encoding='utf-8')
    assert '/architecture' not in header
    assert 'href="/architecture"' not in home


def test_architecture_is_server_authorized_and_staff_restricted() -> None:
    backend = (ROOT / 'services/tenancy_service/app/admin.py').read_text(encoding='utf-8')
    staff = (ROOT / 'apps/staff-web/app/architecture/page.tsx').read_text(encoding='utf-8')
    nav = (ROOT / 'apps/staff-web/app/StaffShell.tsx').read_text(encoding='utf-8')
    assert "@router.get('/platform-architecture')" in backend
    assert 'SuperuserDep' in backend
    assert "session.roles.includes('platform_super_admin')" in staff
    assert "roles: ['platform_super_admin']" in nav
