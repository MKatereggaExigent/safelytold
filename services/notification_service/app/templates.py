from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

TEMPLATE_DIR = Path(__file__).parent / 'templates'

_PLACEHOLDER = re.compile(r'\{[^}]+\}')
_EMAIL = re.compile(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', re.I)
_PHONE = re.compile(r'(?<!\d)(?:\+?\d[\d ()-]{7,}\d)(?!\d)')
_UUID = re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')

LOCALES = ('en', 'af', 'zu')


class NeutralTemplate(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=2000)


class _Store(BaseModel):
    mailbox_nudge_v1: NeutralTemplate


def _load(locale: str) -> _Store:
    path = TEMPLATE_DIR / f'{locale}.json'
    if not path.exists():
        raise ValueError(f'Unknown notification locale: {locale}')
    return _Store.model_validate(json.loads(path.read_text(encoding='utf-8')))


def _assert_neutral(value: str) -> None:
    if _PLACEHOLDER.search(value):
        raise ValueError('Neutral templates must not contain variables or case content')
    if _EMAIL.search(value) or _PHONE.search(value) or _UUID.search(value):
        raise ValueError('Neutral templates must not contain contact details or identifiers')


def assert_neutral(subject: str, body: str) -> None:
    """Public neutrality contract check used by admin template overrides."""
    _assert_neutral(subject)
    _assert_neutral(body)


def render_subject(template_code: str, locale: str) -> str:
    store = _load(locale)
    value = getattr(store, template_code, None)
    if value is None:
        raise KeyError(f'Unknown template code: {template_code}')
    _assert_neutral(value.subject)
    return value.subject


def render_body(template_code: str, locale: str) -> str:
    store = _load(locale)
    value = getattr(store, template_code, None)
    if value is None:
        raise KeyError(f'Unknown template code: {template_code}')
    _assert_neutral(value.body)
    return value.body


def list_locales() -> list[str]:
    return sorted(LOCALES)


def list_templates() -> list[str]:
    return ['mailbox_nudge_v1']
