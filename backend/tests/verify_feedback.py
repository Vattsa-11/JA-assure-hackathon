import os
import sys
from pathlib import Path

backend_dir = r"c:\Users\sharv\Downloads\hackthon\ja-assure-marketing-agent\backend"
sys.path.append(backend_dir)

from app.core.db import SessionLocal
from app.models.brand import Brand
from app.models.content import ContentAsset, ContentVersion, Feedback
from app.agents.content import generate_content

def prove_feedback_loop():
    db = SessionLocal()
    try:
        # Get Jade Brand
        brand = db.query(Brand).filter(Brand.name == "Jade").first()
        if not brand:
            print("Brand 'Jade' not found. Make sure DB is seeded.")
            return

        topic = "A new comprehensive insurance policy for small retail jewelers"
        
        print("\n--- PHASE 1: INITIAL GENERATION ---")
        print(f"Generating content for topic: {topic}")
        initial_assets = generate_content(db, brand.id, topic)
        
        # Pick one asset (e.g. LinkedIn variant A)
        target_asset = [a for a in initial_assets if a.platform == "linkedin"][0]
        initial_version = db.query(ContentVersion).filter(ContentVersion.content_asset_id == target_asset.id).first()
        print("\n[BEFORE FEEDBACK] LinkedIn Output:")
        print("="*60)
        print(initial_version.content_text)
        print("="*60)
        
        print("\n--- PHASE 2: INJECTING REJECTION FEEDBACK ---")
        # Simulate user rejecting it for being too salesy
        feedback = Feedback(
            content_asset_id=target_asset.id,
            reason_tag="too_salesy",
            note="too salesy — drop fear-based framing, lead with the coverage detail instead"
        )
        db.add(feedback)
        db.commit()
        print("Feedback injected: 'too salesy — drop fear-based framing, lead with the coverage detail instead'")
        
        print("\n--- PHASE 3: RE-GENERATION ---")
        print("Generating content again for the exact same topic...")
        new_assets = generate_content(db, brand.id, topic)
        new_target_asset = [a for a in new_assets if a.platform == "linkedin"][0]
        new_version = db.query(ContentVersion).filter(ContentVersion.content_asset_id == new_target_asset.id).first()
        
        print("\n[AFTER FEEDBACK] LinkedIn Output:")
        print("="*60)
        print(new_version.content_text)
        print("="*60)
        
        print("\nProof complete! Check the difference above.")

    finally:
        db.close()

if __name__ == "__main__":
    prove_feedback_loop()
