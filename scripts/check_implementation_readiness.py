"""Fail closed when proposal-critical domains are still scaffolding."""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config/implementation-readiness.yaml'
PLACEHOLDER = re.compile(r'(?im)^\s*(pass|raise NotImplementedError)\s*$|production adapter|placeholder')


def assess() -> list[str]:
    config = yaml.safe_load(CONFIG.read_text(encoding='utf-8'))
    errors: list[str] = []
    for service in config['critical_services']:
        service_root = ROOT / 'services' / service
        main = service_root / 'app' / 'main.py'
        if not main.exists():
            errors.append(f'{service}: main.py missing')
            continue
        source = main.read_text(encoding='utf-8')
        if config['requirements']['forbid_generic_router'] and 'safelytold_common.generic' in source:
            errors.append(f'{service}: still uses generic domain-record router')
        migration_versions = service_root / 'migrations' / 'versions'
        migrations = list(migration_versions.glob('*.py'))
        if config['requirements']['require_migration_versions'] and not migrations:
            errors.append(f'{service}: no versioned production migration')
        elif config['requirements']['require_migration_versions'] and not any(
            'op.create_table' in path.read_text(encoding='utf-8')
            or 'op.add_column' in path.read_text(encoding='utf-8')
            for path in migrations
        ):
            errors.append(f'{service}: migration contains no executable schema operation')
        if config['requirements']['forbid_placeholders']:
            for path in (service_root / 'app').glob('*.py'):
                if PLACEHOLDER.search(path.read_text(encoding='utf-8')):
                    errors.append(f'{service}: placeholder in {path.name}')
    return errors


def main() -> int:
    errors = assess()
    for error in errors:
        print(f'BLOCKER: {error}')
    print(f'Implementation readiness: {len(errors)} blocker(s)')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
