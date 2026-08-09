#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SERVICES = {
    'api_gateway', 'tenancy_service', 'identity_service', 'reporter_identity_service', 'policy_service',
    'intake_service', 'mailbox_service', 'case_service', 'investigation_service', 'evidence_service',
    'protection_service', 'support_service', 'analytics_service', 'integration_service',
    'notification_service', 'privacy_service', 'audit_service', 'security_monitor_service', 'ai_gateway',
    'blockchain_ledger_service',
}
REQUIRED_COMPOSE_SERVICES = {
    'postgres-core', 'postgres-vault', 'postgres-audit', 'rabbitmq', 'temporal', 'temporal-ui',
    'minio', 'clamav', 'keycloak', 'opa', 'api-gateway', 'reporter-identity-service',
    'audit-service', 'blockchain-ledger-service', 'workflow-worker', 'event-consumer',
    'reporter-web', 'staff-web', 'trust-center-web', 'otel-collector', 'prometheus', 'grafana',
}
REQUIRED_EVENTS = {
    'case.reported.v1', 'case.conflict_detected.v1', 'case.acknowledged.v1', 'evidence.received.v1',
    'evidence.sanitised.v1', 'case.assignment_changed.v1', 'case.finding_submitted.v1', 'case.closed.v1',
    'retaliation.concern_reported.v1', 'privacy.security_incident.v1', 'ledger.root_anchored.v1',
}
FORBIDDEN_EVENT_FIELDS = {
    'name', 'email', 'phone', 'address', 'body', 'content', 'description', 'evidence', 'identity', 'message',
    'narrative', 'password', 'secret', 'statement', 'token', 'ip_address', 'device_fingerprint',
    'allegation_text',
}
REQUIRED_PROHIBITIONS = {
    'truthfulness_scoring', 'automated_discipline', 'covert_email_monitoring', 'covert_chat_monitoring',
    'public_accusation_board', 'individual_reputation_scores', 'autonomous_regulator_reporting',
    'broad_employee_surveillance',
}
SKIP_PARTS = {'.git', '.pytest_cache', '__pycache__', 'node_modules', '.next', 'dist', 'build'}


def fail(message: str) -> None:
    print(f'ERROR: {message}', file=sys.stderr)
    raise SystemExit(1)


def load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding='utf-8'))
    except Exception as exc:  # pragma: no cover - validation script
        fail(f'invalid YAML in {path.relative_to(ROOT)}: {exc}')


def validate_serialised_files() -> tuple[int, int]:
    json_count = 0
    yaml_count = 0
    for path in ROOT.rglob('*'):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() == '.json':
            try:
                json.loads(path.read_text(encoding='utf-8'))
            except Exception as exc:
                fail(f'invalid JSON in {path.relative_to(ROOT)}: {exc}')
            json_count += 1
        elif path.suffix.lower() in {'.yaml', '.yml'}:
            # Helm templates contain Go expressions and are validated by Helm in deployment CI.
            if 'helm' in path.parts and 'templates' in path.parts:
                continue
            load_yaml(path)
            yaml_count += 1
    return json_count, yaml_count


def validate_services() -> int:
    services = {p.name for p in (ROOT / 'services').iterdir() if p.is_dir()}
    missing = REQUIRED_SERVICES - services
    if missing:
        fail(f'missing services: {sorted(missing)}')

    for service in REQUIRED_SERVICES:
        for path in [ROOT / 'services' / service / 'app' / 'main.py', ROOT / 'services' / service / 'README.md']:
            if not path.exists():
                fail(f'missing {path.relative_to(ROOT)}')
    return len(services)


def validate_events() -> int:
    events = {p.stem for p in (ROOT / 'contracts' / 'events').glob('*.json')}
    missing_events = REQUIRED_EVENTS - events
    if missing_events:
        fail(f'missing event contracts: {sorted(missing_events)}')

    for path in (ROOT / 'contracts' / 'events').glob('*.json'):
        schema = json.loads(path.read_text(encoding='utf-8'))
        props = set(schema['properties']['data']['properties'])
        violations = {prop for prop in props if prop.lower() in FORBIDDEN_EVENT_FIELDS}
        if violations:
            fail(f'{path.name} exposes forbidden event fields: {sorted(violations)}')
        if schema['properties']['type'].get('const') != path.stem:
            fail(f'{path.name} event type does not match filename')
    return len(events)


