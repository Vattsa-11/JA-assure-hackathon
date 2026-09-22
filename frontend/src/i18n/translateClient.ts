import { API_URL } from './apiUrl';

/**
 * Client for DYNAMIC content translation (drafts, emails, topics, reasons).
 * Static UI labels use translations.ts dictionaries instead.
 *
 * Design:
 * - Memory cache per language → instant re-renders, zero refetch
 * - In-flight dedup → same text requested twice = one HTTP call
 * - Micro-batching → all texts mounted in the same tick go in ONE request
 * - Fail-soft → on any error we render the original text
 */

type CacheState = {
  /** resolved translations, original -> translated */
  resolved: Map<string, string>;
  /** original -> list of pending subscribers waiting for the translation */
  pending: Map<string, Array<(translated: string) => void>>;
  /** batch timer */
  batchTimer: ReturnType<typeof setTimeout> | null;
};

const caches = new Map<string, CacheState>();

/**
 * Ask the backend (once per session) to pre-translate all DB content into
 * every supported language, so switching language renders instantly.
 * Fire-and-forget: the endpoint runs the warm-up as a background task and
 * no-ops when everything is already cached.
 */
let warmTriggered = false;
export function triggerWarmup(): void {
  if (warmTriggered) return;
  warmTriggered = true;
  fetch(`${API_URL}/translate/warm`, { method: 'POST' }).catch(() => {});
}

function getCache(lang: string): CacheState {
  let state = caches.get(lang);
  if (!state) {
    state = { resolved: new Map(), pending: new Map(), batchTimer: null };
    caches.set(lang, state);
  }
  return state;
}

function flushBatch(lang: string) {
  const state = getCache(lang);
  state.batchTimer = null;

  const batch = [...state.pending.keys()];
  if (batch.length === 0) return;
  const subscribers = new Map(state.pending);
  state.pending.clear();

  (async () => {
    try {
      const res = await fetch(`${API_URL}/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texts: batch, target_language: lang }),
      });
      if (!res.ok) throw new Error(`translate failed: ${res.status}`);
      const data: { translations: Record<string, string> } = await res.json();
      for (const original of batch) {
        const translated = data.translations[original] ?? original;
        state.resolved.set(original, translated);
        (subscribers.get(original) ?? []).forEach(cb => cb(translated));
      }
    } catch {
      // Fail soft: resolve everything to the original text
      for (const original of batch) {
        (subscribers.get(original) ?? []).forEach(cb => cb(original));
      }
    }
  })();
}

/**
 * Subscribe to the translation of `text` into `lang`.
 * Returns an unsubscribe function. `onResult` fires synchronously with a
 * cached value when available, otherwise after the batch resolves.
 * English (source language) resolves immediately to the original text.
 */
export function subscribeTranslation(
  text: string,
  lang: string,
  onResult: (translated: string) => void,
): () => void {
  if (!text || lang === 'en') {
    onResult(text);
    return () => {};
  }

  const state = getCache(lang);
  const cached = state.resolved.get(text);
  if (cached !== undefined) {
    onResult(cached);
    return () => {};
  }

  // English source is returned as-is by the backend too, short-circuit here
  if (!lang) {
    onResult(text);
    return () => {};
  }

  let active = true;
  const wrapped = (translated: string) => {
    if (active) onResult(translated);
  };
  if (!state.pending.has(text)) state.pending.set(text, []);
  state.pending.get(text)!.push(wrapped);

  if (state.batchTimer === null) {
    state.batchTimer = setTimeout(() => flushBatch(lang), 40);
  }

  return () => {
    active = false;
  };
}
