'use client';

import { useI18n } from '@safelytold/ui/context';

interface Section {
  id: string;
  label: string;
}

interface HomeNavProps {
  sections: Section[];
  active: string;
  onSelect: (id: string) => void;
}

export function HomeNav({ sections, active, onSelect }: HomeNavProps) {
  const { t } = useI18n();
  return (
    <nav className="home-tab-bar" aria-label={t('home_nav_aria')}>
      {sections.map((section) => (
        <button
          key={section.id}
          type="button"
          className={`trust-nav-link${active === section.id ? ' trust-nav-link-active' : ''}`}
          onClick={() => onSelect(section.id)}
        >
          {t(section.label)}
        </button>
      ))}
    </nav>
  );
}
