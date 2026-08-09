"""AI Gateway.

Provider-agnostic advisory AI. Supports a mock provider (default) and a real
OpenAI provider. Provider and credentials come from the environment:

  AI_PROVIDER=mock|openai          (default: mock)
  OPENAI_API_KEY=...               (required for AI_PROVIDER=openai)
  OPENAI_MODEL=...                 (default: gpt-4o-mini)
  OPENAI_BASE_URL=...              (default: https://api.openai.com/v1)

The gateway only produces advisory drafts - never adverse or disciplinary
decisions. Every run is flagged for human review.
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from collections import OrderedDict
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import JSON, DateTime, String
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Mapped, mapped_column

from safelytold_common.db import Base, session_factory
from safelytold_common.privacy import redact_text
from safelytold_common.service import create_app

logger = logging.getLogger(__name__)

AI_PROVIDER = os.getenv('AI_PROVIDER', 'mock').strip().lower()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '').strip()
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini').strip()
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1').rstrip('/')

TRANSLATOR_ENDPOINT = os.getenv('TRANSLATOR_ENDPOINT', 'https://api.cognitive.microsofttranslator.com').rstrip('/')
TRANSLATOR_KEY = os.getenv('TRANSLATOR_KEY', '').strip()
TRANSLATOR_REGION = os.getenv('TRANSLATOR_REGION', '').strip()

# Azure Translator uses BCP-47 codes that differ from common ISO-639 short codes.
TRANSLATOR_ALIASES = {
    'zh': 'zh-Hans',
    'pt': 'pt-PT',
    'nb': 'no',
    'he': 'iw',
    'jw': 'jv',
}

r = APIRouter(prefix='/v1/ai', tags=['ai'])


class Capability(StrEnum):
    REPORTER_WRITING = 'reporter_writing'
    ANONYMITY_SCAN = 'anonymity_scan'
    TRIAGE = 'triage_copilot'
    CHRONOLOGY = 'evidence_chronology'
    POLICY = 'policy_retrieval'
    SUMMARY = 'investigation_summary'
    TRANSLATION = 'translation'
    PATTERNS = 'pattern_analytics'
    SLA = 'sla_remediation'


PROHIBITED = {
    'truthfulness_score',
    'guilt_score',
    'credibility_score',
    'disciplinary_decision',
    'dismissal_decision',
    'promotion_decision',
    'mental_health_diagnosis',
    'employee_reputation_score',
}

CAPABILITY_DESCRIPTIONS: dict[str, str] = {
    Capability.REPORTER_WRITING.value: 'Helps a reporter draft a clear, factual narrative without coaching.',
    Capability.ANONYMITY_SCAN.value: 'Finds personal identifiers so a report can be safely anonymised.',
    Capability.TRIAGE.value: 'Summarises a report and suggests next steps; never decides an outcome.',
    Capability.CHRONOLOGY.value: 'Builds a timeline from redacted evidence and flags gaps.',
    Capability.POLICY.value: 'Answers policy questions from the supplied policy text only.',
    Capability.SUMMARY.value: 'Summarises investigation state and open items, without verdicts.',
    Capability.TRANSLATION.value: 'Translates redacted material between languages.',
    Capability.PATTERNS.value: 'Describes patterns without attributing intent to individuals.',
    Capability.SLA.value: 'Identifies process delays and suggests process-level remedies.',
}

CAPABILITY_PROMPTS: dict[str, str] = {
    Capability.REPORTER_WRITING.value: (
        'You are a writing assistant for an anonymous workplace reporting service. Help draft a clear, '
        'neutral, chronological account of the events the reporter describes. Do not add facts, do not '
        'judge the reporter, and do not advise them to withhold or exaggerate anything.'
    ),
    Capability.ANONYMITY_SCAN.value: (
        'You are an anonymity scanner. From the redacted text, list every personal identifier you can '
        'find (names, email addresses, phone numbers, ID numbers, usernames, device/IP identifiers). '
        'Return only a bullet list of the identifiers and nothing else. If there are none, say "none".'
    ),
    Capability.TRIAGE.value: (
        'You are a triage copilot for a workplace concerns team. Summarise the report in neutral language '
        'and list possible next steps. Never recommend a specific disciplinary or dismissal outcome, never '
        'score credibility, and flag any immediate safety or legal-preservation concerns.'
    ),
    Capability.CHRONOLOGY.value: (
        'You are an evidence chronology assistant. Build a dated timeline from the supplied redacted '
        'evidence. Where dates or facts are missing, mark them as gaps. Never draw conclusions about '
        'guilt, credibility, or responsibility.'
    ),
    Capability.POLICY.value: (
        'You answer only from the policy text provided. If the answer is not covered by the supplied '
        'policy, say so. Do not invent policy.'
    ),
    Capability.SUMMARY.value: (
        'You summarise an investigation state from the supplied redacted notes. List the current facts, '
        'open items, and next steps. Do not offer a verdict or any opinion on any person.'
    ),
    Capability.TRANSLATION.value: (
        'You are a translator for redacted workplace material. Translate the supplied text faithfully, '
        'preserving names, dates, and references as-is.'
    ),
    Capability.PATTERNS.value: (
        'You analyse patterns in de-identified aggregate data. Describe trends or patterns at a process '
        'level. Never attribute intent, blame, or traits to any individual.'
    ),
    Capability.SLA.value: (
        'You identify procedural delays in the supplied timeline and suggest process-level remedies. '
        'Never assign blame to any person.'
    ),
}


class Request(BaseModel):
    tenant_id: UUID
    case_id: UUID | None = None
    capability: Capability
    purpose: str
    redacted_input: str = Field(max_length=50000)
    source_refs: list[str] = Field(default_factory=list)


class CapabilityInfo(BaseModel):
    name: str
    description: str


class TranslateRequest(BaseModel):
    target_locale: str = Field(min_length=2, max_length=64)
    source_locale: str = Field(default='en', min_length=2, max_length=64)
    source: dict[str, str] = Field(default_factory=dict, max_length=1024)


TRANSLATE_SYSTEM_PROMPT = (
    'You are a professional UI translator for a workplace integrity platform. '
    'Translate each UI string faithfully into the requested target language. '
    'Keep the tone neutral and clear, and preserve any {placeholder} tokens and '
    'proper nouns exactly as-is. Return ONLY a JSON object that maps the exact '
    'same keys to the translated strings.'
)


def _parse_json(content: str) -> Any:
    text = content.strip()
    if text.startswith('```'):
        text = re.sub(r'^```[a-zA-Z]*\n?', '', text)
        text = re.sub(r'\n?```$', '', text).strip()
    return json.loads(text)


FALLBACK_LANGUAGES = [
    {'code': 'en', 'name': 'English'},
    {'code': 'af', 'name': 'Afrikaans'},
    {'code': 'zu', 'name': 'isiZulu'},
    {'code': 'xh', 'name': 'isiXhosa'},
    {'code': 'st', 'name': 'Sesotho'},
    {'code': 'tn', 'name': 'Setswana'},
    {'code': 'fr', 'name': 'French'},
    {'code': 'pt', 'name': 'Portuguese'},
    {'code': 'sw', 'name': 'Swahili'},
    {'code': 'de', 'name': 'German'},
    {'code': 'ar', 'name': 'Arabic'},
    {'code': 'hi', 'name': 'Hindi'},
    {'code': 'zh', 'name': 'Chinese'},
]


TRANSLATE_CACHE: OrderedDict[str, dict[str, str]] = OrderedDict()
TRANSLATE_CACHE_MAX = 256

# Single-flight guards: only one in-flight request per cache key computes a
# translation; every concurrent requester waits for (and reuses) the result.
# Prevents a thundering herd of users from stampeding Azure/OpenAI on a cold key.
_translate_locks: dict[str, asyncio.Lock] = {}


def _translate_lock(cache_key: str) -> asyncio.Lock:
    lock = _translate_locks.get(cache_key)
    if lock is None:
        lock = _translate_locks[cache_key] = asyncio.Lock()
    return lock


class TranslationCache(Base):
    """Persistent, content-addressed translation cache shared across all users.

    Keyed by a SHA-256 of the source dictionary plus the locale pair, so the same
    English strings are translated once globally and served forever after - across
    restarts, browsers, and users. Rows are inert data (never report content).
    """

    __tablename__ = 'translation_cache'
    cache_key: Mapped[str] = mapped_column(String(256), primary_key=True)
    source_locale: Mapped[str] = mapped_column(String(64), index=True)
    target_locale: Mapped[str] = mapped_column(String(64), index=True)
    values: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


async def _db_translate_get(cache_key: str) -> dict[str, str] | None:
    try:
        async with session_factory()() as session:
            row = await session.get(TranslationCache, cache_key)
        return dict(row.values) if row is not None else None
    except Exception:
        logger.exception('translation cache read failed; falling back to compute')
        return None


async def _db_translate_put(cache_key: str, source_locale: str, target_locale: str, values: dict[str, str]) -> None:
    if not values:
        return
    try:
        stmt = pg_insert(TranslationCache).values(
            cache_key=cache_key,
            source_locale=source_locale,
            target_locale=target_locale,
            values=values,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ).on_conflict_do_nothing(index_elements=['cache_key'])
        async with session_factory()() as session:
            await session.execute(stmt)
            await session.commit()
    except Exception:
        logger.exception('translation cache write failed; keeping in-memory only')

# Supported-languages list is fetched from Azure once and revalidated with its
# ETag every 24h (the docs say the list rarely changes). Keeps every page load
# from hitting Azure just to populate the language dropdown.
LANGUAGES_CACHE: dict[str, Any] = {}
LANGUAGES_CACHE_TTL = 86400


def _translate_cache_key(source_locale: str, target_locale: str, source: dict[str, str]) -> str:
    """Content-addressed cache key: same source text + locales always collide."""
    canonical = json.dumps(source, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    return f'{source_locale}->{target_locale}:{digest}'


def _translate_cache_get(key: str) -> dict[str, str] | None:
    entry = TRANSLATE_CACHE.get(key)
    if entry is not None:
        TRANSLATE_CACHE.move_to_end(key)
        return entry
    return None


def _translate_cache_put(key: str, values: dict[str, str]) -> None:
    TRANSLATE_CACHE[key] = values
    TRANSLATE_CACHE.move_to_end(key)
    while len(TRANSLATE_CACHE) > TRANSLATE_CACHE_MAX:
        TRANSLATE_CACHE.popitem(last=False)


async def _azure_translate(b: TranslateRequest) -> dict[str, str] | None:
    """Translate a UI dictionary using the Azure Translator Text API (138 languages).

    Returns None when the requested language pair is not supported by the NMT
    'general' system (e.g. Luganda, which Azure does not cover) so the caller can
    fall back to the LLM provider.
    """
    target = TRANSLATOR_ALIASES.get(b.target_locale, b.target_locale)
    source = TRANSLATOR_ALIASES.get(b.source_locale, b.source_locale)
    headers = {'Ocp-Apim-Subscription-Key': TRANSLATOR_KEY, 'Content-Type': 'application/json'}
    if TRANSLATOR_REGION:
        headers['Ocp-Apim-Subscription-Region'] = TRANSLATOR_REGION
    url = f'{TRANSLATOR_ENDPOINT}/translate?api-version=2026-06-06'
    # Azure accepts at most 100 text elements per request; larger dictionaries
    # (e.g. the full 617-key UI bundle) are sent in order-preserving batches.
    batch_size = 100
    items = list(b.source.items())
    translations: list[str] = []
    async with httpx.AsyncClient(timeout=60) as client:
        for start in range(0, len(items), batch_size):
            chunk = items[start : start + batch_size]
            body = {
                'inputs': [
                    {'text': text, 'language': source, 'targets': [{'language': target}]}
                    for _, text in chunk
                ]
            }
            response = await client.post(url, headers=headers, json=body)
            if response.status_code in (400, 404, 422):
                return None
            if response.status_code >= 400:
                detail = response.text[:500]
                raise HTTPException(502, f'Azure Translator error ({response.status_code}): {detail}')
            data = response.json()
            value = data.get('value') if isinstance(data, dict) else data
            for entry in value or []:
                trans = (entry.get('translations') or [{}])[0]
                translations.append(trans.get('text') or '')
    out: dict[str, str] = {}
    for (key, _), text in zip(items, translations):
        out[key] = text
    return out


async def _openai_translate(b: TranslateRequest) -> dict[str, str]:
    """Translate a UI dictionary via the LLM provider, in small concurrent batches.

    Full UI dictionaries (600+ keys) are too large for a single LLM completion -
    the model truncates its JSON response or the request times out. The dictionary
    is split into small batches, translated with a bounded number of concurrent
    calls, and merged back in order. Transient failures are retried with backoff.
    """
    batch_size = 15
    items = list(b.source.items())
    batches = [dict(items[start : start + batch_size]) for start in range(0, len(items), batch_size)]

    async def _translate_batch(batch: dict[str, str]) -> dict[str, str]:
        payload = {
            'model': OPENAI_MODEL,
            'temperature': 0.1,
            'response_format': {'type': 'json_object'},
            'messages': [
                {'role': 'system', 'content': TRANSLATE_SYSTEM_PROMPT},
                {
                    'role': 'user',
                    'content': (
                        f'Translate from {b.source_locale} to {b.target_locale}.\n'
                        f'Source dictionary (JSON):\n{json.dumps(batch, ensure_ascii=False)}'
                    ),
                },
            ],
        }
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=240) as client:
                    response = await client.post(
                        f'{OPENAI_BASE_URL}/chat/completions',
                        headers={'Authorization': f'Bearer {OPENAI_API_KEY}'},
                        json=payload,
                    )
                if response.status_code == 429 and attempt < 2:
                    await asyncio.sleep(3 * (attempt + 1))
                    continue
                if response.status_code >= 400:
                    detail = response.text[:500]
                    raise HTTPException(502, f'OpenAI provider error ({response.status_code}): {detail}')
                data = response.json()
                content = data['choices'][0]['message']['content']
                parsed = _parse_json(content)
                if not isinstance(parsed, dict):
                    raise ValueError('OpenAI provider returned a non-object translation')
                return {str(key): value for key, value in parsed.items() if isinstance(value, str)}
            except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(3 * (attempt + 1))
                    continue
                break
        raise HTTPException(502, f'OpenAI provider error after retries: {last_error}')

    semaphore = asyncio.Semaphore(4)

    async def _limited(batch: dict[str, str]) -> dict[str, str]:
        async with semaphore:
            return await _translate_batch(batch)

    results = await asyncio.gather(*(_limited(batch) for batch in batches))
    out: dict[str, str] = {}
    for result in results:
        out.update(result)
    return out


@r.get('/languages')
async def languages() -> dict[str, Any]:
    """List every language Azure Translator supports (138), for the UI selector.

    Fetched from Azure once, then served from memory and revalidated via ETag
    every 24 hours (or on any failure, the last known-good list is served).
    """
    now = time.time()
    if LANGUAGES_CACHE.get('languages') and now - LANGUAGES_CACHE['fetched_at'] < LANGUAGES_CACHE_TTL:
        return {'languages': LANGUAGES_CACHE['languages'], 'provider': 'cached'}
    headers = {}
    if LANGUAGES_CACHE.get('etag'):
        headers['If-None-Match'] = LANGUAGES_CACHE['etag']
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f'{TRANSLATOR_ENDPOINT}/languages?api-version=2026-06-06&scope=translation',
                headers=headers,
            )
            if response.status_code == 304:
                LANGUAGES_CACHE['fetched_at'] = now
                return {'languages': LANGUAGES_CACHE['languages'], 'provider': 'cached'}
            response.raise_for_status()
            data = response.json()
            translation = data.get('translation') or {}
            langs = [
                {'code': code, 'name': (info.get('name') or code)}
                for code, info in sorted(translation.items(), key=lambda kv: (kv[1].get('name') or kv[0]).lower())
            ]
            LANGUAGES_CACHE.update({
                'etag': response.headers.get('etag') or '',
                'languages': langs,
                'fetched_at': now,
            })
            return {'languages': langs, 'provider': 'azure'}
    except Exception:
        if LANGUAGES_CACHE.get('languages'):
            return {'languages': LANGUAGES_CACHE['languages'], 'provider': 'cached'}
        return {'languages': FALLBACK_LANGUAGES, 'provider': 'fallback'}


@r.post('/translate')
async def translate(b: TranslateRequest) -> dict[str, Any]:
    """Translate a UI dictionary into any of 138+ languages.

    Uses the Azure Translator Text API (cheap, 138 languages) when TRANSLATOR_KEY
    is configured. Languages Azure does not cover (e.g. Luganda) fall back to the
    GPT/OpenAI provider, then to the dev mock. Results are cached by content hash
    - first in Postgres (shared across all users and instances, survives restarts)
    then in a per-process LRU. Only the first request for a given (locale pair,
    source hash) ever reaches a paid provider; a single-flight lock stops a cold
    key from being translated by many concurrent requests at once. Only UI strings
    are sent - never report, journal or mailbox content.
    """
    if len(b.source) == 0:
        return {'target_locale': b.target_locale, 'source_locale': b.source_locale, 'values': {}}
    cache_key = _translate_cache_key(b.source_locale, b.target_locale, dict(b.source))

    async with _translate_lock(cache_key):
        values = _translate_cache_get(cache_key)
        if values is None:
            values = await _db_translate_get(cache_key)
            if values is not None:
                _translate_cache_put(cache_key, values)
        if values is None:
            if TRANSLATOR_KEY:
                values = await _azure_translate(b)
            if values is None and AI_PROVIDER == 'openai':
                if not OPENAI_API_KEY:
                    raise HTTPException(503, "AI provider 'openai' configured but OPENAI_API_KEY is not set")
                values = await _openai_translate(b)
            if values is None:
                values = dict(b.source)
            await _db_translate_put(cache_key, b.source_locale, b.target_locale, values)
            _translate_cache_put(cache_key, values)

    for key, value in b.source.items():
        values.setdefault(key, value)
    return {'target_locale': b.target_locale, 'source_locale': b.source_locale, 'values': values}


async def _openai_run(capability: str, purpose: str, redacted_input: str) -> str:
    system = CAPABILITY_PROMPTS.get(capability, CAPABILITY_PROMPTS[Capability.TRIAGE.value])
    payload = {
        'model': OPENAI_MODEL,
        'temperature': 0.2,
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': f'Purpose of this request: {purpose}\n\n{redacted_input}'},
        ],
    }
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f'{OPENAI_BASE_URL}/chat/completions',
            headers={'Authorization': f'Bearer {OPENAI_API_KEY}'},
            json=payload,
        )
        if response.status_code >= 400:
            detail = response.text[:500]
            raise HTTPException(502, f'OpenAI provider error ({response.status_code}): {detail}')
        data = response.json()
    try:
        return data['choices'][0]['message']['content']
    except (KeyError, IndexError, TypeError):
        raise HTTPException(502, 'OpenAI provider returned an unexpected response shape')


@r.post('/runs')
async def run(b: Request) -> dict[str, Any]:
    if b.purpose in PROHIBITED:
        raise HTTPException(422, 'Purpose prohibited by trust charter')
    safe = redact_text(b.redacted_input)
    if AI_PROVIDER == 'openai':
        if not OPENAI_API_KEY:
            raise HTTPException(503, "AI provider 'openai' configured but OPENAI_API_KEY is not set")
        output = await _openai_run(b.capability.value, b.purpose, safe)
        return {
            'run_id': str(uuid4()),
            'capability': b.capability,
            'status': 'awaiting_human_review',
            'output': output,
            'source_refs': b.source_refs,
            'uncertainty': 'medium',
            'requires_human_approval': True,
        }
    return {
        'run_id': str(uuid4()),
        'capability': b.capability,
        'status': 'awaiting_human_review',
        'output': f'Development mock processed {len(safe)} redacted characters.',
        'source_refs': b.source_refs,
        'uncertainty': 'high',
        'requires_human_approval': True,
    }


@r.get('/governance')
async def governance() -> dict[str, Any]:
    return {
        'capabilities': [
            CapabilityInfo(
                name=c.value,
                description=CAPABILITY_DESCRIPTIONS.get(c.value, 'Advisory draft; human decides.'),
            )
            for c in Capability
        ],
        'prohibited_purposes': sorted(PROHIBITED),
        'raw_evidence_allowed': False,
        'human_approval_default': True,
        'provider': AI_PROVIDER,
    }


app = create_app('AI Gateway', 'Bounded, provider-agnostic AI; no adverse decisions.', [r])
