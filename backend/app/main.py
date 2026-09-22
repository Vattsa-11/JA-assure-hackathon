import logging
import os
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.dashboard import router as dashboard_router
from app.api.pipeline import router as pipeline_router
from app.api.review import router as review_router
from app.api.translate import router as translate_router

app = FastAPI(title="JA Assure AI Marketing Agent")

# Make app-level loggers (agents, services) visible in uvicorn output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(review_router)
app.include_router(pipeline_router)
app.include_router(dashboard_router)
app.include_router(translate_router)

# Mount media directory for videos
media_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "media"))
if not os.path.exists(media_dir):
    os.makedirs(media_dir)
app.mount("/media", StaticFiles(directory=media_dir), name="media")


@app.get("/")
def read_root():
    return {"status": "ok"}


@app.on_event("startup")
def startup_tasks() -> None:
    """Seed major competitors, start the auto-scan scheduler, and warm caches."""
    # 1. Competitor watchlist: seed known majors + start 6-hourly auto-scan
    def _competitor_setup():
        try:
            from app.agents.research import seed_major_competitors, start_auto_scanner
            from app.core.db import SessionLocal

            db = SessionLocal()
            try:
                seed_major_competitors(db)
            finally:
                db.close()
            start_auto_scanner()
        except Exception as e:  # noqa: BLE001 - setup must never crash the app
            logging.getLogger(__name__).error(f"Competitor setup failed: {e}")

    threading.Thread(target=_competitor_setup, name="competitor-setup", daemon=True).start()

    # 2. Translation warm-up (pre-existing)
    def _warm():
        try:
            from app.services.translation_service import warm_language_caches
            logging.getLogger(__name__).info("Translation warm-up starting...")
            summary = warm_language_caches()
            logging.getLogger(__name__).info(f"Translation warm-up finished: {summary}")
        except Exception as e:  # noqa: BLE001 - warm-up must never crash the app
            logging.getLogger(__name__).error(f"Startup translation warm-up failed: {e}")

    threading.Thread(target=_warm, name="translation-warmup", daemon=True).start()
