import os
import sys
import logging

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.services.llm_client import llm_client
from app.services.osm_client import osm_client
from app.services.scraping_client import scraping_client
from app.services.tts_video_client import tts_video_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_smoke_tests():
    logger.info("=== Starting Smoke Tests ===")
    
    # 1. Config Test
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY is not set. LLM tests will fail.")
        
    # 2. OSM Test
    logger.info("Testing OSM Client...")
    results = osm_client.find_businesses("jewellery", "Singapore", limit=1)
    if results:
        logger.info(f"OSM Success: Found {results[0]['name']}")
    else:
        logger.warning("OSM Test failed or returned no results.")

    # 3. Scraping Test
    logger.info("Testing Scraping Client...")
    text = scraping_client.scrape_url("https://example.com")
    if text:
        logger.info(f"Scrape Success: Fetched {len(text)} chars from example.com")
    else:
        logger.warning("Scraping Test failed.")

    # 4. TTS Test
    logger.info("Testing TTS Client...")
    audio_path = "../media/test_audio.mp3"
    success = tts_video_client.generate_audio("Hello, this is a smoke test.", audio_path)
    if success:
        logger.info(f"TTS Success: Created {audio_path}")
    else:
        logger.warning("TTS Test failed.")
        
    logger.info("=== Smoke Tests Complete ===")

if __name__ == "__main__":
    run_smoke_tests()
