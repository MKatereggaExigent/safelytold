"""Provision the isolated SafelyTold synthetic demonstration environment.

This command deliberately uses the same HTTP APIs as the staff application.
It never grants platform_super_admin and never stores a password in source.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config' / 'demo-environment.yaml'
FORBIDDEN_DEMO_ROLES = {'platform_super_admin', 'platform_security_admin', 'platform_support_admin'}


def load_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG.read_text(encoding='utf-8'))


def require_env(name: str) -> str:
    value = os.getenv(name, '').strip()
    if not value:
        raise SystemExit(f'{name} is required')
    return value


class Keycloak:
    def __init__(self, base_url: str, admin_user: str, admin_password: str):
        self.base = base_url.rstrip('/')
        with httpx.Client(timeout=20) as client:
            response = client.post(
                f'{self.base}/realms/master/protocol/openid-connect/token',
                data={'client_id': 'admin-cli', 'grant_type': 'password', 'username': admin_user, 'password': admin_password},
            )
            response.raise_for_status()
            self.headers = {'Authorization': f"Bearer {response.json()['access_token']}"}

    def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        response = httpx.request(method, f'{self.base}{path}', headers=self.headers, timeout=20, **kwargs)
        if response.status_code not in {200, 201, 204, 409}:
            raise RuntimeError(f'Keycloak {method} {path}: {response.status_code} {response.text}')
        return response

    def provision(self, config: dict[str, Any], password: str, expires_at: str) -> None:
        realm = config['keycloak']['realm']
        realm_path = f'/admin/realms/{realm}'
        source_realm = json.loads((ROOT / 'infrastructure' / 'keycloak' / 'safelytold-realm.json').read_text(encoding='utf-8'))
        security_keys = {
            'registrationAllowed', 'verifyEmail', 'duplicateEmailsAllowed', 'rememberMe',
            'resetPasswordAllowed', 'editUsernameAllowed', 'revokeRefreshToken', 'refreshTokenMaxReuse',
            'accessTokenLifespan', 'accessTokenLifespanForImplicitFlow', 'ssoSessionIdleTimeout',
            'ssoSessionMaxLifespan', 'offlineSessionIdleTimeout', 'offlineSessionMaxLifespanEnabled',
            'offlineSessionMaxLifespan', 'clientSessionIdleTimeout', 'clientSessionMaxLifespan',
            'passwordPolicy', 'bruteForceProtected', 'permanentLockout', 'maxTemporaryLockouts',
            'maxFailureWaitSeconds', 'minimumQuickLoginWaitSeconds', 'waitIncrementSeconds',
            'quickLoginCheckMilliSeconds', 'maxDeltaTimeSeconds', 'failureFactor', 'eventsEnabled',
            'eventsExpiration', 'enabledEventTypes', 'adminEventsEnabled', 'adminEventsDetailsEnabled',
        }
        active_realm = self.request('GET', realm_path).json()
        active_realm.update({key: source_realm[key] for key in security_keys})
        self.request('PUT', realm_path, json=active_realm)
        profile = self.request('GET', f'{realm_path}/users/profile').json()
        profile_by_name = {item['name']: item for item in profile.get('attributes', [])}
        governed_attributes = [
            {
                'name': 'tenant_id', 'displayName': 'Tenant identifier',
                'validations': {'pattern': {'pattern': r'^[0-9a-fA-F-]{36}$', 'error-message': 'Invalid tenant identifier'}},
                'permissions': {'view': ['admin', 'user'], 'edit': ['admin']}, 'multivalued': False,
            },
            {
                'name': 'demo_account', 'displayName': 'Demonstration account',
                'validations': {'options': {'options': ['true', 'false']}},
                'permissions': {'view': ['admin'], 'edit': ['admin']}, 'multivalued': False,
            },
            {
                'name': 'demo_expires_at', 'displayName': 'Demonstration expiry',
                'validations': {'length': {'max': 40}},
                'permissions': {'view': ['admin'], 'edit': ['admin']}, 'multivalued': False,
            },
            {
                'name': 'data_classification', 'displayName': 'Data classification',
                'validations': {'options': {'options': ['synthetic', 'production']}},
                'permissions': {'view': ['admin'], 'edit': ['admin']}, 'multivalued': False,
            },
        ]
        for item in governed_attributes:
            profile_by_name[item['name']] = item
        profile['attributes'] = list(profile_by_name.values())
        self.request('PUT', f'{realm_path}/users/profile', json=profile)
        defined_roles = self.request('GET', f'{realm_path}/roles').json()
        role_by_name = {role['name']: role for role in defined_roles}
        for role in source_realm['roles']['realm']:
            if role['name'] not in role_by_name:
                self.request('POST', f'{realm_path}/roles', json=role)
        defined_roles = self.request('GET', f'{realm_path}/roles').json()
        role_by_name = {role['name']: role for role in defined_roles}
        for persona in config['personas']:
            roles = set(persona['roles'])
            forbidden = roles & FORBIDDEN_DEMO_ROLES
            if forbidden:
                raise SystemExit(f"Demo persona {persona['username']} requests forbidden roles: {sorted(forbidden)}")
            missing = roles - role_by_name.keys()
            if missing:
                raise SystemExit(f'Roles are absent from Keycloak realm: {sorted(missing)}')
            username = persona['username']
            email = f"{username}@demo.safelytold.invalid"
            found = self.request('GET', f'{realm_path}/users', params={'username': username, 'exact': 'true'}).json()
            payload = {
                'username': username, 'email': email, 'enabled': True, 'emailVerified': True,
                'firstName': persona['display_name'].split()[0],
                'lastName': ' '.join(persona['display_name'].split()[1:]) or 'Demo',
                'attributes': {
                    'tenant_id': [config['tenant']['id']], 'demo_account': ['true'],
                    'demo_expires_at': [expires_at], 'data_classification': ['synthetic'],
                },
                'requiredActions': ['CONFIGURE_TOTP'],
            }
            if found:
                user_id = found[0]['id']
                self.request('PUT', f'{realm_path}/users/{user_id}', json=payload)
            else:
                created = self.request('POST', f'{realm_path}/users', json=payload)
                user_id = created.headers['Location'].rsplit('/', 1)[-1]
            if not found or os.getenv('DEMO_ROTATE_PASSWORD', '').lower() == 'true':
                self.request('PUT', f'{realm_path}/users/{user_id}/reset-password', json={
                    'type': 'password', 'value': password, 'temporary': True,
                })
            current = self.request('GET', f'{realm_path}/users/{user_id}/role-mappings/realm').json()
            if current:
                self.request('DELETE', f'{realm_path}/users/{user_id}/role-mappings/realm', json=current)
            self.request('POST', f'{realm_path}/users/{user_id}/role-mappings/realm', json=[role_by_name[name] for name in sorted(roles)])
            print(f'provisioned {username} ({", ".join(sorted(roles))})')

    def disable_expired(self, config: dict[str, Any]) -> None:
        realm_path = f"/admin/realms/{config['keycloak']['realm']}"
        users = self.request('GET', f'{realm_path}/users', params={'q': 'demo_account:true', 'max': 500}).json()
        now = datetime.now(UTC)
        for user in users:
            raw = (user.get('attributes', {}).get('demo_expires_at') or [''])[0]
            if raw and datetime.fromisoformat(raw.replace('Z', '+00:00')) <= now and user.get('enabled'):
                user['enabled'] = False
                self.request('PUT', f"{realm_path}/users/{user['id']}", json=user)
                print(f"disabled expired demo account {user['username']}")


class DemoApi:
    def __init__(self, base: str, config: dict[str, Any], token: str | None, dev_auth: bool):
        self.base = base.rstrip('/') + '/v1/gateway'
        if dev_auth:
            roles = sorted({role for p in config['personas'] for role in p['roles']})
            self.headers = {
                'x-tenant-id': config['tenant']['id'], 'x-purpose': 'synthetic-demo-provisioning',
                'x-dev-subject': 'demo-provisioner', 'x-dev-roles': ','.join(roles),
            }
        else:
            if not token:
                raise SystemExit('DEMO_SEED_ACCESS_TOKEN is required unless --dev-auth is explicitly used')
            self.headers = {'Authorization': f'Bearer {token}', 'x-purpose': 'synthetic-demo-provisioning'}

    def call(self, service: str, method: str, path: str, body: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> Any:
        response = httpx.request(method, f'{self.base}/{service}{path}', headers={**self.headers, **(headers or {})}, json=body, timeout=30)
        if response.status_code >= 400:
            raise RuntimeError(f'{service} {method} {path}: {response.status_code} {response.text}')
        return response.json() if response.content else None

    def seed(self) -> None:
        existing = self.call('case', 'GET', '/v1/cases?limit=500')
        if any(item.get('workflow_id') == 'synthetic-demo-v1' for item in existing):
            print('synthetic-demo-v1 records already exist; seed is idempotently skipped')
            return
        future = (datetime.now(UTC) + timedelta(days=30)).isoformat()
        cases: list[dict[str, Any]] = []
        case_specs = [
            ('critical', 'fraud', ['triage', 'open', 'investigating', 'decision_pending']),
            ('high', 'retaliation', ['triage', 'open', 'investigating']),
            ('medium', 'harassment', ['triage', 'open']),
            ('low', 'policy_breach', ['triage', 'referred']),
            ('medium', 'conflict_of_interest', ['triage', 'closed']),
            ('high', 'health_and_safety', ['triage', 'open', 'on_hold']),
        ]
        for index, (severity, category, transitions) in enumerate(case_specs, 1):
            case = self.call('case', 'POST', '/v1/cases', {
                'jurisdiction_code': 'ZA', 'severity_band': severity, 'workflow_id': 'synthetic-demo-v1',
                'policy_version_id': 'd3a00000-0000-4000-8000-000000000100',
            })
            allegation = self.call('case', 'POST', f"/v1/cases/{case['id']}/allegations", {'taxonomy_code': category})
            check = self.call('case', 'POST', f"/v1/cases/{case['id']}/conflict-checks", {
                'candidate_subject_id': 'demo.investigator', 'conflicts': [], 'decision': 'clear',
            })
            self.call('case', 'POST', f"/v1/cases/{case['id']}/assignments", {
                'subject_id': 'demo.investigator', 'role': 'investigator', 'purpose': 'Synthetic demonstration investigation',
                'valid_until': future, 'conflict_check_id': check['id'],
            })
            for status in transitions:
                case = self.call('case', 'POST', f"/v1/cases/{case['id']}/transitions", {'status': status, 'reason': 'Synthetic demo lifecycle'})
            case['_allegation_id'] = allegation['id']
            cases.append(case)

        investigation = self.call('investigation', 'POST', '/v1/investigations', {
            'case_id': cases[0]['id'], 'issue_ids': [cases[0]['_allegation_id']],
            'scope': 'Synthetic review of procurement controls and approval evidence.',
            'evidence_sources': ['Synthetic procurement register', 'Synthetic approval log'],
            'milestones': [{'name': 'Evidence review', 'status': 'complete'}],
        })
        finding = self.call('investigation', 'POST', f"/v1/investigations/{investigation['id']}/findings", {
            'allegation_id': cases[0]['_allegation_id'], 'category': 'substantiated',
            'rationale_ref': 'SYNTHETIC-DEMO-RATIONALE-001', 'evidence_ids': [], 'contrary_evidence_ids': [],
            'limitations': ['Synthetic dataset; not a real finding'],
        })
        self.call('investigation', 'POST', f"/v1/investigations/{investigation['id']}/findings/{finding['id']}/review", {'reviewer_approval_id': str(uuid4())})
        appeal = self.call('investigation', 'POST', f"/v1/investigations/{investigation['id']}/appeals", {
            'grounds_ref': 'SYNTHETIC-DEMO-APPEAL-001', 'reviewer_ref': 'demo.reviewer', 'additional_evidence_ids': [],
        })
        self.call('investigation', 'POST', f"/v1/investigations/{investigation['id']}/appeals/{appeal['id']}/decision", {'status': 'dismissed'})

        plan = self.call('protection', 'POST', '/v1/protection/plans', {
            'case_id': cases[1]['id'], 'requested_measures': ['manager separation', 'weekly check-in'],
            'approved_measures': ['manager separation', 'weekly check-in'], 'owner_ref': 'demo.protection', 'next_review_at': future,
        })
        checkin = self.call('protection', 'POST', f"/v1/protection/plans/{plan['id']}/check-ins", {'due_at': future})
        self.call('protection', 'POST', f"/v1/protection/check-ins/{checkin['id']}/complete", {'risk_band': 'low', 'notes': ['Synthetic check-in completed'], 'escalation_id': None})

        consent = self.call('privacy', 'POST', '/v1/privacy/consents', {
            'subject_ref': 'synthetic-reporter-001', 'purpose': 'Demonstrate consent-governed support referral',
            'notice_version': 'demo-v1', 'decision': 'granted',
        })
        dsr = self.call('privacy', 'POST', '/v1/privacy/requests', {
            'request_type': 'access', 'requester_ref': 'synthetic-reporter-001',
            'identity_verification_ref': 'SYNTHETIC-VERIFICATION-001', 'scope': ['case metadata'], 'jurisdiction_code': 'ZA',
        })
        self.call('privacy', 'POST', f"/v1/privacy/requests/{dsr['id']}/decision", {
            'status': 'partially_fulfilled', 'decision_notes': 'Synthetic response with third-party data restricted.',
            'restrictions': ['third-party confidentiality'],
        })
        self.call('privacy', 'POST', '/v1/privacy/breaches', {
            'incident_id': str(uuid4()), 'jurisdictions': ['ZA'], 'affected_data_classes': ['synthetic case metadata'],
        })
        provider = self.call('support', 'POST', '/v1/support/directory', {
            'jurisdiction_code': 'ZA', 'category': 'employee assistance', 'provider_name': 'Synthetic Support Provider',
            'contact_route': 'demo-only:no-contact', 'disclaimer': 'Synthetic provider record. Do not contact.',
        })
        self.call('support', 'POST', '/v1/support/referrals', {
            'case_id': cases[1]['id'], 'directory_entry_id': provider['id'], 'consent_receipt_id': consent['id'],
        })

        periods = [date.today().replace(day=1), (date.today().replace(day=1) - timedelta(days=1)).replace(day=1)]
        for period in periods:
            for metric, value, dimensions in [
                ('case.volume', 12, {'channel': 'web'}), ('case.volume', 7, {'channel': 'hotline'}),
                ('case.volume', 2, {'channel': 'email'}), ('case.closed', 8, {'outcome': 'completed'}),
            ]:
                self.call('analytics', 'POST', '/v1/analytics/observations', {'metric': metric, 'period': period.isoformat(), 'dimensions': dimensions, 'value': value})

        alert = self.call('security', 'POST', '/v1/security/alerts', {
            'alert_type': 'repeated_access_denial', 'severity': 'high', 'resource_ref': 'synthetic:case-store',
            'privacy_safe_context': {'attempt_count': 7, 'source_class': 'synthetic-demo'},
        })
        self.call('security', 'POST', f"/v1/security/alerts/{alert['id']}/triage", {
            'status': 'resolved', 'runbook': 'SEC-DEMO-01', 'containment_actions': ['Synthetic token revoked', 'Synthetic session reviewed'],
        })
        self.seed_operations(cases[0]['id'])
        print(f'created {len(cases)} synthetic cases and linked lifecycle records')

    def ensure_tenant(self, config: dict[str, Any], admin_token: str) -> None:
        headers = {'Authorization': f'Bearer {admin_token}', 'x-purpose': 'synthetic-demo-provisioning'}
        response = httpx.get(f'{self.base}/tenancy/v1/admin/tenants', headers=headers, timeout=30)
        if response.status_code >= 400:
            raise RuntimeError(f'tenancy GET: {response.status_code} {response.text}')
        if any(row['id'] == config['tenant']['id'] for row in response.json()):
            print('demo tenant already exists')
            return
        payload = {key: config['tenant'][key] for key in ('id', 'slug', 'display_name', 'home_region')}
        response = httpx.post(f'{self.base}/tenancy/v1/admin/tenants', headers=headers, json=payload, timeout=30)
        if response.status_code >= 400:
            raise RuntimeError(f'tenancy POST: {response.status_code} {response.text}')
        print('created isolated demo tenant')

    def seed_operations(self, case_id: str) -> None:
        specs = {
            'awareness': ({'title': 'Speak-up awareness pack', 'approved_by': 'demo.reviewer'}, ['approved', 'published']),
            'training': ({'course': 'Case handling fundamentals', 'score': 92, 'critical_questions_passed': True}, ['in_progress', 'passed']),
            'qa': ({'sample': 'synthetic-demo', 'critical_defects': 0}, ['approved']),
            'continuity': ({'target_rto_minutes': 60, 'target_rpo_minutes': 15, 'actual_rto_minutes': 42, 'actual_rpo_minutes': 8, 'restore_verified': True}, ['passed']),
            'coverage': ({'primary_subject': 'demo.case-manager', 'secondary_subject': 'demo.owner'}, ['active']),
            'hotline': ({'provider_call_id': 'SYNTHETIC-CALL-001', 'reporting_mode': 'verified_anonymous', 'language': 'en-ZA', 'started_at': datetime.now(UTC).isoformat(), 'case_id': case_id}, ['submitted']),
            'reporting': ({'report_name': 'Synthetic monthly management report', 'period_start': str(date.today().replace(day=1)), 'period_end': str(date.today())}, ['generated', 'approved']),
        }
        for area, (payload, transitions) in specs.items():
            row = self.call('integration', 'POST', '/v1/operations', {'area': area, 'payload': payload}, {'x-idempotency-key': f'synthetic-demo-v1-{area}'})
            for status in transitions:
                row = self.call('integration', 'POST', f"/v1/operations/{row['id']}/transition", {'status': status, 'evidence': payload})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['keycloak', 'tenant', 'seed', 'all', 'disable-expired'])
    parser.add_argument('--dev-auth', action='store_true', help='Use explicit local-only development auth headers')
    args = parser.parse_args()
    config = load_config()
    if args.action in {'keycloak', 'all', 'disable-expired'}:
        kc = Keycloak(
            os.getenv('KEYCLOAK_URL', 'http://localhost:8080'),
            require_env('KEYCLOAK_ADMIN_USERNAME'), require_env('KEYCLOAK_ADMIN_PASSWORD'),
        )
        if args.action == 'disable-expired':
            kc.disable_expired(config)
        else:
            expiry = os.getenv('DEMO_ACCOUNT_EXPIRES_AT') or (datetime.now(UTC) + timedelta(days=30)).isoformat()
            kc.provision(config, require_env('DEMO_USER_PASSWORD'), expiry)
    if args.action in {'tenant', 'seed', 'all'}:
        api = DemoApi(os.getenv('DEMO_API_BASE_URL', 'http://localhost:8101'), config, os.getenv('DEMO_SEED_ACCESS_TOKEN'), args.dev_auth)
        if args.action in {'tenant', 'all'}:
            if args.dev_auth:
                print('tenant creation skipped in development bypass; configure SEED_TENANTS with the demo tenant')
            else:
                api.ensure_tenant(config, require_env('DEMO_ADMIN_ACCESS_TOKEN'))
        if args.action in {'seed', 'all'}:
            api.seed()


if __name__ == '__main__':
    try:
        main()
    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        print(f'demo provisioning failed: {exc}', file=sys.stderr)
        raise SystemExit(1) from exc
