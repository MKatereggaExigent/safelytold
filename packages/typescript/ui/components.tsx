'use client';

import { useEffect, useId, type ButtonHTMLAttributes, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from 'react';
import { useTheme, useToast } from './context';

export type Tone = 'neutral' | 'accent' | 'ok' | 'warn' | 'danger' | 'info' | 'violet';

const TONE_CLASS: Record<Tone, string> = {
  neutral: 'tone-neutral',
  accent: 'tone-accent',
  ok: 'tone-ok',
  warn: 'tone-warn',
  danger: 'tone-danger',
  info: 'tone-info',
  violet: 'tone-violet',
};

/* ------------------------------------------------------------------ */
/* Button                                                              */
/* ------------------------------------------------------------------ */

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: ReactNode;
}

export function Button({ variant = 'primary', size = 'md', loading, icon, className = '', children, disabled, ...props }: ButtonProps) {
  const cls = `btn btn-${variant} btn-${size}${className ? ` ${className}` : ''}`;
  return (
    <button className={cls} disabled={disabled || loading} {...props}>
      {loading ? <span className="spinner" aria-hidden /> : icon ? <span className="btn-icon" aria-hidden>{icon}</span> : null}
      {children}
    </button>
  );
}

/* ------------------------------------------------------------------ */
/* Badges and status pills                                             */
/* ------------------------------------------------------------------ */

export function Badge({ tone = 'accent', children }: { tone?: Tone; children: ReactNode }) {
  return <span className={`badge ${TONE_CLASS[tone]}`}>{children}</span>;
}

const STATUS_TONES: Record<string, Tone> = {
  active: 'ok',
  clean: 'ok',
  approved: 'ok',
  allow: 'ok',
  open: 'info',
  triage: 'info',
  pending: 'warn',
  reviewing: 'warn',
  require_approval: 'warn',
  unverified: 'warn',
  await: 'warn',
  denied: 'danger',
  denied_high_risk: 'danger',
  malware_detected: 'danger',
  recuse: 'danger',
  closed: 'neutral',
  resolved: 'neutral',
  expired: 'neutral',
  revealed: 'neutral',
  inactive: 'neutral',
  vaulted: 'accent',
  substantiated: 'danger',
  unsubstantiated: 'ok',
  inconclusive: 'neutral',
  referred: 'info',
};

export function StatusPill({ status, label }: { status?: string; label?: string }) {
  const key = (status ?? '').toLowerCase();
  const tone = STATUS_TONES[key] ?? 'neutral';
  return <span className={`pill ${TONE_CLASS[tone]}`}>{label ?? (status ?? 'Unknown')}</span>;
}

/* ------------------------------------------------------------------ */
/* Panel / card                                                        */
/* ------------------------------------------------------------------ */

interface PanelProps {
  title?: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  padded?: boolean;
}