def validate_compose() -> None:
    compose = load_yaml(ROOT / 'docker-compose.yml') or {}
    compose_services = set((compose.get('services') or {}).keys())
    missing = REQUIRED_COMPOSE_SERVICES - compose_services
    if missing:
        fail(f'docker-compose.yml is missing required services: {sorted(missing)}')
    if not {'postgres-vault', 'postgres-audit'}.issubset(compose_services):
        fail('identity vault and audit databases must remain physically separate in the foundation')


def validate_security_controls() -> None:
    contract = (ROOT / 'blockchain' / 'contracts' / 'IntegrityAnchor.sol').read_text(encoding='utf-8').lower()
    for forbidden in ['string report', 'string allegation', 'string evidence', 'string identity', 'string email']:
        if forbidden in contract:
            fail(f'blockchain contract appears to accept prohibited content: {forbidden}')

    helm_values = load_yaml(ROOT / 'helm' / 'safelytold' / 'values.yaml') or {}
    global_values = helm_values.get('global') or {}
    if global_values.get('environment') == 'production' and global_values.get('devAuthBypass') is not False:
        fail('production Helm values must set global.devAuthBypass to false')

    features = load_yaml(ROOT / 'config' / 'features.yaml') or {}
    missing_prohibitions = REQUIRED_PROHIBITIONS - set(features.get('prohibited') or [])
    if missing_prohibitions:
        fail(f'AI/product prohibition list is incomplete: {sorted(missing_prohibitions)}')

    identity_source = (ROOT / 'services' / 'reporter_identity_service' / 'app' / 'main.py').read_text(encoding='utf-8')
    for required in ['VaultAccessRequest', 'VaultAccessApproval', 'REQUIRED_APPROVALS = 2', 'requester_subject_id']:
        if required not in identity_source:
            fail(f'identity-vault dual-control foundation is missing marker: {required}')


def validate_no_embedded_production_secrets() -> None:
    secret_patterns = [
        re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
        re.compile(r'AKIA[0-9A-Z]{16}'),
    ]
    for path in ROOT.rglob('*'):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix in {'.zip', '.png', '.jpg', '.jpeg', '.webp', '.pyc'}:
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        if any(pattern.search(text) for pattern in secret_patterns):
            fail(f'possible production secret in {path.relative_to(ROOT)}')


def validate_inventory() -> None:
    expected = [
        'docs/COMPONENT_INVENTORY.md',
        'docs/security/threat-model.md',
        'docs/security/trust-charter.md',
        'docs/security/role-matrix.md',
        'docs/architecture/blockchain-security.md',
        'docs/architecture/system-context.md',
        'docs/ai/governance.md',
        'runbooks/privacy-security-incident.md',
        'runbooks/blockchain-reconciliation.md',
        'legal-packs/za.yaml',
        'legal-packs/eu.yaml',
        'legal-packs/uk.yaml',
        'legal-packs/us.yaml',
        'helm/safelytold/values.yaml',
        'terraform/environments/dev/main.tf',
        'blockchain/besu/README.md',
        'contracts/asyncapi.yaml',
    ]
    for item in expected:
        if not (ROOT / item).exists():
            fail(f'missing foundation component: {item}')


def main() -> None:
    service_count = validate_services()
    event_count = validate_events()
    json_count, yaml_count = validate_serialised_files()
    validate_compose()
    validate_security_controls()
    validate_no_embedded_production_secrets()
    validate_inventory()

    print(
        'Foundation validation passed: '
        f'{service_count} services, {event_count} event contracts, '
        f'{json_count} JSON files and {yaml_count} YAML files.'
    )


if __name__ == '__main__':
    main()
