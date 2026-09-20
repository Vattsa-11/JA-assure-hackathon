import logging

from sqlalchemy.orm import Session

from app.models.brand import Brand
from app.models.lead import Lead, LeadStatus
from app.services.hunter_client import hunter_client
from app.services.llm_client import llm_client
from app.services.osm_client import osm_client
from app.services.scraping_client import scraping_client

logger = logging.getLogger(__name__)

def find_leads(db: Session, brand_id: int, niche: str, region: str) -> list[Lead]:
    """
    Finds leads via OSM, enriches them via scraping, finds emails via Hunter,
    scores them, and drafts outreach.
    """
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise ValueError("Brand not found")

    osm_results = osm_client.find_businesses(niche, region, limit=3)
    created_leads = []

    for b in osm_results:
        scraped_text = ""
        email = b.get("email")

        website = b.get("website")
        if website:
            scraped_text = scraping_client.scrape_url(website) or ""
            if not email:
                domain = website.replace("https://", "").replace("http://", "").split("/")[0]
                email = hunter_client.find_email_for_domain(domain)

        prompt = f"""
Business Name: {b['name']}
Niche: {niche}
Region: {region}
Website Text: {scraped_text[:1500]}
"""
        system_prompt = f"""You are a lead qualifier and SDR for {brand.name}.
{brand.voice_description}

Score the lead from 0 to 100 on how well they fit our insurance products.
Provide a short plain-text reason for the score.
Draft a personalized outreach email referencing their specific business name and scraped details.

IMPORTANT RULES for the drafted email:
1. DO NOT use generic placeholders like [Name], [Your Name], or [Insert Link].
2. Address the email to the general business team if a specific contact person is unknown (e.g., "Hello [Business Name] Team," or simply "Hello,"). DO NOT address the business as if it were a person (e.g., do not say "Dear Michael Trio,").
3. Sign off as "The {brand.name} Team".

Return JSON:
{{{{
    "fit_score": 85,
    "fit_reason": "They are a local jewelry shop that...",
    "draft_outreach": "Hello [Business Name] Team,\\n..."
}}}}
"""
        try:
            result_json = llm_client.generate_json(
                prompt=prompt,
                system_prompt=system_prompt,
                model_name="qwen/qwen3.8-27b",
                temperature=0.3
            )

            lead = Lead(
                business_name=b["name"],
                website=website,
                email=email,
                niche=niche,
                region=region,
                fit_score=result_json.get("fit_score", 0),
                fit_reason=result_json.get("fit_reason", ""),
                draft_outreach=result_json.get("draft_outreach", ""),
                status=LeadStatus.draft
            )
            db.add(lead)
            db.commit()
            created_leads.append(lead)
        except Exception as e:  # noqa: BLE001 -- fail-soft: one bad lead must not abort the whole batch
            logger.warning(f"Failed to process lead {b['name']}: {e}")

    return created_leads