export function Panel({ title, subtitle, actions, children, className = '', padded = true }: PanelProps) {
  return (
    <section className={`panel${padded ? ' panel-padded' : ''}${className ? ` ${className}` : ''}`}>
      {(title || actions) && (
        <div className="panel-head">
          <div>
            {title && <h2 className="panel-title">{title}</h2>}
            {subtitle && <p className="panel-subtitle">{subtitle}</p>}
          </div>
          {actions && <div className="panel-actions">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  );
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`card${className ? ` ${className}` : ''}`}>{children}</div>;
}

/* ------------------------------------------------------------------ */
/* Stat                                                                */
/* ------------------------------------------------------------------ */

export function Stat({ label, value, hint, tone = 'neutral' }: { label: string; value: ReactNode; hint?: ReactNode; tone?: Tone }) {
  return (
    <div className={`stat ${TONE_CLASS[tone]}`}>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
      {hint && <div className="stat-hint">{hint}</div>}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Form controls                                                       */
/* ------------------------------------------------------------------ */

interface FieldProps {
  label?: ReactNode;
  hint?: ReactNode;
  error?: string | null;
  required?: boolean;
  children: ReactNode;
  className?: string;
}

export function Field({ label, hint, error, required, children, className = '' }: FieldProps) {
  return (
    <div className={`field${className ? ` ${className}` : ''}`}>
      {label && (
        <span className="field-label">
          {label}
          {required && <span className="req" aria-hidden> *</span>}
        </span>
      )}
      <div className="field-control">{children}</div>
      {hint && !error && <p className="field-hint">{hint}</p>}
      {error && <p className="field-error" role="alert">{error}</p>}
    </div>
  );
}

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;
}

export function Input({ invalid, className = '', ...props }: InputProps) {
  return <input className={`input${invalid ? ' input-invalid' : ''}${className ? ` ${className}` : ''}`} {...props} />;
}

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  invalid?: boolean;
}

export function Textarea({ invalid, className = '', ...props }: TextareaProps) {
  return <textarea className={`textarea${invalid ? ' input-invalid' : ''}${className ? ` ${className}` : ''}`} {...props} />;
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  options?: { value: string; label: string }[];
  placeholder?: string;
}

export function Select({ options = [], placeholder, className = '', children, ...props }: SelectProps) {
  return (
    <select className={`select${className ? ` ${className}` : ''}`} {...props}>
      {placeholder && <option value="">{placeholder}</option>}
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
      {children}
    </select>
  );
}

export function Checkbox({ label, hint, ...props }: { label: ReactNode; hint?: ReactNode } & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="checkbox">
      <input type="checkbox" {...props} />
      <span className="checkbox-box" aria-hidden />
      <span>
        <span className="checkbox-label">{label}</span>
        {hint && <span className="checkbox-hint">{hint}</span>}
      </span>
    </label>
  );
}

interface RadioCardProps {
  value: string;
  selected: boolean;
  onSelect: (value: string) => void;
  title: string;
  description: string;
  badge?: ReactNode;
  disabled?: boolean;
}

export function RadioCard({ value, selected, onSelect, title, description, badge, disabled }: RadioCardProps) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      disabled={disabled}
      onClick={() => onSelect(value)}
      className={`radio-card${selected ? ' radio-card-selected' : ''}`}
    >
      <span className="radio-card-dot" aria-hidden />
      <span className="radio-card-body">
        <span className="radio-card-title">{title}</span>
        {badge && <span className="radio-card-badge">{badge}</span>}
        <span className="radio-card-desc">{description}</span>
      </span>
    </button>
  );
}

