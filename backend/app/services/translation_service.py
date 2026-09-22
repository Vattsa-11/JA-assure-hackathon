import hashlib
import logging
import re
import threading
import time

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.translation import TranslationCache
from app.services.llm_client import llm_client

logger = logging.getLogger(__name__)

TARGET_LANGUAGES = {
    "ms": "Malay (Bahasa Melayu)",
    "id": "Indonesian (Bahasa Indonesia)",
    "th": "Thai",
    "zh": "Simplified Chinese (Mandarin)",
    "en": "English",
}

# Matches the localization agent's rules so tone stays consistent app-wide
_TRANSLATION_SYSTEM_PROMPT = """You are an expert translator for insurance marketing content in Southeast Asia.
Translate the given texts into {language_full}.

CRITICAL RULES:
- DO NOT translate word-for-word. Adapt idioms and cultural context for a native {language_full} speaker.
- Keep the tone professional and suitable for insurance marketing.
- Preserve line breaks, emojis, and formatting exactly.
- For Simplified Chinese: use simplified characters (不要用繁體字).
- Return ONLY a JSON object mapping each index (as a string) to its translation, e.g. {{{{"0": "...", "1": "..."}}}}.
"""

MAX_BATCH_CHARS = 2500  # keep each LLM call under Groq free-tier OTPM (1000 tokens/min)
BATCH_PAUSE_SECONDS = 3  # pace consecutive LLM calls to avoid OTPM bursts
MAX_BATCH_RETRIES = 5  # 429 cooldowns on free tier can be ~50s; be patient


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def _llm_translate_batch(texts: list[str], target_language: str) -> list[str]:
    """Translate a list of texts in one LLM call. Returns translations in the same order.

    Retries patiently on rate limits: Groq free tier enforces a ~1000 output-token
    per minute cap, and its 429s advertise a cooldown ("try again in ~50s").
    """
    import json

    language_full = TARGET_LANGUAGES.get(target_language, target_language)
    payload = {str(i): text for i, text in enumerate(texts)}

    prompt = (
        json.dumps(payload, ensure_ascii=False)
        + "\n\nReturn the JSON object with every index translated into "
        + language_full
        + "."
    )
    result = None
    for attempt in range(MAX_BATCH_RETRIES):
        try:
            result = llm_client.generate_json(
                prompt=prompt,
                system_prompt=_TRANSLATION_SYSTEM_PROMPT.format(language_full=language_full),
                model_name="qwen/qwen3.8-27b",
                temperature=0.2,
            )
            break
        except Exception as e:  # noqa: BLE001 - rate limits & transient provider errors
            if attempt == MAX_BATCH_RETRIES - 1:
                raise
            wait = 15.0
            hint = re.search(r"try again in ([\d.]+)s", str(e))
            if hint:
                wait = min(float(hint.group(1)) + 1.0, 60.0)
            logger.warning(
                f"Translation batch rate-limited/error, waiting {wait:.0f}s "
                f"(attempt {attempt + 1}/{MAX_BATCH_RETRIES}): {str(e)[:120]}"
            )
            time.sleep(wait)

    translations: list[str] = []
    for i, original in enumerate(texts):
        translated = result.get(str(i))
        if not isinstance(translated, str) or not translated.strip():
            # Fail soft per item: keep original rather than dropping the row
            logger.warning(f"Translation missing for index {i}; keeping original text.")
            translated = original
        translations.append(translated)
    return translations


