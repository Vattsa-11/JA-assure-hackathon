import hashlib

from sqlalchemy.orm import Session

from app.models.research import CompetitorDigestEntry
from app.services.llm_client import llm_client
from app.services.scraping_client import scraping_client


def run_competitor_digest(db: Session, competitor_urls: list[str]) -> list[CompetitorDigestEntry]:
    results = []
    for url in competitor_urls:
        scraped_text = scraping_client.scrape_url(url)
        if not scraped_text:
            continue

        current_hash = hashlib.sha256(scraped_text.encode('utf-8')).hexdigest()

        previous_entry = db.query(CompetitorDigestEntry).filter(CompetitorDigestEntry.competitor_url == url).order_by(CompetitorDigestEntry.created_at.desc()).first()

        if previous_entry and previous_entry.last_snapshot_hash == current_hash:
            continue

        prompt = f"We are tracking {url}. Here is the current text on their page:\n\n{scraped_text[:3000]}"
        system_prompt = """You are a competitive intelligence analyst.
Based on the provided text from a competitor's website, summarize any key updates or offerings and provide a suggested action for our marketing team.
Keep it under 3 sentences."""

        suggested_action = llm_client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            model_name="qwen/qwen3.8-27b",
            temperature=0.2
        )

        entry = CompetitorDigestEntry(
            competitor_url=url,
            last_snapshot_hash=current_hash,
            suggested_action=suggested_action.strip()
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        results.append(entry)

    return results