interface SegmentedProps<T extends string> {
  options: { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
  ariaLabel?: string;
}

export function Segmented<T extends string>({ options, value, onChange, ariaLabel }: SegmentedProps<T>) {
  return (
    <div className="segmented" role="tablist" aria-label={ariaLabel}>
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          role="tab"
          aria-selected={value === o.value}
          className={`segmented-option${value === o.value ? ' segmented-active' : ''}`}
          onClick={() => onChange(o.value)}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Data table                                                          */
/* ------------------------------------------------------------------ */

export interface Column<T> {
  key: string;
  label: ReactNode;
  render?: (row: T) => ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  keyField: keyof T;
  empty?: ReactNode;
  loading?: boolean;
  caption?: string;
}

export function DataTable<T>({ columns, rows, keyField, empty, loading, caption }: DataTableProps<T>) {
  return (
    <div className="table-wrap">
      <table className="table">
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} className={c.className}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading
            ? Array.from({ length: 3 }).map((_, i) => (
                <tr key={i}>
                  {columns.map((c) => (
                    <td key={c.key}><Skeleton width={80} height={14} /></td>
                  ))}
                </tr>
              ))
            : rows.length === 0
              ? (
                <tr>
                  <td colSpan={columns.length} className="table-empty">
                    {empty ?? 'No records'}
                  </td>
                </tr>
              )
              : rows.map((row) => (
                <tr key={String(row[keyField])}>
                  {columns.map((c) => (
                    <td key={c.key} className={c.className}>{c.render ? c.render(row) : (row[c.key as keyof T] as ReactNode)}</td>
                  ))}
                </tr>
              ))}
        </tbody>
      </table>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Pagination                                                          */
/* ------------------------------------------------------------------ */

function pageNumbers(page: number, totalPages: number): (number | '…')[] {
  if (totalPages <= 7) return Array.from({ length: totalPages }, (_, i) => i + 1);
  const set = new Set<number>([1, 2, page - 1, page, page + 1, totalPages - 1, totalPages]);
  const sorted = [...set].filter((p) => p >= 1 && p <= totalPages).sort((a, b) => a - b);
  const out: (number | '…')[] = [];
  let prev = 0;
  for (const p of sorted) {
    if (p - prev > 1) out.push('…');
    out.push(p);
    prev = p;
  }
  return out;
}

export interface PaginationProps {
  page: number;
  totalPages: number;
  onChange: (page: number) => void;
  /** Optional "Showing X–Y of Z" summary. */
  totalItems?: number;
  from?: number;
  to?: number;
  label?: string;
}

export function Pagination({ page, totalPages, onChange, totalItems, from, to, label = 'Pagination' }: PaginationProps) {
  if (totalPages <= 1) return null;
  return (
    <nav className="pagination" aria-label={label}>
      {typeof totalItems === 'number' && (
        <span className="pagination-info">
          {totalItems === 0 ? 'No items' : `${from ?? 1}–${to ?? totalItems} of ${totalItems}`}
        </span>
      )}
      <div className="pagination-controls">
        <button
          type="button"
          className="pagination-btn"
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
          aria-label="Previous page"
        >
          ‹
        </button>
        {pageNumbers(page, totalPages).map((p, i) =>
          p === '…' ? (
            <span key={`e${i}`} className="pagination-ellipsis">…</span>
          ) : (
            <button
              key={p}
              type="button"
              className={`pagination-btn${p === page ? ' pagination-btn-active' : ''}`}
              aria-current={p === page ? 'page' : undefined}
              onClick={() => onChange(p)}
            >
              {p}
            </button>
          ),
        )}
        <button
          type="button"
          className="pagination-btn"
          disabled={page >= totalPages}
          onClick={() => onChange(page + 1)}
          aria-label="Next page"
        >
          ›
        </button>
      </div>
    </nav>
  );
}

/* ------------------------------------------------------------------ */
/* Tabs                                                                */
/* ------------------------------------------------------------------ */

export interface TabItem {
  id: string;
  label: string;
  icon?: ReactNode;
  count?: number;
}

export function Tabs({ tabs, active, onChange }: { tabs: TabItem[]; active: string; onChange: (id: string) => void }) {
  return (
    <div className="tabs" role="tablist">
      {tabs.map((t) => (
        <button
          key={t.id}
          role="tab"
          aria-selected={active === t.id}
          className={`tab${active === t.id ? ' tab-active' : ''}`}
          onClick={() => onChange(t.id)}
        >
          {t.icon}
          <span>{t.label}</span>
          {typeof t.count === 'number' && <span className="tab-count">{t.count}</span>}
        </button>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Modal                                                               */
/* ------------------------------------------------------------------ */

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  size?: 'sm' | 'md' | 'lg';
}

export function Modal({ open, onClose, title, children, footer, size = 'md' }: ModalProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div className="modal-overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className={`modal modal-${size}`} role="dialog" aria-modal="true" aria-label={typeof title === 'string' ? title : 'Dialog'}>
        <div className="modal-head">
          <h2 className="modal-title">{title}</h2>
          <button type="button" className="modal-close" aria-label="Close" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-foot">{footer}</div>}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Alert / empty / skeleton / stepper / code                           */
/* ------------------------------------------------------------------ */

export function Alert({ tone = 'info', title, children }: { tone?: Tone; title?: ReactNode; children?: ReactNode }) {
  return (
    <div className={`alert ${TONE_CLASS[tone]}`} role={tone === 'danger' ? 'alert' : 'status'}>
      <strong>{title}</strong>
      {children && <div className="alert-body">{children}</div>}
    </div>
  );
}

export function EmptyState({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="empty">
      <div className="empty-glyph" aria-hidden>◈</div>
      <h3 className="empty-title">{title}</h3>
      {description && <p className="empty-desc">{description}</p>}
      {action && <div className="empty-action">{action}</div>}
    </div>
  );
}

export function Skeleton({ width = '100%', height = 12, className = '' }: { width?: number | string; height?: number | string; className?: string }) {
  return <span className={`skeleton${className ? ` ${className}` : ''}`} style={{ width, height }} />;
}

export function Stepper({ steps, current }: { steps: string[]; current: number }) {
  return (
    <ol className="stepper">
      {steps.map((label, i) => (
        <li key={label} className={`step${i <= current ? ' step-done' : ''}${i === current ? ' step-current' : ''}`}>
          <span className="step-dot">{i + 1}</span>
          <span className="step-label">{label}</span>
        </li>
      ))}
    </ol>
  );
}

export function CodeBlock({ text, title, tone = 'neutral', compact }: { text: string; title?: string; tone?: Tone; compact?: boolean }) {
  const { push } = useToast();
  return (
    <div className={`code-block ${TONE_CLASS[tone]}${compact ? ' code-compact' : ''}`}>
      {title && <div className="code-title">{title}</div>}
      <pre className="code-pre">
        <code>{text}</code>
      </pre>
      <button
        type="button"
        className="code-copy"
        onClick={() => {
          navigator.clipboard?.writeText(text).catch(() => undefined);
          push('Copied to clipboard', 'ok');
        }}
      >
        Copy
      </button>
    </div>
  );
}

export function Kv({ items, columns = 2 }: { items: { label: string; value: ReactNode }[]; columns?: 1 | 2 }) {
  return (
    <dl className={`kv kv-${columns}`}>
      {items.map((item) => (
        <div key={item.label} className="kv-row">
          <dt>{item.label}</dt>
          <dd>{item.value ?? '—'}</dd>
        </div>
      ))}
    </dl>
  );
}

/* ------------------------------------------------------------------ */
/* Page header / brand / theme toggle / toaster                        */
/* ------------------------------------------------------------------ */

export function PageHeader({ eyebrow, title, subtitle, actions }: { eyebrow?: string; title: ReactNode; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <header className="page-head">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </header>
  );
}

export function Logo({
  label = 'Integrity Platform',
  title = 'HELP ME',
  compact = false,
}: {
  label?: string;
  title?: string;
  compact?: boolean;
}) {
  const gradientId = useId();
  return (
    <span className="brand">
      <svg className="brand-sigil" viewBox="0 0 64 80" role="presentation" aria-hidden focusable="false">
        <defs>
          <linearGradient id={`${gradientId}-shield`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.95" />
            <stop offset="100%" stopColor="var(--accent-strong)" stopOpacity="0.85" />
          </linearGradient>
          <radialGradient id={`${gradientId}-pulse`} cx="0.35" cy="0.2" r="0.8">
            <stop offset="0%" stopColor="rgba(255,255,255,0.9)" />
            <stop offset="70%" stopColor="rgba(255,255,255,0)" />
          </radialGradient>
        </defs>
        <path
          d="M32 4 L56 14 V36 C56 53 46 66 32 74 C18 66 8 53 8 36 V14 Z"
          fill={`url(#${gradientId}-shield)`}
          stroke="var(--accent-strong)"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
        <path
          d="M24 34 L31 41 L44 26"
          fill="none"
          stroke="var(--surface)"
          strokeWidth="4.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="21" cy="22" r="6" fill="var(--surface)" opacity="0.95" />
        <circle cx="21" cy="22" r="12" fill={`url(#${gradientId}-pulse)`} />
      </svg>
      {!compact && (
        <span className="brand-text">
          <span className="brand-title">{title}</span>
          <span className="brand-tagline">{label}</span>
        </span>
      )}
    </span>
  );
}

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const next: 'light' | 'dark' | 'system' = theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light';
  const icon = theme === 'dark' ? '☀' : theme === 'light' ? '◐' : '◍';
  return (
    <button
      type="button"
      className="icon-btn"
      onClick={() => setTheme(next)}
      aria-label={`Theme: ${theme}. Click to switch to ${next}.`}
      title={`Theme: ${theme}`}
    >
      <span aria-hidden>{icon}</span>
    </button>
  );
}

export function Toaster() {
  const { toasts, dismiss } = useToast();
  return (
    <div className="toaster" aria-live="polite">
      {toasts.map((t) => (
        <div key={t.id} className={`toast ${TONE_CLASS[t.tone]}`}>
          <span className="toast-msg">{t.message}</span>
          <button type="button" className="toast-close" aria-label="Dismiss" onClick={() => dismiss(t.id)}>×</button>
        </div>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Page transitions                                                    */
/* ------------------------------------------------------------------ */

/**
 * Wraps the routed page content and replays a fade/slide-in animation
 * whenever the route path changes, so navigation between tabs is smooth
 * instead of an abrupt swap. Scrolls to the top on each page change.
 *
 * `path` is supplied by the app shell (a small client wrapper in each
 * Next.js app that reads `usePathname()`), keeping this package
 * framework-agnostic.
 */
export function PageTransition({ path, children }: { path?: string; children: ReactNode }) {
  const pathKey = path ?? '/';

  useEffect(() => {
    if (typeof window !== 'undefined') window.scrollTo({ top: 0, left: 0, behavior: 'auto' });
  }, [pathKey]);

  return (
    <div className="page-transition" key={pathKey} data-page={pathKey}>
      {children}
    </div>
  );
}