def get_translations(
    db: Session, texts: list[str], target_language: str
) -> dict[str, str]:
    """Translate texts into target_language, using the DB cache first.

    Returns a mapping of original text -> translated text. Texts already in the
    target language are returned unchanged. Cache misses are translated in one
    or more LLM batch calls and persisted for all future requests.
    """
    if target_language == "en":
        # English is the source language of the app; nothing to do.
        return {text: text for text in texts}

    if target_language not in TARGET_LANGUAGES:
        raise ValueError(
            f"Unsupported target language: {target_language}. Supported: {list(TARGET_LANGUAGES)}"
        )

    # Deduplicate (many feed items share topics/brands) and drop empties
    unique_texts: list[str] = []
    seen: set[str] = set()
    for text in texts:
        if text and text.strip() and text not in seen:
            seen.add(text)
            unique_texts.append(text)
    if not unique_texts:
        return {}

    # URLs/emails have nothing to translate — pass through, never cache
    passthrough: list[str] = []
    translatable: list[str] = []
    for text in unique_texts:
        stripped = text.strip()
        if (stripped.startswith(("http://", "https://")) and " " not in stripped) or "@" in stripped:
            passthrough.append(text)
        else:
            translatable.append(text)
    for text in passthrough:
        result[text] = text
    unique_texts = translatable
    if not unique_texts:
        return result

    result: dict[str, str] = {}
    misses: list[str] = []

    hashes = {text: _hash_text(text) for text in unique_texts}
    rows = (
        db.query(TranslationCache)
        .filter(
            TranslationCache.source_hash.in_(list(hashes.values())),
            TranslationCache.target_language == target_language,
        )
        .all()
    )
    hash_to_original = {h: text for text, h in hashes.items()}
    for row in rows:
        original = hash_to_original.get(row.source_hash)
        if original is None:
            continue
        result[original] = row.translated_text
        row.hit_count += 1
    db.commit()

    for text in unique_texts:
        if text not in result:
            misses.append(text)

    # Split misses into batches that stay under MAX_BATCH_CHARS
    batches: list[list[str]] = []
    current: list[str] = []
    current_len = 0
    for text in misses:
        if current and current_len + len(text) > MAX_BATCH_CHARS:
            batches.append(current)
            current = []
            current_len = 0
        current.append(text)
        current_len += len(text)
    if current:
        batches.append(current)

    for batch_idx, batch in enumerate(batches):
        if batch_idx > 0:
            time.sleep(BATCH_PAUSE_SECONDS)  # pace consecutive LLM calls
        try:
            translations = _llm_translate_batch(batch, target_language)
        except Exception as e:  # noqa: BLE001 - fail-soft over external service I/O
            logger.error(f"LLM translation failed for batch of {len(batch)}: {e}")
            for text in batch:
                result[text] = text  # graceful fallback: original text
            continue
        for text, translated in zip(batch, translations):
            result[text] = translated
            db.add(
                TranslationCache(
                    source_hash=_hash_text(text),
                    target_language=target_language,
                    source_text=text,
                    translated_text=translated,
                    hit_count=0,
                )
            )
        if batches:
            try:
                db.commit()  # per-batch commit: progress survives interruptions
            except IntegrityError:
                # A concurrent request (e.g. the warm-up job) inserted the same
                # (hash, language) row first. Keep their translation, avoid a 500.
                db.rollback()
                logger.info("Translation insert raced a concurrent writer; reconciling from cache.")
                rows = (
                    db.query(TranslationCache)
                    .filter(
                        TranslationCache.source_hash.in_([_hash_text(t) for t in batch]),
                        TranslationCache.target_language == target_language,
                    )
                    .all()
                )
                for row in rows:
                    result[row.source_text] = row.translated_text

    return result


def collect_translatable_texts(db: Session) -> list[str]:
    """Gather every dynamic string in the DB worth translating.

    Used by the warm-up job so that switching to any language renders
    instantly from cache instead of translating live on first view.
    """
    from app.models.content import ContentAsset, ContentVersion
    from app.models.lead import Lead
    from app.models.research import CompetitorDigestEntry

    texts: list[str] = []
    texts.extend(row[0] for row in db.query(ContentVersion.content_text).all())
    texts.extend(row[0] for row in db.query(ContentAsset.topic).all() if row[0])
    texts.extend(row[0] for row in db.query(Lead.fit_reason).all() if row[0])
    texts.extend(row[0] for row in db.query(Lead.draft_outreach).all() if row[0])
    texts.extend(row[0] for row in db.query(Lead.region).all() if row[0])
    texts.extend(row[0] for row in db.query(Lead.niche).all() if row[0])
    texts.extend(row[0] for row in db.query(CompetitorDigestEntry.suggested_action).all() if row[0])

    # Drop empties and pathological outliers (LLM batches are sized for short text)
    cleaned: list[str] = []
    seen: set[str] = set()
    for text in texts:
        if not text:
            continue
        stripped = text.strip()
        if not stripped or len(stripped) > 4000 or stripped in seen:
            continue
        seen.add(stripped)
        cleaned.append(text)
    return cleaned


_warm_lock = threading.Lock()


def warm_language_caches(languages: list[str] | None = None) -> dict:
    """Pre-translate ALL dynamic DB content into the given languages.

    Runs as a background job (startup thread or /translate/warm endpoint).
    Safe to call twice: a second call while one is running is a no-op, and
    completed languages cost only a cache lookup.
    """
    if _warm_lock.locked():
        logger.info("Translation warm-up already running; skipping.")
        return {"status": "already_running"}
    with _warm_lock:
        from app.core.db import SessionLocal

        langs = languages or [lang for lang in TARGET_LANGUAGES if lang != "en"]
        summary: dict = {"status": "completed", "languages": {}}
        for lang in langs:
            db = SessionLocal()
            try:
                texts = collect_translatable_texts(db)
                get_translations(db, texts, lang)
                summary["languages"][lang] = len(texts)
                logger.info(f"Translation cache warm for '{lang}': {len(texts)} strings ensured.")
            except Exception as e:  # noqa: BLE001 - warm-up must never crash the app
                logger.error(f"Translation warm-up failed for '{lang}': {e}")
                summary["languages"][lang] = f"error: {str(e)[:100]}"
            finally:
                db.close()
        return summary
