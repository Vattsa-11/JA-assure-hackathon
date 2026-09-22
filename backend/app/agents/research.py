import hashlib
import logging
import threading
import time
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.research import CompetitorDigestEntry, TrackedCompetitor
from app.services.llm_client import llm_client
from app.services.scraping_client import scraping_client

logger = logging.getLogger(__name__)

#JA Assure's business description, injected into every research prompt.
JA_ASSURE_BRIEF = """JA Assure sells commercial insurance in Singapore/Southeast Asia to three niches:
- Jewellery retailers (theft, smash-and-grab, stock through-transit risk)
- Healthcare practitioners (professional indemnity, clinic cover)
- Cash-in-transit / high-value logistics firms (cash secrecy, goods-in-transit)
"""

MAJOR_COMPETITORS: list[dict] = [
    {"name": "Income Insurance", "url": "https://www.income.com.sg",
     "why": "Largest local composite insurer; SME and commercial lines directly overlap JA Assure's niches."},
    {"name": "Chubb Insurance Singapore", "url": "https://www.chubb.com/sg-en",
     "why": "Global insurer strong in property/casualty and high-value goods — direct competitor for jewellery and transit cover."},
    {"name": "AIG Singapore", "url": "https://www.aig.sg",
     "why": "Major commercial insurer offering SME packages and specialty liability products."},
    {"name": "Zurich Singapore", "url": "https://www.zurich.com.sg",
     "why": "Strong SME and corporate insurance presence including retail and logistics sectors."},
    {"name": "AXA Singapore", "url": "https://www.axa.sg",
     "why": "Composite insurer with SME commercial lines and healthcare-related cover."},
    {"name": "Allianz Singapore", "url": "https://www.allianz.sg",
     "why": "Global composite insurer active in SME, liability and engineering lines."},
]

_AUTO_SCAN_LOCK = threading.Lock()
_AUTO_SCAN_STOP = threading.Event()
_AUTO_SCAN_INTERVAL_SECONDS = 6 * 60 * 60  # every 6 hours
_AUTO_SCAN_MAX_FAILURES = 5  # after this many consecutive failures, a URL is parked

SCAN_MODELS = ["qwen/qwen3.8-27b", "openai/gpt-oss-20b"]


def _llm_text(prompt: str, system_prompt: str, temperature: float = 0.2) -> str | None:
    """LLM call with model fallback; returns None when all models fail."""
    for model in SCAN_MODELS:
        try:
            return llm_client.generate_text(
                prompt=prompt, system_prompt=system_prompt,
                model_name=model, temperature=temperature,
            )
        except Exception as e:  # noqa: BLE001 - try next model
            logger.warning(f"LLM call failed on {model}: {e}")
    return None


def _looks_parked(scraped_text: str, url: str) -> bool:
    """Heuristic for parked/for-sale/default-registrar pages that yield no signal."""
    lowered = scraped_text[:1500].lower()
    markers = [
        "this domain is for sale", "buy this domain", "domain is parked",
        "sedoparking", "afternic", "dan.com", "hugedomains",
        "future home of a quite stereotyped", "default web site page",
        "welcome to nginx", "index of /",
    ]
    if any(m in lowered for m in markers):
        return True
    # Very little real content relative to the URL echo = likely parked
    if len(scraped_text.strip()) < 220 and url.lower() in lowered:
        return True
    return False


def seed_major_competitors(db: Session) -> int:
    """Insert the known major competitors into the watchlist (idempotent)."""
    added = 0
    for c in MAJOR_COMPETITORS:
        exists = db.query(TrackedCompetitor).filter(
            TrackedCompetitor.competitor_url == c["url"]
        ).first()
        if exists:
            if not exists.name:
                exists.name = c["name"]
                db.commit()
            continue
        db.add(TrackedCompetitor(
            competitor_url=c["url"], name=c["name"], source="major", status="active",
        ))
        added += 1
    if added:
        db.commit()
    logger.info(f"Seeded {added} major competitors (total watchlist: {db.query(TrackedCompetitor).count()}).")
    return added


def discover_competitors() -> list[dict]:
    """Ask the LLM to suggest real competitor websites for JA Assure.

    Returns [{name, url, why}] — nothing is stored; the user picks which to track.
    """
    system_prompt = f"""You are a market research assistant for JA Assure's competitors.
{JA_ASSURE_BRIEF}
Suggest 6 real, currently-operating insurance company websites that compete with JA Assure in Singapore and Southeast Asia.
Rules:
- Return ONLY a JSON object: {{{{"competitors": [{{{{"name": "...", "url": "https://...", "why": "one short sentence on who they target"}}}}]}}}}
- URLs must be the company's real homepage domain (e.g. https://www.example.com.sg). No placeholders, no parked domains.
- Prefer insurers whose products overlap JA Assure's niches.
"""
    raw = _llm_text(
        prompt="List the competitor insurance companies now.",
        system_prompt=system_prompt,
        temperature=0.3,
    )
    if not raw:
        return []

    import json as _json
    if raw.startswith("```json"):
        raw = raw[7:-3]
    elif raw.startswith("```"):
        raw = raw[3:-3]
    try:
        parsed = _json.loads(raw.strip())
    except _json.JSONDecodeError:
        logger.warning("discover_competitors: LLM returned non-JSON output")
        return []

    competitors = []
    seen: set[str] = set()
    for item in parsed.get("competitors", []):
        url = str(item.get("url", "")).strip()
        if not url.startswith("http"):
            url = f"https://{url}"
        if url in seen:
            continue
        seen.add(url)
        competitors.append({
            "name": str(item.get("name", ""))[:80],
            "url": url,
            "why": str(item.get("why", ""))[:200],
        })
    return competitors[:6]


