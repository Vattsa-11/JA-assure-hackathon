import sys
import os
import logging
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.db import SessionLocal
from app.models.brand import Brand

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = TestClient(app)

def run_pipeline_tests():
    db = SessionLocal()
    brand = db.query(Brand).filter(Brand.name == 'Jade').first()
    db.close()
    
    if not brand:
        logger.error("No Jade brand found. Please run seed script first.")
        return

    logger.info("=== Testing Content Pipeline Endpoint ===")
    try:
        response = client.post("/pipeline/content/run", json={
            "brand_id": brand.id,
            "topic": "The benefits of business insurance for retailers"
        })
        logger.info(f"Status: {response.status_code}")
        logger.info(f"Response: {response.json()}")
    except Exception as e:
        logger.error(f"Pipeline failed (expected if no API key): {e}")

    logger.info("=== Testing Lead Pipeline Endpoint ===")
    try:
        response = client.post("/pipeline/leads/run", json={
            "brand_id": brand.id,
            "niche": "jewellery",
            "region": "Singapore"
        })
        logger.info(f"Status: {response.status_code}")
        logger.info(f"Response: {response.json()}")
    except Exception as e:
        logger.error(f"Pipeline failed (expected if no API key): {e}")

if __name__ == "__main__":
    run_pipeline_tests()
