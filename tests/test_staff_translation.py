from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_staff_shell_applies_language_control_to_every_route() -> None:
    shell = (ROOT / 'apps/staff-web/app/StaffShell.tsx').read_text(encoding='utf-8')
    assert '<StaffLanguage />' in shell


def test_staff_translation_excludes_sensitive_operational_content() -> None:
    source = (ROOT / 'apps/staff-web/app/StaffLanguage.tsx').read_text(encoding='utf-8')
    for selector in ('td', '.mono', '.chat', 'pre', 'code', '[data-no-translate]'):
        assert selector in source
    assert "querySelectorAll<HTMLElement>('[placeholder],[aria-label],[title]')" in source


def test_staff_static_dictionaries_have_language_controls() -> None:
    import json
    for locale in ('en', 'af', 'zu'):
        values = json.loads((ROOT / f'apps/staff-web/messages/{locale}.json').read_text(encoding='utf-8'))
        assert all(key in values for key in ('lang_label', 'lang_other', 'lang_translating', 'lang_apply', 'lang_failed'))


def test_staff_shell_uses_base_path_safe_role_switch_and_friendly_roles() -> None:
    shell = (ROOT / 'apps/staff-web/app/StaffShell.tsx').read_text(encoding='utf-8')
    roles = (ROOT / 'apps/staff-web/lib/staff.ts').read_text(encoding='utf-8')
    assert '<Link href="/" className="btn btn-ghost btn-sm">Switch role</Link>' in shell
    assert "{ value: 'platform_developer', label: 'Platform developer' }" in roles
    assert 'staffRoleLabel(session.roles[0])' in shell


def test_shared_unpadded_panels_keep_content_away_from_boundaries() -> None:
    styles = (ROOT / 'packages/typescript/ui/styles.css').read_text(encoding='utf-8')
    assert '.panel:not(.panel-padded) > .panel-head' in styles
    assert '.panel-body {' in styles