def research_new_competitors(db: Session, known_urls: list[str] | None = None) -> dict:
    """Search for NEW competitors we don't track yet, scrape each candidate,
    and produce a full intelligence digest for the promising ones.

    Returns {found, researched: [{name, url, summary, suggested_action, is_new}],
             errors: [{url, note}]}.
    """
    known = set(known_urls or [])
    if not known:
        known = {t.competitor_url for t in db.query(TrackedCompetitor).all()}
        known |= {e.competitor_url for e in db.query(CompetitorDigestEntry).distinct()}

    system_prompt = f"""You are a competitive research analyst for JA Assure, a Singapore commercial insurer.
{JA_ASSURE_BRIEF}
Task: identify insurance companies (or insurtech startups) that COMPETE with JA Assure but are NOT in this already-known list:
{chr(10).join(sorted(known)) if known else "(none known yet)"}

Rules:
- Return ONLY JSON: {{{{"competitors": [{{{{"name": "...", "url": "https://...", "why": "one sentence"}}}}]}}}}
- Focus on newer/niche players: insurtechs, MGAs, brokers specialised in jewellery/clinic/logistics cover, regional insurers expanding into Singapore.
- URLs must be real homepage domains. No placeholders, no parked domains, no duplicates of the known list.
- Up to 4 competitors.
"""
    raw = _llm_text(
        prompt="Find new competitors we are not tracking yet.",
        system_prompt=system_prompt,
        temperature=0.4,
    )
    if not raw:
        return {"found": [], "researched": [], "errors": [{"url": "-", "note": "LLM unavailable"}]}

    import json as _json
    if raw.startswith("```json"):
        raw = raw[7:-3]
    elif raw.startswith("```"):
        raw = raw[3:-3]
    try:
        parsed = _json.loads(raw.strip())
    except _json.JSONDecodeError:
        return {"found": [], "researched": [], "errors": [{"url": "-", "note": "LLM returned invalid JSON"}]}

    candidates = []
    seen: set[str] = set()
    for item in parsed.get("competitors", []):
        url = str(item.get("url", "")).strip()
        if not url.startswith("http"):
            url = f"https://{url}"
        if url in seen or url in known:
            continue
        seen.add(url)
        candidates.append({
            "name": str(item.get("name", ""))[:80],
            "url": url,
            "why": str(item.get("why", ""))[:200],
        })

    researched, errors = [], []
    for c in candidates[:4]:
        scraped = scraping_client.scrape_url(c["url"])
        if not scraped:
            errors.append({"url": c["url"], "note": "Could not scrape candidate site."})
            continue
        if _looks_parked(scraped, c["url"]):
            errors.append({"url": c["url"], "note": "Site looks parked/inactive — skipped."})
            continue

        action = _llm_text(
            prompt=f"We are evaluating {c['url']} as a competitor. Page text:\n\n{scraped[:3000]}",
            system_prompt=f"""You are a competitive intelligence analyst for JA Assure.
{JA_ASSURE_BRIEF}
Summarise what this competitor offers and give a concrete suggested marketing action for JA Assure.
Format: 2-4 sentences. First summarise them, then one sentence starting with 'Suggested action:'.
""",
            temperature=0.2,
        )
        if not action:
            errors.append({"url": c["url"], "note": "Analysis LLM call failed."})
            continue

        researched.append({
            "name": c["name"],
            "url": c["url"],
            "why": c["why"],
            "summary": action.strip(),
            "is_new": True,
        })

    return {"found": candidates, "researched": researched, "errors": errors}


