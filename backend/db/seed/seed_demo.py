import sys
import time
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[2]
sys.path.append(str(backend_dir))

from app.core.db import SessionLocal
from app.models.brand import Brand
from app.models.content import ContentAsset, ContentVersion, Feedback, ContentStatus
from app.api.pipeline import _run_content, _run_leads
from app.agents.content import generate_content

def seed_demo():
    """
    Seeds demo data by running the actual pipelines so the dashboard 
    is populated with realistic data and a real feedback history.
    """
    db = SessionLocal()
    try:
        jade = db.query(Brand).filter(Brand.name == "Jade").first()
        doc = db.query(Brand).filter(Brand.name == "DoctorShield").first()
        
        if not jade or not doc:
            print("Brands missing. Run seed_brands.py first.")
            return

        print("--- Seeding Content & Generating Real Feedback History ---")
        topic = "New cyber protection policy for jewelry stores"
        # Generate initial assets
        assets = generate_content(db, jade.id, topic)
        
        li_asset = [a for a in assets if a.platform == "linkedin"][0]
        
        # We must commit the assets before hitting the API, so the API can find the asset.
        db.commit()
        
        print(f"Calling real API endpoint to reject asset {li_asset.id}...")
        # Programmatically reject the LinkedIn variant using the actual FastAPI app logic
        # by calling the endpoint function directly (or via TestClient) to ensure
        # the exact same logic runs as if a human clicked it.
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        response = client.post(
            f"/review/{li_asset.id}/reject",
            json={
                "reason_tag": "too_salesy",
                "note": "Too aggressive. Do not use urgency language or emojis. Keep it extremely professional."
            }
        )
        print(f"API Reject Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error rejecting: {response.text}")

        # Mark others as approved for metrics via the real API
        for a in assets:
            if a.id != li_asset.id:
                resp = client.post(f"/review/{a.id}/approve")
                print(f"API Approve Status for {a.id}: {resp.status_code}")

        print("--- Running Content Pipeline (Background) ---")
        # Run a real content pipeline run so the queue has pending items
        _run_content(doc.id, "Medical malpractice insurance simplified for new clinics")
        
        print("--- Running Lead Pipeline (Background) ---")
        # Run a real lead pipeline run so the leads dashboard has pending leads
        _run_leads(jade.id, "jewelry", "Singapore")
        
        print("Demo seed complete! The dashboard is now ready for a live presentation.")

    except Exception as e:
        print(f"Seed failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo()
