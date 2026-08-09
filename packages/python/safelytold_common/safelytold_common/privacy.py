from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

SENSITIVE = {
    'allegation', 'body', 'content', 'description', 'evidence', 'identity', 'message',
    'narrative', 'password', 'private_key', 'recovery_secret', 'secret', 'statement',
    'token', 'email', 'phone', 'address', 'ip_address', 'device_fingerprint',
}
EMAIL = re.compile(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', re.I)
PHONE = re.compile(r'(?<!\d)(?:\+?\d[\d ()-]{7,}\d)(?!\d)')
UUID = re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')


def redact_text(value: str) -> str:
    return PHONE.sub('[REDACTED_PHONE]', EMAIL.sub('[REDACTED_EMAIL]', value))


def redact_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return redact_mapping(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item) for item in value)
    if isinstance(value, str):
        return redact_text(value)
    return value


def redact_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, item in value.items():
        output[key] = '[REDACTED]' if any(term in key.lower() for term in SENSITIVE) else redact_value(item)
    return output


def _unsafe_paths(value: Any, path: str = 'data') -> list[str]:
    violations: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            current = f'{path}.{key}'
            if any(term in key.lower() for term in SENSITIVE):
                violations.append(current)
            violations.extend(_unsafe_paths(item, current))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            violations.extend(_unsafe_paths(item, f'{path}[{index}]'))
    elif isinstance(value, str) and not UUID.fullmatch(value) and (EMAIL.search(value) or PHONE.search(value)):
        violations.append(path)
    return violations


def assert_event_safe(value: Mapping[str, Any]) -> None:
    bad = _unsafe_paths(value)
    if bad:
        raise ValueError(f'Sensitive data forbidden in events at: {sorted(set(bad))}')
