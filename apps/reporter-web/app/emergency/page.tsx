'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, Button, PageHeader, Panel, Select } from '@safelytold/ui/components';
import { useI18n } from '@safelytold/ui/context';
import { COUNTRIES } from '../../lib/country-names';
import type { DetectedLocation, EmergencyResult } from '../../lib/emergency';

const REVERSE_GEO_ENDPOINT = 'https://api.bigdatacloud.net/data/reverse-geocode-client?localityLanguage=en';

async function reverseGeocode(latitude?: number, longitude?: number): Promise<DetectedLocation> {
  const params = new URLSearchParams({ localityLanguage: 'en' });
  if (typeof latitude === 'number' && typeof longitude === 'number') {
    params.set('latitude', String(latitude));
    params.set('longitude', String(longitude));
  }
  const res = await fetch(`${REVERSE_GEO_ENDPOINT}&${params.toString()}`, { signal: AbortSignal.timeout(8000) });
  if (!res.ok) throw new Error('Could not determine your location');
  const data = (await res.json()) as { city?: string; locality?: string; countryName?: string; countryCode?: string; lookupSource?: string };
  return {
    city: data.city ?? data.locality ?? '',
    countryName: data.countryName ?? '',
    countryCode: (data.countryCode ?? '').toUpperCase(),
    method: data.lookupSource === 'coordinates' ? 'gps' : 'ip',
  };
}

function getPosition(): Promise<{ latitude: number; longitude: number }> {
  return new Promise((resolve, reject) => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      reject(new Error('Geolocation unavailable'));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ latitude: pos.coords.latitude, longitude: pos.coords.longitude }),
      reject,
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 600000 },
    );
  });
}

async function fetchNumbers(code: string, fresh = false): Promise<EmergencyResult> {
  const res = await fetch(`/api/emergency?country=${encodeURIComponent(code)}`, {
    cache: fresh ? 'no-store' : 'force-cache',
  });
  const data = (await res.json()) as EmergencyResult | { error: string };
  if (!res.ok || 'error' in data) {
    throw new Error('error' in data ? data.error : 'Could not load emergency numbers');
  }
  return data;
}

function NumberRow({ label, numbers, tone }: { label: string; numbers: string[]; tone?: 'accent' | 'danger' | 'info' }) {
  const { t } = useI18n();
  return (
    <div className="emergency-service">
      <span className="emergency-service-label">{label}</span>
      {numbers.length > 0 ? (
        <span className={`emergency-number${tone ? ` emergency-number-${tone}` : ''}`}>
          {numbers.join(' · ')}
        </span>
      ) : (
        <span className="muted">{t('emg_not_listed_for_location')}</span>
      )}
    </div>
  );
}