def scan_tracked_competitors(db: Session, urls: list[str] | None = None) -> dict:
    """Scrape tracked competitor pages, hash-diff, digest only what changed.

    urls=None scans the whole watchlist (used by the auto-scheduler).
    Returns {results: [{url, status, note}], scanned_at}.
    status: digested | unchanged | unreachable
    """
    if urls is None:
        watchlist = db.query(TrackedCompetitor).all()
        urls = [t.competitor_url for t in watchlist if t.status != "unreachable"]
    else:
        urls = [u.strip() for u in urls if u.strip()]

    results = []
    for url in urls:
        scraped_text = scraping_client.scrape_url(url)
        tracked = db.query(TrackedCompetitor).filter(
            TrackedCompetitor.competitor_url == url
        ).first()

        if not scraped_text:
            if tracked:
                tracked.consecutive_failures = (tracked.consecutive_failures or 0) + 1
                if tracked.consecutive_failures >= _AUTO_SCAN_MAX_FAILURES:
                    tracked.status = "unreachable"
                db.commit()
            results.append({"url": url, "status": "unreachable",
                            "note": "Could not scrape the page (timeout, blocked, or site down)."})
            continue

        if tracked:
            tracked.consecutive_failures = 0
            tracked.status = "active"
            db.commit()

        if _looks_parked(scraped_text, url):
            results.append({"url": url, "status": "unchanged",
                            "note": "Page looks parked/inactive — nothing to analyze."})
            continue

        current_hash = hashlib.sha256(scraped_text.encode("utf-8")).hexdigest()
        previous_entry = (
            db.query(CompetitorDigestEntry)
            .filter(CompetitorDigestEntry.competitor_url == url)
            .order_by(CompetitorDigestEntry.created_at.desc())
            .first()
        )
        if previous_entry and previous_entry.last_snapshot_hash == current_hash:
            results.append({"url": url, "status": "unchanged",
                            "note": "Page unchanged since last scan — existing analysis still valid."})
            continue

        prompt = f"We are tracking {url}. Here is the current text on their page:\n\n{scraped_text[:3000]}"
        system_prompt = f"""You are a competitive intelligence analyst for JA Assure.
{JA_ASSURE_BRIEF}
Based on the provided text from a competitor's website, summarize any key updates or offerings and provide a suggested action for JA Assure's marketing team.
Format: 2-3 sentences. End with a sentence starting with 'Suggested action:'.
"""
        suggested_action = _llm_text(prompt=prompt, system_prompt=system_prompt, temperature=0.2)
        if not suggested_action:
            results.append({"url": url, "status": "unreachable",
                            "note": "Analysis failed (LLM unavailable) — will retry next scan."})
            continue

        entry = CompetitorDigestEntry(
            competitor_url=url,
            last_snapshot_hash=current_hash,
            suggested_action=suggested_action.strip(),
        )
        db.add(entry)
        db.commit()
        results.append({"url": url, "status": "digested",
                        "note": "New page content analyzed."})

    return {"scanned_at": datetime.utcnow().isoformat(), "results": results}


# ---------------------------------------------------------------------------
# Automated scanning loop
# ---------------------------------------------------------------------------

def _auto_scan_tick() -> None:
    """One full watchlist scan in its own DB session (scheduler thread)."""
    from app.core.db import SessionLocal

    if not _AUTO_SCAN_LOCK.acquire(blocking=False):
        return  # a manual scan is running; skip this tick
    try:
        db = SessionLocal()
        try:
            watchlist = db.query(TrackedCompetitor).count()
            if watchlist == 0:
                seed_major_competitors(db)
            logger.info("Auto-scan: starting scheduled watchlist scan...")
            summary = scan_tracked_competitors(db, urls=None)
            digested = sum(1 for r in summary["results"] if r["status"] == "digested")
            logger.info(f"Auto-scan finished: {len(summary['results'])} URLs, {digested} digested, "
                        f"{sum(1 for r in summary['results'] if r['status'] == 'unchanged')} unchanged, "
                        f"{sum(1 for r in summary['results'] if r['status'] == 'unreachable')} unreachable.")
        finally:
            db.close()
    except Exception as e:  # noqa: BLE001 - scheduler must never crash
        logger.error(f"Auto-scan tick failed: {e}")
    finally:
        _AUTO_SCAN_LOCK.release()


def _auto_scan_loop() -> None:
    while not _AUTO_SCAN_STOP.wait(_AUTO_SCAN_INTERVAL_SECONDS):
        _auto_scan_tick()


def start_auto_scanner() -> None:
    """Start the background scheduler thread (idempotent, called on app startup)."""
    if any(t.name == "competitor-auto-scan" for t in threading.enumerate()):
        return
    _AUTO_SCAN_STOP.clear()
    start_auto_scanner._started_at = datetime.utcnow()  # type: ignore[attr-defined]
    threading.Thread(target=_auto_scan_loop, name="competitor-auto-scan", daemon=True).start()
    logger.info(f"Competitor auto-scanner started (interval: {_AUTO_SCAN_INTERVAL_SECONDS // 3600}h).")


def stop_auto_scanner() -> None:
    _AUTO_SCAN_STOP.set()


def next_auto_scan_time() -> str | None:
    """Best-effort estimate of when the next auto-scan fires (for the UI)."""
    # The loop waits on an Event with a timeout; we can't know the phase exactly
    # without extra state, so report the interval-based schedule from process start.
    started_at = getattr(start_auto_scanner, "_started_at", None)
    if started_at is None:
        return None
    nxt = started_at + timedelta(seconds=_AUTO_SCAN_INTERVAL_SECONDS)
    return max(nxt, datetime.utcnow()).isoformat()
