'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import {
  LANGUAGES,
  LANGUAGE_META,
  TRANSLATIONS,
  type Language,
  type TranslationKey,
} from './translations';

const STORAGE_KEY = 'ja-assure-lang';
const GEO_FLAG_KEY = 'ja-assure-lang-geo'; // '1' once geo-detection has been attempted

const COUNTRY_TO_LANGUAGE: Record<string, Language> = {
  id: 'id', // Indonesia
  th: 'th', // Thailand
  cn: 'zh', // China
  tw: 'zh', // Taiwan
  hk: 'zh', // Hong Kong
  mo: 'zh', // Macau
  sg: 'en', // Singapore (English is the working language)
  my: 'ms', // Malaysia uses Malay (Bahasa Malaysia)
  bn: 'ms', // Brunei
};

function detectInitialLanguage(): Language {
  if (typeof window === 'undefined') return 'en';
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY) as Language | null;
    if (stored && (LANGUAGES as readonly string[]).includes(stored)) return stored;
  } catch {
    // localStorage unavailable (private mode etc.) — fall through to detection
  }
  const candidates = navigator.languages ?? [navigator.language];
  for (const candidate of candidates) {
    const code = candidate.toLowerCase();
    if (code.startsWith('zh')) return 'zh';
    if (code.startsWith('ms')) return 'ms';
    if (code.startsWith('th')) return 'th';
    if (code.startsWith('id')) return 'id';
  }
  return 'en';
}

type LanguageContextValue = {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: TranslationKey, vars?: Record<string, string | number>) => string;
};

const LanguageContext = createContext<LanguageContextValue | null>(null);

/** Reverse-geocode coords to a country code via a key-free client API.
 *  Returns null on any failure — language just falls back to browser detection. */
async function countryCodeFromCoords(lat: number, lon: number): Promise<string | null> {
  try {
    const res = await fetch(
      `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=en`,
      { signal: AbortSignal.timeout(6000) },
    );
    if (!res.ok) return null;
    const data = await res.json();
    const code = typeof data.countryCode === 'string' ? data.countryCode.toLowerCase() : null;
    return code && code.length === 2 ? code : null;
  } catch {
    return null;
  }
}

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>('en');

  // Load persisted / detected language after mount (client only)
  useEffect(() => {
    setLanguageState(detectInitialLanguage());

    // Location-based detection: only when the user has never picked a language
    // manually AND we haven't already asked for location once (avoids re-prompting
    // after a denial). The browser shows the native permission prompt — that IS
    // the user consent step.
    let geoAlreadyTried = false;
    try {
      geoAlreadyTried = window.localStorage.getItem(GEO_FLAG_KEY) === '1';
    } catch {
      geoAlreadyTried = false;
    }
    const hasStoredChoice = (() => {
      try {
        return !!window.localStorage.getItem(STORAGE_KEY);
      } catch {
        return false;
      }
    })();

    if (geoAlreadyTried || hasStoredChoice || !('geolocation' in navigator)) return;

    try {
      window.localStorage.setItem(GEO_FLAG_KEY, '1');
    } catch {
      // non-fatal: worst case we ask again next load
    }

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const country = await countryCodeFromCoords(pos.coords.latitude, pos.coords.longitude);
        if (!country) return;
        const geoLang = COUNTRY_TO_LANGUAGE[country];
        if (!geoLang) return; // unsupported region — keep current language
        // Don't override if the user picked something while geolocation was in flight
        try {
          if (window.localStorage.getItem(STORAGE_KEY)) return;
        } catch {
          // treat as no explicit choice
        }
        setLanguageState(geoLang);
      },
      () => {
        // Permission denied or unavailable — keep browser-language behaviour.
      },
      { timeout: 8000, maximumAge: 6 * 60 * 60 * 1000 },
    );
  }, []);

  // Keep <html lang> in sync for accessibility + font rendering (Thai/Chinese)
  useEffect(() => {
    document.documentElement.lang = LANGUAGE_META[language].htmlLang;
  }, [language]);

  const setLanguage = useCallback((lang: Language) => {
    setLanguageState(lang);
    try {
      window.localStorage.setItem(STORAGE_KEY, lang);
    } catch {
      // non-fatal: language still applies for this session
    }
  }, []);

  const t = useCallback(
    (key: TranslationKey, vars?: Record<string, string | number>): string => {
      const dict = TRANSLATIONS[language] ?? TRANSLATIONS.en;
      let text = dict[key] ?? TRANSLATIONS.en[key] ?? key;
      if (vars) {
        for (const [name, value] of Object.entries(vars)) {
          text = text.replace(new RegExp(`\\{${name}\\}`, 'g'), String(value));
        }
      }
      return text;
    },
    [language],
  );

  const value = useMemo(
    () => ({ language, setLanguage, t }),
    [language, setLanguage, t],
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useLanguage must be used within <LanguageProvider>');
  return ctx;
}
