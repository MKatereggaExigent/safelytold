'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { DEFAULT_SESSION, type Session } from './api';

/* ------------------------------------------------------------------ */
/* Session                                                             */
/* ------------------------------------------------------------------ */

const SESSION_STORAGE_KEY = 'wpc:session';

interface SessionContextValue {
  session: Session;
  setSession: (patch: Partial<Session>) => void;
  resetSession: () => void;
}

const SessionContext = createContext<SessionContextValue | null>(null);

function readStoredSession(): Session | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<Session>;
    return { ...DEFAULT_SESSION, ...parsed };
  } catch {
    return null;
  }
}

/* ------------------------------------------------------------------ */
/* Theme                                                               */
/* ------------------------------------------------------------------ */

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextValue {
  theme: Theme;
  resolved: 'light' | 'dark';
  setTheme: (t: Theme) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

function systemTheme(): 'light' | 'dark' {
  return typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches
    ? 'dark'
    : 'light';
}

function readStoredTheme(): Theme {
  if (typeof window === 'undefined') return 'system';
  const stored = localStorage.getItem('wpc:theme');
  if (stored === 'light' || stored === 'dark' || stored === 'system') return stored;
  return 'system';
}

/* ------------------------------------------------------------------ */
/* i18n                                                                */
/* ------------------------------------------------------------------ */

interface I18nContextValue {
  locale: string;
  setLocale: (l: string) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
  /** Merge a runtime dictionary (e.g. GPT-translated) for a locale. */
  registerDictionary: (locale: string, dict: Record<string, string>) => void;
}

const I18nContext = createContext<I18nContextValue | null>(null);

const LOCALE_STORAGE_KEY = 'wpc:locale';
const I18N_EXTRA_KEY = 'wpc:i18n:extra';

function readExtraDictionaries(): Record<string, Record<string, string>> {
  if (typeof window === 'undefined') return {};
  try {
    return JSON.parse(localStorage.getItem(I18N_EXTRA_KEY) ?? '{}') as Record<string, Record<string, string>>;
  } catch {
    return {};
  }
}

/* ------------------------------------------------------------------ */
/* Toasts                                                              */
/* ------------------------------------------------------------------ */

export type ToastTone = 'ok' | 'danger' | 'warn' | 'info';

export interface Toast {
  id: string;
  tone: ToastTone;
  message: string;
}

interface ToastContextValue {
  push: (message: string, tone?: ToastTone) => void;
  toasts: Toast[];
  dismiss: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

/* ------------------------------------------------------------------ */
/* Provider                                                            */
/* ------------------------------------------------------------------ */

export interface FoundationProviderProps {
  children: ReactNode;
  /** locale -> dictionary map. If omitted the app renders with default strings. */
  messages?: Record<string, Record<string, string>>;
  defaultLocale?: string;
}

export function FoundationProvider({ children, messages = {}, defaultLocale = 'en' }: FoundationProviderProps) {
  const [session, setSessionState] = useState<Session>(() => readStoredSession() ?? DEFAULT_SESSION);
  const [theme, setThemeState] = useState<Theme>(() => readStoredTheme());
  const [locale, setLocaleState] = useState<string>(
    () => (typeof window !== 'undefined' ? (localStorage.getItem(LOCALE_STORAGE_KEY) ?? defaultLocale) : defaultLocale),
  );
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());
  const [extra, setExtra] = useState<Record<string, Record<string, string>>>(() => readExtraDictionaries());

  useEffect(() => {
    localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
  }, [session]);

  const setSession = useCallback((patch: Partial<Session>) => {
    setSessionState((prev) => ({ ...prev, ...patch }));
  }, []);

  const resetSession = useCallback(() => {
    setSessionState(DEFAULT_SESSION);
  }, []);

  const resolved = theme === 'system' ? systemTheme() : theme;
  useEffect(() => {
    document.documentElement.dataset.theme = resolved;
  }, [resolved]);

  const setTheme = useCallback((t: Theme) => {
    setThemeState(t);
    localStorage.setItem('wpc:theme', t);
  }, []);

  const setLocale = useCallback((l: string) => {
    setLocaleState(l);
    localStorage.setItem(LOCALE_STORAGE_KEY, l);
  }, []);

  const registerDictionary = useCallback((l: string, dict: Record<string, string>) => {
    setExtra((prev) => {
      const existing = prev[l] ?? {};
      let changed = false;
      for (const [k, v] of Object.entries(dict)) {
        if (existing[k] !== v) {
          changed = true;
          break;
        }
      }
      if (!changed) return prev;
      const next = { ...prev, [l]: { ...existing, ...dict } };
      try {
        localStorage.setItem(I18N_EXTRA_KEY, JSON.stringify(next));
      } catch {
        /* storage unavailable */
      }
      return next;
    });
  }, []);

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) => {
      const current = { ...(messages[locale] ?? {}), ...(extra[locale] ?? {}) };
      const fallback = messages[defaultLocale] ?? {};
      let text = current[key] ?? (locale !== defaultLocale ? fallback[key] : undefined) ?? key;
      if (vars) {
        for (const [k, v] of Object.entries(vars)) text = text.replaceAll(`{${k}}`, String(v));
      }
      return text;
    },
    [locale, messages, defaultLocale, extra],
  );

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
  }, []);

  const push = useCallback(
    (message: string, tone: ToastTone = 'info') => {
      const id = crypto.randomUUID();
      setToasts((prev) => [...prev.slice(-3), { id, tone, message }]);
      const timer = setTimeout(() => dismiss(id), 6000);
      timers.current.set(id, timer);
    },
    [dismiss],
  );

  useEffect(() => {
    const cleanup = timers.current;
    return () => cleanup.forEach((timer) => clearTimeout(timer));
  }, []);

  const sessionValue = useMemo(() => ({ session, setSession, resetSession }), [session, setSession, resetSession]);
  const themeValue = useMemo(() => ({ theme, resolved, setTheme }), [theme, resolved, setTheme]);
  const i18nValue = useMemo(
    () => ({ locale, setLocale, t, registerDictionary }),
    [locale, setLocale, t, registerDictionary],
  );
  const toastValue = useMemo(() => ({ push, toasts, dismiss }), [push, toasts, dismiss]);

  return (
    <SessionContext.Provider value={sessionValue}>
      <ThemeContext.Provider value={themeValue}>
        <I18nContext.Provider value={i18nValue}>
          <ToastContext.Provider value={toastValue}>{children}</ToastContext.Provider>
        </I18nContext.Provider>
      </ThemeContext.Provider>
    </SessionContext.Provider>
  );
}

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error('useSession must be used within FoundationProvider');
  return ctx;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within FoundationProvider');
  return ctx;
}

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useI18n must be used within FoundationProvider');
  return ctx;
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within FoundationProvider');
  return ctx;
}
