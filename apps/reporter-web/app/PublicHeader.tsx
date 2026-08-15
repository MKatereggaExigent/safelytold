'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Logo, ThemeToggle } from '@safelytold/ui/components';
import { useI18n } from '@safelytold/ui/context';
import { useToast } from '@safelytold/ui/context';
import { getSupportedLanguages, translateMessagesCached, type SupportedLanguage } from '@safelytold/ui/api';
import en from '../messages/en.json';

const LINKS = [
  { href: '/', key: 'nav_home' },
  { href: '/control-room', key: 'nav_control_room' },
  { href: '/trust', key: 'nav_trust' },
  { href: '/pricing', key: 'nav_pricing' },
];

const STATIC_LOCALES = ['en', 'af', 'zu'];

const FALLBACK_LANGUAGES: SupportedLanguage[] = [
  { code: 'en', name: 'English' },
  { code: 'af', name: 'Afrikaans' },
  { code: 'zu', name: 'isiZulu' },
  { code: 'xh', name: 'isiXhosa' },
  { code: 'st', name: 'Sesotho' },
  { code: 'tn', name: 'Setswana' },
  { code: 'fr', name: 'French' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'sw', name: 'Swahili' },
  { code: 'de', name: 'German' },
  { code: 'ar', name: 'Arabic' },
  { code: 'hi', name: 'Hindi' },
  { code: 'zh', name: 'Chinese' },
];

export function PublicHeader() {
  const pathname = usePathname();
  const { t, locale, setLocale, registerDictionary } = useI18n();
  const { push } = useToast();
  const [open, setOpen] = useState(false);
  const [otherOpen, setOtherOpen] = useState(false);
  const [customLocale, setCustomLocale] = useState('');
  const [translating, setTranslating] = useState(false);
  const [languages, setLanguages] = useState<SupportedLanguage[]>(FALLBACK_LANGUAGES);
  useEffect(() => setOpen(false), [pathname]);

  useEffect(() => {
    let alive = true;
    getSupportedLanguages()
      .then((res) => {
        if (alive && res.languages.length > 0) setLanguages(res.languages);
      })
      .catch(() => {
        /* keep fallback list */
      });
    return () => {
      alive = false;
    };
  }, []);

  const translateTo = useCallback(
    async (target: string) => {
      if (STATIC_LOCALES.includes(target)) {
        setLocale(target);
        return;
      }
      setTranslating(true);
      try {
        const values = await translateMessagesCached(target, en as Record<string, string>);
        registerDictionary(target, values);
        setLocale(target);
      } catch (err) {
        setLocale(target);
        push(err instanceof Error ? err.message : 'Translation temporarily unavailable.', 'warn');
      } finally {
        setTranslating(false);
      }
    },
    [push, registerDictionary, setLocale],
  );

  useEffect(() => {
    if (!STATIC_LOCALES.includes(locale)) {
      void translateTo(locale);
    }
  }, [locale, translateTo]);

  function onLocaleChange(value: string) {
    if (value === '__other') {
      setCustomLocale('');
      setOtherOpen(true);
      return;
    }
    setOtherOpen(false);
    void translateTo(value);
  }

  function submitOther(e: FormEvent) {
    e.preventDefault();
    const name = customLocale.trim();
    if (!name) return;
    const code = name.toLowerCase().replace(/[^a-z\s-]/g, '').replace(/\s+/g, '-').slice(0, 24);
    void translateTo(code);
  }

  const options = languages.some((l) => l.code === locale) ? languages : [...languages, { code: locale, name: locale }];

  return (
    <>
      <div className="bar-banner">
        <strong>⚠</strong>
        <Link href="/emergency" className="bar-banner-link">{t('emergency')}</Link>
        <span className="right">
          <label className="sr-only" htmlFor="locale">{t('ph_language')}</label>
          <select
            id="locale"
            className="select"
            style={{ width: 'auto', padding: '4px 8px', fontSize: '0.82rem' }}
            value={locale}
            disabled={translating}
            onChange={(e) => onLocaleChange(e.target.value)}
          >
            {options.map((lang) => (
              <option key={lang.code} value={lang.code}>{lang.name}</option>
            ))}
            <option value="__other">{t('ph_other_language')}</option>
          </select>
          {translating && <span className="muted" style={{ fontSize: '0.75rem', marginLeft: 6 }}>{t('ph_translating')}</span>}
        </span>
      </div>
      <form onSubmit={submitOther} style={{ display: otherOpen ? 'flex' : 'none', gap: 6, padding: '6px 16px', alignItems: 'center' }}>
        <label className="muted" style={{ fontSize: '0.8rem' }} htmlFor="custom-locale">{t('ph_translate_to')}</label>
        <input
          id="custom-locale"
          className="input"
          value={customLocale}
          onChange={(e) => setCustomLocale(e.target.value)}
          placeholder={t('ph_custom_placeholder')}
          style={{ maxWidth: 240 }}
        />
        <button type="submit" className="btn btn-primary btn-sm" disabled={translating || !customLocale.trim()}>
          {t('ph_translate_btn')}
        </button>
      </form>
      <header className="site-header">
        <div className="site-header-inner">
          <Link href="/" aria-label={t('ph_home')}><Logo title={t('layout_fab')} label={t('layout_brand')} /></Link>
          <button
            type="button"
            className="nav-toggle"
            aria-expanded={open}
            aria-controls="primary-nav"
            aria-label={open ? t('ph_close_menu') : t('ph_open_menu')}
            onClick={() => setOpen((v) => !v)}
          >
            <span aria-hidden>{open ? '×' : '☰'}</span>
          </button>
          <nav id="primary-nav" className={`nav-links${open ? ' nav-open' : ''}`} aria-label={t('ph_primary')}>
            {LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`nav-link${pathname === link.href ? ' nav-link-active' : ''}`}
              >
                {t(link.key)}
              </Link>
            ))}
            <Link href="/report" className="btn btn-primary btn-sm">
              {t('ph_helpme')}
            </Link>
            <ThemeToggle />
          </nav>
        </div>
      </header>
    </>
  );
}
