'use client';

import { useEffect, useState } from 'react';
import { useLanguage } from './LanguageContext';
import { subscribeTranslation, triggerWarmup } from './translateClient';

/**
 * useTranslated: resolve a dynamic (DB/LLM-generated) string into the
 * current UI language. Returns the original text until the translation
 * arrives (usually one batched request).
 */
export function useTranslated(text: string | null | undefined): string {
  const { language } = useLanguage();
  const [resolved, setResolved] = useState(text ?? '');

  useEffect(() => {
    if (!text) {
      setResolved('');
      return;
    }
    if (language !== 'en') triggerWarmup(); // keep other languages pre-cached
    // Show the original immediately; swap when translation lands
    setResolved(text);
    return subscribeTranslation(text, language, setResolved);
  }, [text, language]);

  return resolved;
}

/**
 * <T text={dynamicString} /> — renders dynamic content translated into the
 * language selected in the navbar switcher.
 */
export default function T({ text }: { text: string | null | undefined }) {
  const translated = useTranslated(text);
  return <>{translated}</>;
}
