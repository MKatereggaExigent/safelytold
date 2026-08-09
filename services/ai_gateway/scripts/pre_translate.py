"""Pre-translate UI dictionaries for non-Azure languages and persist them.

Languages Azure Translator does not cover (e.g. Luganda) fall back to the LLM
provider at runtime, which is slow, costly, and can time out inside a live HTTP
request. This script does that translation once, ahead of serving, writing the
result into the same `translation_cache` table the gateway reads - so the
runtime endpoint serves the language instantly with zero provider calls, for
every user and every refresh. It also writes a static messages/<locale>.json
artifact for the frontend.

Run as a one-off job with the ai-gateway image (mount the repo paths):

  docker run --rm --network safelytold_default \
    -e OPENAI_API_KEY="$OPENAI_API_KEY" \
    -e OPENAI_MODEL=gpt-4o-mini \
    -e DATABASE_URL="postgresql+asyncpg://safelytold:safelytold_dev_only@postgres-core:5432/ai_gateway" \
    -v <repo>/services/ai_gateway/scripts:/scripts:ro \
    -v <repo>/apps/reporter-web/messages:/messages:ro \
    <ai-gateway-image> python /scripts/pre_translate.py --locale lg

Use --locale "lg,af,zu" for several languages in one run.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, '/app')
sys.path.insert(0, '/scripts')

import httpx  # noqa: E402
from sqlalchemy.dialects.postgresql import insert as pg_insert  # noqa: E402

from safelytold_common.db import session_factory  # noqa: E402
from services.ai_gateway.app.main import (  # noqa: E402
    TRANSLATE_SYSTEM_PROMPT,
    _parse_json,
    _translate_cache_key,
)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '').strip()
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini').strip()
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1').rstrip('/')

# Characters that never appear in the target language but are common when the
# LLM drifts to a different one (gpt-4o-mini sometimes answers Igbo for `lg`).
# Dot-below vowels are not part of Luganda orthography.
LANG_REJECT_MARKERS: dict[str, str] = {
    'lg': 'ụọịẹỤỌỊẸ',
}


class WrongLanguageError(RuntimeError):
    """Raised when a translation batch came back in the wrong target language."""


async def translate_batch(client: httpx.AsyncClient, locale: str, batch: dict[str, str]) -> dict[str, str]:
    reject = LANG_REJECT_MARKERS.get(locale, '')
    messages = [
        {'role': 'system', 'content': TRANSLATE_SYSTEM_PROMPT},
        {
            'role': 'user',
            'content': f'Translate from en to {locale}.\nSource dictionary (JSON):\n{json.dumps(batch, ensure_ascii=False)}',
        },
    ]
    last_error: Exception | None = None
    for attempt in range(5):
        if attempt > 0 and reject:
            messages.append(
                {
                    'role': 'system',
                    'content': f'WARNING: the previous output was rejected because it was NOT in {locale}. '
                    f'Reply ONLY in {locale}.',
                }
            )
        payload = {
            'model': OPENAI_MODEL,
            'temperature': 0.1,
            'max_tokens': 8192,
            'response_format': {'type': 'json_object'},
            'messages': messages,
        }
        try:
            response = await client.post(
                f'{OPENAI_BASE_URL}/chat/completions',
                headers={'Authorization': f'Bearer {OPENAI_API_KEY}'},
                json=payload,
            )
            if response.status_code == 429:
                await asyncio.sleep(10 * (attempt + 1))
                continue
            if response.status_code >= 400:
                raise RuntimeError(f'OpenAI provider error ({response.status_code}): {response.text[:300]}')
            data = response.json()
            content = data['choices'][0]['message']['content']
            parsed = _parse_json(content)
            if not isinstance(parsed, dict):
                raise ValueError(f'non-object translation (content len={len(content)}, head={content[:200]!r})')
            result = {str(k): v for k, v in parsed.items() if isinstance(v, str)}
            if reject:
                bad = [k for k, v in result.items() if any(ch in v for ch in reject)]
                if bad:
                    raise WrongLanguageError(f'keys {bad[:3]}... came back in the wrong language for {locale}')
            return result
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError, WrongLanguageError) as exc:
            last_error = exc
            print(f'      retry {attempt + 1}/5 after: {exc}', file=sys.stderr)
            if attempt < 4:
                await asyncio.sleep(8 * (attempt + 1))
    raise RuntimeError(f'batch failed after retries: {last_error}')


async def translate_batch_safe(client: httpx.AsyncClient, locale: str, batch: dict[str, str], depth: int = 0) -> dict[str, str]:
    """Translate a batch, splitting it in half on hard failure to isolate bad keys.

    A single problematic string can make the LLM deterministically truncate a
    whole batch's response; halving the batch lets the good keys translate while
    the stubborn key is eventually left as the source text rather than failing
    the entire run.
    """
    try:
        return await translate_batch(client, locale, batch)
    except RuntimeError as exc:
        if depth >= 4 or len(batch) <= 1:
            print(f'  [{locale}] keys {list(batch)[:3]}... failed permanently ({exc}); keeping source', file=sys.stderr)
            return {}
        items = list(batch.items())
        mid = len(items) // 2
        print(f'  [{locale}] splitting batch of {len(batch)} keys after failure', file=sys.stderr)
        left = await translate_batch_safe(client, locale, dict(items[:mid]), depth + 1)
        right = await translate_batch_safe(client, locale, dict(items[mid:]), depth + 1)
        return {**left, **right}


async def translate_locale(locale: str, source: dict[str, str], batch_size: int) -> dict[str, str]:
    items = list(source.items())
    batches = [dict(items[start : start + batch_size]) for start in range(0, len(items), batch_size)]
    out: dict[str, str] = {}
    async with httpx.AsyncClient(timeout=300) as client:
        for index, batch in enumerate(batches, 1):
            result = await translate_batch_safe(client, locale, batch)
            out.update(result)
            print(f'  [{locale}] batch {index}/{len(batches)} ok ({len(batch)} keys)', flush=True)
    for key, value in source.items():
        out.setdefault(key, value)
    return out


async def persist(locale: str, source: dict[str, str], values: dict[str, str]) -> None:
    from services.ai_gateway.app.main import TranslationCache

    cache_key = _translate_cache_key('en', locale, source)
    stmt = pg_insert(TranslationCache).values(
        cache_key=cache_key,
        source_locale='en',
        target_locale=locale,
        values=values,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    ).on_conflict_do_nothing(index_elements=['cache_key'])
    async with session_factory()() as session:
        await session.execute(stmt)
        await session.commit()
    print(f'[{locale}] persisted cache_key={cache_key[:40]}...')


async def persist_updated(locale: str, source: dict[str, str], values: dict[str, str]) -> None:
    """Merge corrected values into an existing row (used by --fix-only)."""
    from services.ai_gateway.app.main import TranslationCache

    cache_key = _translate_cache_key('en', locale, source)
    async with session_factory()() as session:
        row = await session.get(TranslationCache, cache_key)
        if row is None:
            print(f'[{locale}] no existing row for {cache_key[:40]}...; skipping', file=sys.stderr)
            return
        merged = dict(row.values)
        merged.update(values)
        row.values = merged
        row.updated_at = datetime.now(UTC)
        await session.commit()
    print(f'[{locale}] updated {len(values)} keys in cache_key={cache_key[:40]}...')


async def main() -> int:
    parser = argparse.ArgumentParser(description='Pre-translate UI dictionaries into the persistent cache.')
    parser.add_argument('--locale', required=True, help='Comma-separated target locales (e.g. lg or lg,af,zu)')
    parser.add_argument('--source', default='/messages/en.json', help='Source English dictionary path')
    parser.add_argument('--batch', type=int, default=15, help='Keys per LLM batch')
    parser.add_argument('--write-json', action='store_true', help='Also write messages/<locale>.json artifact')
    parser.add_argument('--fix-only', help='Comma-separated keys to re-translate and merge into the existing row')
    args = parser.parse_args()

    if not OPENAI_API_KEY:
        print('OPENAI_API_KEY is required', file=sys.stderr)
        return 2

    source_path = Path(args.source)
    source = json.loads(source_path.read_text(encoding='utf-8'))
    print(f'source: {source_path} ({len(source)} keys)')

    fix_only = [k.strip() for k in args.fix_only.split(',') if k.strip()] if args.fix_only else None
    locales = [loc.strip() for loc in args.locale.split(',') if loc.strip()]
    for locale in locales:
        started = time.time()
        if fix_only:
            subset = {k: source[k] for k in fix_only if k in source}
            print(f'[{locale}] re-translating {len(subset)} keys into existing row...', flush=True)
            values = await translate_locale(locale, subset, args.batch)
            await persist_updated(locale, source, values)
            if args.write_json:
                target = source_path.parent / f'{locale}.json'
                if target.exists():
                    merged = json.loads(target.read_text(encoding='utf-8'))
                    merged.update(values)
                    target.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding='utf-8')
                    print(f'[{locale}] updated {target}')
            print(f'[{locale}] fix done in {time.time() - started:.0f}s', flush=True)
            continue
        print(f'[{locale}] translating {len(source)} keys in batches of {args.batch}...', flush=True)
        values = await translate_locale(locale, source, args.batch)
        await persist(locale, source, values)
        if args.write_json:
            target = source_path.parent / f'{locale}.json'
            target.write_text(json.dumps(values, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f'[{locale}] wrote {target}')
        non_ascii = sum(1 for v in values.values() if not v.isascii())
        print(f'[{locale}] done in {time.time() - started:.0f}s - {len(values)} keys, {non_ascii} non-ASCII', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
