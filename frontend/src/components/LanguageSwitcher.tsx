'use client';

import { useEffect, useRef, useState } from 'react';
import { LANGUAGES, LANGUAGE_META, type Language } from '../i18n/translations';
import { useLanguage } from '../i18n/LanguageContext';

export default function LanguageSwitcher() {
  const { language, setLanguage, t } = useLanguage();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  // Close the dropdown when clicking anywhere outside it
  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, [open]);

  const current = LANGUAGE_META[language];

  return (
    <div className="lang-switcher" ref={rootRef}>
      <button
        type="button"
        className="lang-switcher-btn"
        onClick={() => setOpen(v => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={t('nav.language')}
        title={t('nav.language')}
      >
        <span className="lang-globe" aria-hidden="true">🌐</span>
        <span className="lang-current-label">{current.label}</span>
        <span className={`lang-chevron${open ? ' lang-chevron-open' : ''}`} aria-hidden="true">▾</span>
      </button>

      {open && (
        <ul className="lang-menu" role="listbox" aria-label={t('nav.language')}>
          {LANGUAGES.map((lang: Language) => {
            const meta = LANGUAGE_META[lang];
            const active = lang === language;
            return (
              <li key={lang} role="option" aria-selected={active}>
                <button
                  type="button"
                  className={`lang-option${active ? ' lang-option-active' : ''}`}
                  onClick={() => {
                    setLanguage(lang);
                    setOpen(false);
                  }}
                >
                  <span className="lang-flag" aria-hidden="true">{meta.flag}</span>
                  <span className="lang-option-label">{meta.label}</span>
                  {active && <span className="lang-check" aria-hidden="true">✓</span>}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
