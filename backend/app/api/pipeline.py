from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.schemas.pipeline import ContentRunRequest, LeadRunRequest, VideoRunRequest
from app.graphs.content_pipeline import content_graph
from app.graphs.lead_pipeline import lead_graph
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

def _run_content(brand_id: int, topic: str):
    initial_state = {
        "brand_id": brand_id,
        "topic": topic,
        "generated_asset_ids": [],
        "passed_asset_ids": [],
        "failed_asset_ids": []
    }
    result = content_graph.invoke(initial_state)
    logger.info(
        f"Content pipeline done. Passed: {result.get('passed_asset_ids')}, "
        f"Failed: {result.get('failed_asset_ids')}"
    )

def _run_leads(brand_id: int, niche: str, region: str):
    initial_state = {
        "brand_id": brand_id,
        "niche": niche,
        "region": region,
        "generated_lead_ids": []
    }
    result = lead_graph.invoke(initial_state)
    logger.info(f"Lead pipeline done. Lead IDs: {result.get('generated_lead_ids')}")

@router.post("/content/run")
def run_content_pipeline(request: ContentRunRequest, background_tasks: BackgroundTasks):
    """
    Triggers the content generation + compliance pipeline as a background task.
    Returns immediately so the browser doesn't time out.
    """
    background_tasks.add_task(_run_content, request.brand_id, request.topic)
    return {"message": "Content pipeline started in background. Check /review/queue for results shortly."}

@router.post("/leads/run")
def run_lead_pipeline(request: LeadRunRequest, background_tasks: BackgroundTasks):
    """
    Triggers the lead discovery + scoring pipeline as a background task.
    """
    background_tasks.add_task(_run_leads, request.brand_id, request.niche, request.region)
    return {"message": "Lead pipeline started in background. Check /review/leads for results shortly."}

@router.post("/video/run")
def run_video_pipeline(request: VideoRunRequest, background_tasks: BackgroundTasks):
    """
    Triggers video script generation + TTS + assembly as a background task.
    """
    def _run_video(brand_id: int, topic: str):
        from app.core.db import SessionLocal
        from app.agents.media import generate_video_script_and_render
        db = SessionLocal()
        try:
            generate_video_script_and_render(db, brand_id, topic)
        except Exception as e:
            logger.error(f"Video pipeline error: {e}")
        finally:
            db.close()

    background_tasks.add_task(_run_video, request.brand_id, request.topic)
    return {"message": "Video pipeline started in background."}
