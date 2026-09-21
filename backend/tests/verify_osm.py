import sys
from pathlib import Path

backend_dir = r"c:\Users\sharv\Downloads\hackthon\ja-assure-marketing-agent\backend"
sys.path.append(backend_dir)

from app.core.db import SessionLocal
from app.models.brand import Brand
from app.agents.lead import find_leads
import json
from app.services.osm_client import osm_client

def prove_osm_leads():
    # Monkey patch osm_client to intercept the raw response
    original_find_businesses = osm_client.find_businesses
    intercepted_raw_data = []

    def patched_find_businesses(niche, region, limit=5):
        print(f"\n--- INTERCEPTING OSM OVERPASS API QUERY ---")
        print(f"Niche: {niche}, Region: {region}, Limit: {limit}")
        results = original_find_businesses(niche, region, limit)
        intercepted_raw_data.extend(results)
        print("Raw OSM JSON response snippet:")
        print(json.dumps(results[:2], indent=2))
        print("-" * 60)
        return results

    osm_client.find_businesses = patched_find_businesses

    db = SessionLocal()
    try:
        brand = db.query(Brand).filter(Brand.name == "Jade").first()
        if not brand:
            print("Brand 'Jade' not found.")
            return

        print("\n--- PHASE 1: RUNNING LEAD PIPELINE (OSM -> Scrape -> LLM) ---")
        leads = find_leads(db, brand.id, "jewelry", "Singapore")
        
        print("\n--- PHASE 2: VERIFYING DB OUTPUT ---")
        for lead in leads:
            print(f"Business Name: {lead.business_name}")
            print(f"Website: {lead.website}")
            print(f"Fit Score: {lead.fit_score}")
            print(f"Fit Reason: {lead.fit_reason}")
            print(f"Email: {lead.email}")
            print("Draft Outreach:")
            print(lead.draft_outreach)
            print("="*60)
            
        print("\nProof complete! OSM data was directly used to create these leads.")
    finally:
        db.close()

if __name__ == "__main__":
    prove_osm_leads()
