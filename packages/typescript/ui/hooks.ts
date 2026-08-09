'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  createRecord,
  gatewayHealth,
  listAllMailboxConcerns,
  listRecords,
  policyDecide,
  type PolicyOutput,
  type RecordView,
  type ServiceSlug,
  type Session,
} from './api';
import { useSession } from './context';

export interface UseRecordsResult {
  records: RecordView[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useRecords(
  service: ServiceSlug,
  kind?: string,
  sessionOverride?: Session | null,
): UseRecordsResult {
  const { session } = useSession();
  const [records, setRecords] = useState<RecordView[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);
  const sessionKey = sessionOverride ? JSON.stringify(sessionOverride) : 'session';

  useEffect(() => {
    const active = { current: true };
    setLoading(true);
    const s = sessionOverride === undefined ? session : sessionOverride;
    listRecords(service, s)
      .then((list) => {
        if (!active.current) return;
        setRecords(kind ? list.filter((r) => r.kind === kind) : list);
        setError(null);
      })
      .catch((err) => {
        if (active.current) setError(err instanceof Error ? err.message : 'Request failed');
      })
      .finally(() => {
        if (active.current) setLoading(false);
      });
    return () => {
      active.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [service, kind, version, sessionKey, session]);

  const refresh = useCallback(() => setVersion((v) => v + 1), []);
  return { records, loading, error, refresh };
}

export interface MailboxConcernRow {
  id: string;
  case_id: string;
  risk_band: string;
  details: string;
  status: string;
  created_at: string;
}

export interface UseMailboxConcernsResult {
  concerns: MailboxConcernRow[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useMailboxConcerns(sessionOverride?: Session | null): UseMailboxConcernsResult {
  const { session } = useSession();
  const [concerns, setConcerns] = useState<MailboxConcernRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);
  const sessionKey = sessionOverride ? JSON.stringify(sessionOverride) : 'session';

  useEffect(() => {
    const active = { current: true };
    setLoading(true);
    const s = sessionOverride === undefined ? session : sessionOverride;
    listAllMailboxConcerns(s)
      .then((list) => {
        if (!active.current) return;
        setConcerns(list);
        setError(null);
      })
      .catch((err) => {
        if (!active.current) return;
        setError(err instanceof Error ? err.message : 'Could not load concerns');
      })
      .finally(() => {
        if (active.current) setLoading(false);
      });
    return () => {
      active.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [version, sessionKey, session]);

  const refresh = useCallback(() => setVersion((v) => v + 1), []);
  return { concerns, loading, error, refresh };
}

export interface UseCreateResult {
  create: (kind: string, payload: Record<string, unknown>) => Promise<RecordView>;
  busy: boolean;
}

export function useCreateRecord(service: ServiceSlug, sessionOverride?: Session | null): UseCreateResult {
  const { session } = useSession();
  const [busy, setBusy] = useState(false);
  const create = useCallback(
    async (kind: string, payload: Record<string, unknown>) => {
      const s = sessionOverride === undefined ? session : sessionOverride;
      setBusy(true);
      try {
        return await createRecord(service, kind, payload, s);
      } finally {
        setBusy(false);
      }
    },
    [service, session, sessionOverride],
  );
  return { create, busy };
}

export interface UsePolicyDecisionResult {
  decide: (input: Omit<Parameters<typeof policyDecide>[0], 'roles' | 'subject_id' | 'purpose' | 'tenant_id'>, extra?: Partial<Parameters<typeof policyDecide>[0]>) => Promise<PolicyOutput>;
  busy: boolean;
}

export function usePolicyDecision(): UsePolicyDecisionResult {
  const { session } = useSession();
  const [busy, setBusy] = useState(false);
  const decide = useCallback(
    async (input: Omit<Parameters<typeof policyDecide>[0], 'roles' | 'subject_id' | 'purpose' | 'tenant_id'>, extra?: Partial<Parameters<typeof policyDecide>[0]>) => {
      setBusy(true);
      try {
        return await policyDecide(
          {
            tenant_id: session.tenantId,
            subject_id: session.subject,
            roles: session.roles,
            purpose: session.purpose,
            ...input,
            ...extra,
          },
          session,
        );
      } finally {
        setBusy(false);
      }
    },
    [session],
  );
  return { decide, busy };
}

export interface UseGatewayHealthResult {
  health: Record<string, { status: string }> | null;
  loading: boolean;
  refresh: () => void;
}

export function useGatewayHealth(): UseGatewayHealthResult {
  const [health, setHealth] = useState<Record<string, { status: string }> | null>(null);
  const [loading, setLoading] = useState(true);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let active = true;
    gatewayHealth()
      .then((h) => {
        if (active) setHealth(h);
      })
      .catch(() => {
        if (active) setHealth(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [version]);

  return { health, loading, refresh: () => setVersion((v) => v + 1) };
}

/* ------------------------------------------------------------------ */
/* Formatting helpers shared across apps                               */
/* ------------------------------------------------------------------ */

export function formatDate(value?: string | number | Date): string {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return `${d.toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'UTC' })} UTC`;
}

export function formatBytes(value?: number): string {
  if (!value && value !== 0) return '—';
  if (value < 1024) return `${value} B`;
  const units = ['KB', 'MB', 'GB'];
  let size = value;
  let unit = -1;
  do {
    size /= 1024;
    unit += 1;
  } while (size >= 1024 && unit < units.length - 1);
  return `${size.toFixed(size < 10 ? 2 : 1)} ${units[unit]}`;
}

export function truncate(value: string, max = 80): string {
  if (value.length <= max) return value;
  return `${value.slice(0, max - 1)}…`;
}

export function shortId(value: string, length = 8): string {
  if (!value) return '—';
  return value.length <= length ? value : value.slice(0, length);
}

/* ------------------------------------------------------------------ */
/* Pagination                                                          */
/* ------------------------------------------------------------------ */

export interface UsePaginationResult<T> {
  page: number;
  onChange: (page: number) => void;
  pageItems: T[];
  totalPages: number;
  totalItems: number;
  from: number;
  to: number;
}

/** Slices `items` into pages of `pageSize`. Clamps the current page when
 * the list shrinks (e.g. after a delete) and returns a safe 1-based range. */
export function usePagination<T>(items: T[], pageSize = 8): UsePaginationResult<T> {
  const [page, setPageRaw] = useState(1);
  const totalItems = items.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));

  useEffect(() => {
    if (page > totalPages) setPageRaw(totalPages);
  }, [page, totalPages]);

  const safePage = Math.min(page, totalPages);
  const start = (safePage - 1) * pageSize;
  return {
    page: safePage,
    onChange: (p: number) => setPageRaw(Math.max(1, Math.min(p, totalPages))),
    pageItems: items.slice(start, start + pageSize),
    totalPages,
    totalItems,
    from: totalItems === 0 ? 0 : start + 1,
    to: Math.min(start + pageSize, totalItems),
  };
}
