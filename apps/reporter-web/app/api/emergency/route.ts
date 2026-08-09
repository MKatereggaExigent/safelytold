import { NextRequest, NextResponse } from 'next/server';
import { EMERGENCY_NUMBERS, type EmergencyEntry } from '../../../lib/emergency-numbers';
import { COUNTRIES } from '../../../lib/country-names';
import type { EmergencyResult } from '../../../lib/emergency';

export const runtime = 'nodejs';

interface LiveResponse {
  Country?: { Name?: string; ISOCode?: string };
  Police?: { All?: Array<string | null> };
  Fire?: { All?: Array<string | null> };
  Ambulance?: { All?: Array<string | null> };
  Dispatch?: { All?: Array<string | null>; GSM?: Array<string | null>; Fixed?: Array<string | null> };
  Member_112?: boolean;
}

const LIVE_ENDPOINT = 'https://emergencynumberapi.com/api/country/';
const LIVE_TIMEOUT_MS = 4000;

function clean(values?: Array<string | null>): string[] {
  return [...new Set((values ?? []).filter((v): v is string => typeof v === 'string' && v.trim() !== ''))];
}

function toResult(entry: EmergencyEntry, name: string, code: string, source: 'live' | 'cached'): EmergencyResult {
  return {
    country: { name, code },
    police: entry.police,
    fire: entry.fire,
    ambulance: entry.ambulance,
    dispatch: entry.dispatch,
    member112: entry.member112,
    source,
    fetchedAt: new Date().toISOString(),
  };
}

async function fetchLive(code: string): Promise<EmergencyResult | null> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), LIVE_TIMEOUT_MS);
  try {
    const res = await fetch(`${LIVE_ENDPOINT}${code}`, {
      signal: controller.signal,
      headers: { accept: 'application/json', 'user-agent': 'safelytold-reporter/1.0' },
      cache: 'no-store',
    });
    if (!res.ok) return null;
    const data = (await res.json()) as LiveResponse;
    const iso = data.Country?.ISOCode;
    if (!iso || !data.Police && !data.Dispatch) return null;
    return {
      country: { name: data.Country?.Name ?? code, code: iso.toUpperCase() },
      police: clean(data.Police?.All),
      fire: clean(data.Fire?.All),
      ambulance: clean(data.Ambulance?.All),
      dispatch: [...clean(data.Dispatch?.All), ...clean(data.Dispatch?.GSM), ...clean(data.Dispatch?.Fixed)],
      member112: data.Member_112 === true,
      source: 'live',
      fetchedAt: new Date().toISOString(),
    };
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

export async function GET(request: NextRequest) {
  const code = (request.nextUrl.searchParams.get('country') ?? '').trim().toUpperCase();
  if (!/^[A-Z]{2}$/.test(code)) {
    return NextResponse.json({ error: 'Provide a two-letter ISO country code, e.g. ?country=ZA.' }, { status: 400 });
  }

  const result = await fetchLive(code);
  const source: 'live' | 'cached' = result ? 'live' : 'cached';
  const final = result ?? (() => {
    const cached = EMERGENCY_NUMBERS[code];
    if (!cached) return null;
    const name = COUNTRIES.find(([c]) => c === code)?.[1] ?? code;
    return toResult(cached, name, code, 'cached');
  })();

  if (!final) {
    return NextResponse.json({ error: `No emergency numbers found for ${code}.` }, { status: 404 });
  }

  const response = NextResponse.json(final);
  response.headers.set(
    'Cache-Control',
    source === 'live'
      ? 'public, s-maxage=600, stale-while-revalidate=86400'
      : 'public, s-maxage=86400',
  );
  return response;
}
