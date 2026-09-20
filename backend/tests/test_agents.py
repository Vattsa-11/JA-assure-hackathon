import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.compliance import check_compliance
from app.agents.content import generate_content
from app.agents.lead import find_leads
from app.agents.lessons import get_relevant_lessons
from app.core.db import SessionLocal
from app.models.brand import Brand

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_agent_tests():
    db = SessionLocal()

    brand = db.query(Brand).filter(Brand.name == 'Jade').first()
    if not brand:
        logger.error("No Jade brand found. Please run seed script first.")
        return

    logger.info("=== Testing Content Generation ===")
    assets = generate_content(db, brand.id, "The importance of jewelry insurance.")
    logger.info(f"Generated {len(assets)} assets.")

    if assets:
        logger.info("=== Testing Compliance Check ===")
        review = check_compliance(db, assets[0].id)
        logger.info(f"Compliance passed: {review.passed}")

    logger.info("=== Testing Feedback Loop ===")
    lessons = get_relevant_lessons(db, brand.id)
    logger.info(f"Lessons found: {len(lessons)}")

    logger.info("=== Testing Lead Generation ===")
    leads = find_leads(db, brand.id, "jewellery", "Singapore")
    logger.info(f"Generated {len(leads)} leads.")
    for lead in leads:
        logger.info(f"- {lead.business_name} (Score: {lead.fit_score})")

if __name__ == "__main__":
    run_agent_tests()