export default function EmergencyPage() {
  const { t } = useI18n();
  const [location, setLocation] = useState<DetectedLocation | null>(null);
  const [locating, setLocating] = useState(true);
  const [locateError, setLocateError] = useState<string | null>(null);
  const [numbers, setNumbers] = useState<EmergencyResult | null>(null);
  const [numbersError, setNumbersError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const resolveNumbers = useCallback(async (code: string, fresh = false) => {
    setNumbersError(null);
    try {
      setNumbers(await fetchNumbers(code, fresh));
    } catch (err) {
      setNumbers(null);
      setNumbersError(err instanceof Error ? err.message : 'Could not load emergency numbers');
    }
  }, []);

  useEffect(() => {
    let alive = true;
    async function run() {
      setLocating(true);
      setLocateError(null);
      try {
        const coords = await getPosition().catch(() => null);
        const loc = await reverseGeocode(coords?.latitude, coords?.longitude);
        if (!alive) return;
        setLocation(loc);
        if (loc.countryCode) await resolveNumbers(loc.countryCode);
      } catch (err) {
        if (!alive) return;
        setLocateError(err instanceof Error ? err.message : 'Could not detect your location');
        setLocation(null);
      } finally {
        if (alive) setLocating(false);
      }
    }
    void run();
    return () => {
      alive = false;
    };
  }, [resolveNumbers]);

  const manualOptions = useMemo(() => COUNTRIES.slice().sort((a, b) => a[1].localeCompare(b[1])), []);

  async function onManual(code: string) {
    if (!code) return;
    setLocation({ city: '', countryName: '', countryCode: code, method: 'manual' });
    await resolveNumbers(code);
  }

  async function refresh() {
    if (!location?.countryCode) return;
    setRefreshing(true);
    try {
      await resolveNumbers(location.countryCode, true);
    } finally {
      setRefreshing(false);
    }
  }

  const locationLabel = location
    ? location.method === 'manual'
      ? t('emg_showing_numbers_for', { n: COUNTRIES.find(([c]) => c === location.countryCode)?.[1] ?? location.countryCode })
      : location.city
        ? `${location.city}, ${location.countryName}`
        : location.countryName
    : '';

  return (
    <main className="shell">
      <PageHeader
        eyebrow={t('emg_eyebrow')}
        title={t('emg_title')}
        subtitle={t('emg_subtitle')}
      />

      {locating && (
        <Alert tone="info" title={t('emg_locating_title')}>
          <p>{t('emg_locating_body')}</p>
        </Alert>
      )}

      {locateError && !location && (
        <Alert tone="warn" title={t('emg_locate_error_title')}>
          <p>{t('emg_locate_error_body')}</p>
        </Alert>
      )}

      {location && (
        <Panel title={t('emg_your_location_title')} subtitle={location.method === 'manual' ? t('emg_method_manual') : location.method === 'gps' ? t('emg_method_gps') : t('emg_method_ip')}>
          <div className="row" style={{ justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
            <strong className="emergency-location-label">{locationLabel}</strong>
            <div className="row" style={{ gap: 8 }}>
              <Button variant="secondary" size="sm" onClick={() => { window.location.reload(); }}>{t('emg_use_my_location')}</Button>
              <Button variant="ghost" size="sm" onClick={refresh} loading={refreshing} disabled={!numbers}>{t('emg_refresh_numbers')}</Button>
            </div>
          </div>
        </Panel>
      )}

      <Panel title={t('emg_choose_country_title')} subtitle={t('emg_choose_country_subtitle')}>
        <Select
          aria-label={t('emg_country_aria')}
          value={location?.countryCode ?? ''}
          onChange={(e) => onManual(e.target.value)}
          placeholder={t('emg_select_country_placeholder')}
        >
          {manualOptions.map(([code, name]) => (
            <option key={code} value={code}>{name}</option>
          ))}
        </Select>
      </Panel>

      {numbersError && <Alert tone="danger" title={t('emg_numbers_error_title')}>{numbersError}</Alert>}

      {numbers && (
        <>
          {numbers.member112 && (
            <Panel className="emergency-primary">
              <div className="emergency-primary-head">
                <span className="emergency-primary-label">{t('emg_in_emergency_call')}</span>
                <span className="emergency-primary-number">112</span>
              </div>
              <p className="muted" style={{ margin: 0 }}>
                {t('emg_112_works', { n: numbers.country.name })}
              </p>
            </Panel>
          )}

          <div className="grid grid-3">
            <div className="emergency-service emergency-service-card">
              <span className="emergency-service-label">{t('emg_police')}</span>
              {numbers.police.length > 0 ? (
                <span className="emergency-number">{numbers.police.join(' · ')}</span>
              ) : (
                <span className="muted">{t('emg_not_listed')}</span>
              )}
            </div>
            <div className="emergency-service emergency-service-card">
              <span className="emergency-service-label">{t('emg_fire')}</span>
              {numbers.fire.length > 0 ? (
                <span className="emergency-number">{numbers.fire.join(' · ')}</span>
              ) : (
                <span className="muted">{t('emg_not_listed')}</span>
              )}
            </div>
            <div className="emergency-service emergency-service-card">
              <span className="emergency-service-label">{t('emg_medical')}</span>
              {numbers.ambulance.length > 0 ? (
                <span className="emergency-number">{numbers.ambulance.join(' · ')}</span>
              ) : (
                <span className="muted">{t('emg_not_listed')}</span>
              )}
            </div>
          </div>

          {numbers.dispatch.length > 0 && (
            <Panel title={t('emg_general_emergency_line')}>
              <NumberRow label={t('emg_all_services')} numbers={numbers.dispatch} tone="accent" />
            </Panel>
          )}

          <Alert tone="info" title={numbers.source === 'live' ? t('emg_numbers_refreshed_live') : t('emg_numbers_refreshed_bundled')}>
            <p>
              {numbers.source === 'live'
                ? t('emg_fetched_live_at', { n: new Date(numbers.fetchedAt).toLocaleTimeString() })
                : t('emg_bundled_fallback')}{' '}
              {t('emg_verify_locally')}
            </p>
          </Alert>
        </>
      )}

      <Alert tone="danger" title={t('emg_in_danger_title')}>
        <ul>
          <li>{t('emg_danger_leave')}</li>
          <li>{t('emg_danger_112_lock')}</li>
          <li>{t('emg_danger_text911')}</li>
          <li>{t('emg_danger_not_service')}</li>
        </ul>
      </Alert>

      <Alert tone="warn" title={t('emg_about_location_title')}>
        <p>{t('emg_about_location_body')}</p>
      </Alert>

      <p className="muted">
        <Link href="/">{t('emg_back_to_platform')}</Link>
      </p>
    </main>
  );
}
