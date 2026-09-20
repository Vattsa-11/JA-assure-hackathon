from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from app.core.db import SessionLocal
from app.agents.content import generate_content
from app.agents.compliance import check_compliance
import logging

logger = logging.getLogger(__name__)

class ContentState(TypedDict):
    brand_id: int
    topic: str
    generated_asset_ids: List[int]
    passed_asset_ids: List[int]
    failed_asset_ids: List[int]

def generate_node(state: ContentState) -> dict:
    db = SessionLocal()
    try:
        assets = generate_content(db, state["brand_id"], state["topic"])
        asset_ids = [a.id for a in assets]
        return {"generated_asset_ids": asset_ids, "passed_asset_ids": [], "failed_asset_ids": []}
    finally:
        db.close()

def compliance_node(state: ContentState) -> dict:
    db = SessionLocal()
    passed = []
    failed = []
    try:
        for asset_id in state.get("generated_asset_ids", []):
            try:
                review = check_compliance(db, asset_id)
                if review.passed:
                    passed.append(asset_id)
                else:
                    failed.append(asset_id)
                    logger.info(f"Asset {asset_id} FAILED compliance. Phrases: {review.flagged_phrases}")
            except Exception as e:
                logger.error(f"Compliance check error for asset {asset_id}: {e}")
                failed.append(asset_id)
        return {"passed_asset_ids": passed, "failed_asset_ids": failed}
    finally:
        db.close()

def compliance_router(state: ContentState) -> str:
    """Route to 'done' regardless — failed assets are kept as draft in DB, passed ones are in queue."""
    passed = state.get("passed_asset_ids", [])
    failed = state.get("failed_asset_ids", [])
    logger.info(f"Compliance results: {len(passed)} passed, {len(failed)} failed")
    return "done"

# Build Graph
builder = StateGraph(ContentState)
builder.add_node("generate", generate_node)
builder.add_node("compliance", compliance_node)

builder.add_edge(START, "generate")
builder.add_edge("generate", "compliance")
# Conditional edge: always routes to END but logs pass/fail split
builder.add_conditional_edges("compliance", compliance_router, {"done": END})

content_graph = builder.compile()
