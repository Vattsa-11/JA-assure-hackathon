from fastapi import APIRouter
from app.schemas.pipeline import ContentRunRequest, LeadRunRequest
from app.graphs.content_pipeline import content_graph
from app.graphs.lead_pipeline import lead_graph

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

@router.post("/content/run")
def run_content_pipeline(request: ContentRunRequest):
    initial_state = {
        "brand_id": request.brand_id,
        "topic": request.topic,
        "generated_asset_ids": []
    }
    result = content_graph.invoke(initial_state)
    return {"message": "Pipeline completed", "asset_ids": result.get("generated_asset_ids", [])}

@router.post("/leads/run")
def run_lead_pipeline(request: LeadRunRequest):
    initial_state = {
        "brand_id": request.brand_id,
        "niche": request.niche,
        "region": request.region,
        "generated_lead_ids": []
    }
    result = lead_graph.invoke(initial_state)
    return {"message": "Pipeline completed", "lead_ids": result.get("generated_lead_ids", [])}
