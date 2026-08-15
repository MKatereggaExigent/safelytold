"""Reject demo-era behavior in the production staff application."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAFF = ROOT / 'apps' / 'staff-web'
FORBIDDEN = {
    'createRecord(': 'generic record creation',
    'listRecords(': 'generic record listing',
    'getRecord(': 'generic record lookup',
    'useRecords(': 'generic record hook',
    'DEFAULT_SESSION': 'default/development session',
    'development demo': 'demo-only disclosure',
}


def assess() -> list[str]:
    errors: list[str] = []
    for path in STAFF.rglob('*'):
        if path.suffix not in {'.ts', '.tsx'} or '.next' in path.parts or 'node_modules' in path.parts:
            continue
        source = path.read_text(encoding='utf-8')
        for token, meaning in FORBIDDEN.items():
            if token in source:
                errors.append(f'{path.relative_to(ROOT)}: {meaning}')
    required_routes = {'cases', 'protection', 'support', 'privacy', 'identity', 'security', 'analytics', 'audit', 'ledger', 'operations'}
    actual = {path.name for path in (STAFF / 'app').iterdir() if path.is_dir()}
    for route in sorted(required_routes - actual):
        errors.append(f'apps/staff-web/app/{route}: required staff route missing')
    shell = (STAFF / 'app' / 'StaffShell.tsx').read_text(encoding='utf-8')
    translator = STAFF / 'app' / 'StaffLanguage.tsx'
    if not translator.exists() or '<StaffLanguage />' not in shell:
        errors.append('apps/staff-web: staff-wide language translation control missing')
    elif "const EXCLUDED='td,.mono,.chat,pre,code,[data-no-translate]" not in translator.read_text(encoding='utf-8'):
        errors.append('apps/staff-web: translation does not protect operational/evidentiary content')
    return errors


if __name__ == '__main__':
    failures = assess()
    for failure in failures:
        print(f'BLOCKER: {failure}')
    print(f'Staff application readiness: {len(failures)} blocker(s)')
    raise SystemExit(1 if failures else 0)
