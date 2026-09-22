import logging

from fastapi import APIRouter, BackgroundTasks

from app.graphs.content_pipeline import ContentState, content_graph
from app.graphs.lead_pipeline import LeadState, lead_graph
from app.schemas.pipeline import (
    ContentRunRequest,
    ImageRunRequest,
    LeadRunRequest,
    VideoRunRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

def _run_content(brand_id: int, topic: str, localize: bool = False, target_languages: list[str] | None = None, language: str = "en"):
    initial_state: ContentState = {
        "brand_id": brand_id,
        "topic": topic,
        "generated_asset_ids": [],
        "passed_asset_ids": [],
        "failed_asset_ids": [],
        "localize": localize,
        "target_languages": target_languages or [],
        "localized_asset_ids": [],
        "localized_failed_ids": [],
        "language": language
    }
    result = content_graph.invoke(initial_state)
    logger.info(
        f"Content pipeline done. Passed: {result.get('passed_asset_ids')}, "
        f"Failed: {result.get('failed_asset_ids')}, "
        f"Localized: {result.get('localized_asset_ids')}"
    )

def _run_leads(brand_id: int, niche: str, region: str, language: str = "en"):
    initial_state: LeadState = {
        "brand_id": brand_id,
        "niche": niche,
        "region": region,
        "generated_lead_ids": [],
        "passed_lead_ids": [],
        "failed_lead_ids": [],
        "language": language
    }
    result = lead_graph.invoke(initial_state)
    logger.info(f"Lead pipeline done. Lead IDs: {result.get('generated_lead_ids')}")

@router.post("/content/run")
def run_content_pipeline(request: ContentRunRequest, background_tasks: BackgroundTasks):
    """
    Triggers the content generation + compliance pipeline as a background task.
    Returns immediately so the browser doesn't time out.
    """
    background_tasks.add_task(
        _run_content, request.brand_id, request.topic, request.localize, request.target_languages, request.language or "en"
    )
    return {"message": "Content pipeline started in background. Check /review/queue for results shortly."}

@router.post("/leads/run")
def run_lead_pipeline(request: LeadRunRequest, background_tasks: BackgroundTasks):
    """
    Triggers the lead discovery + scoring pipeline as a background task.
    """
    background_tasks.add_task(_run_leads, request.brand_id, request.niche, request.region, request.language or "en")
    return {"message": "Lead pipeline started in background. Check /review/leads for results shortly."}

@router.post("/video/run")
def run_video_pipeline(request: VideoRunRequest, background_tasks: BackgroundTasks):
    """
    Triggers video script generation + TTS + assembly as a background task.
    """
    def _run_video(brand_id: int, topic: str, language: str = "en", use_ai_video: bool = False):
        from app.agents.media import generate_video_script_and_render
        from app.core.db import SessionLocal
        db = SessionLocal()
        try:
            generate_video_script_and_render(db, brand_id, topic, language, use_ai_video)
        except Exception as e:  # noqa: BLE001 - fail-soft over external service I/O
            logger.error(f"Video pipeline error: {e}")
        finally:
            db.close()

    background_tasks.add_task(_run_video, request.brand_id, request.topic, request.language or "en", request.use_ai_video)
    return {"message": "Video pipeline started in background."}

@router.post("/image/run")
def run_image_pipeline(request: ImageRunRequest, background_tasks: BackgroundTasks):
    """
    Triggers AI image generation (LLM visual brief -> Replicate) as a background task.
    The resulting ImageAsset + ContentAsset appear in the dashboard feed.
    """
    def _run_image(brand_id: int, topic: str, language: str = "en"):
        from app.agents.image import generate_campaign_image
        from app.core.db import SessionLocal
        db = SessionLocal()
        try:
            generate_campaign_image(db, brand_id, topic, language)
        except Exception as e:  # noqa: BLE001 - fail-soft over external service I/O
            logger.error(f"Image pipeline error: {e}")
        finally:
            db.close()

    background_tasks.add_task(_run_image, request.brand_id, request.topic, request.language or "en")
    return {"message": "Image pipeline started in background."}

