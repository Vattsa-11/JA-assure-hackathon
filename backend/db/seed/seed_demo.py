import sys
import os
import logging
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.db import SessionLocal
from app.models.brand import Brand
from app.models.content import ContentAsset, ContentStatus, Feedback, ContentVersion
from app.graphs.content_pipeline import content_graph
from app.graphs.lead_pipeline import lead_graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_seed():
    db = SessionLocal()
    
    brand = db.query(Brand).filter(Brand.name == 'Jade').first()
    if not brand:
        logger.error("Brand 'Jade' not found. Please run seed_brands.py first.")
        db.close()
        return

    logger.info("Running Content Pipeline to generate demo data...")
    try:
        result = content_graph.invoke({
            "brand_id": brand.id,
            "topic": "Why jewelry insurance is critical for engagement rings.",
            "generated_asset_ids": []
        })
        
        asset_ids = result.get("generated_asset_ids", [])
        if asset_ids:
            # Simulate a human rejection for the metrics dashboard
            rejected_asset_id = asset_ids[0]
            asset = db.query(ContentAsset).filter(ContentAsset.id == rejected_asset_id).first()
            if asset:
                asset.status = ContentStatus.draft
                
                feedback = Feedback(
                    content_asset_id=asset.id,
                    reason_tag="tone",
                    note="Too casual. Jade is a premium brand, we need to sound more professional and luxurious."
                )
                db.add(feedback)
                db.commit()
                logger.info(f"Simulated human rejection on asset {asset.id} to populate metrics.")
                
        logger.info("Running Lead Pipeline...")
        lead_graph.invoke({
            "brand_id": brand.id,
            "niche": "jewellery",
            "region": "Singapore",
            "generated_lead_ids": []
        })
        logger.info("Demo data seeded successfully.")
        
    except Exception as e:
        logger.warning(f"Could not complete real generation (expected if no GROQ_API_KEY). Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
