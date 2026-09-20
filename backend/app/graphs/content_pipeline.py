import logging
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.compliance import check_compliance
from app.agents.content import generate_content
from app.agents.localization import localize_content, resolve_target_languages
from app.core.db import SessionLocal
from app.models.content import ContentStatus

logger = logging.getLogger(__name__)

class ContentState(TypedDict):
    brand_id: int
    topic: str
    generated_asset_ids: list[int]
    passed_asset_ids: list[int]
    failed_asset_ids: list[int]
    # Localization (opt-in): localize every compliance-passed asset into the
    # requested target languages, each independently compliance-checked.
    localize: bool
    target_languages: list[str]
    localized_asset_ids: list[int]
    localized_failed_ids: list[int]

def generate_node(state: ContentState) -> dict:
    db = SessionLocal()
    try:
        assets = generate_content(db, state["brand_id"], state["topic"])
        asset_ids = [a.id for a in assets]
        return {
            "generated_asset_ids": asset_ids,
            "passed_asset_ids": [],
            "failed_asset_ids": [],
            "localized_asset_ids": [],
            "localized_failed_ids": [],
        }
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
            except Exception as e:  # noqa: BLE001 -- fail-soft: route the failed asset through, keep the graph alive
                logger.error(f"Compliance check error for asset {asset_id}: {e}")
                failed.append(asset_id)
        return {"passed_asset_ids": passed, "failed_asset_ids": failed}
    finally:
        db.close()

def localize_node(state: ContentState) -> dict:
    """
    For every compliance-passed asset, create a localized version per target
    language. Each localized version runs through the compliance agent
    independently inside localize_content (master plan 3E). Fail-soft per
    (asset, language): one LLM failure must not abort the remaining work.
    """
    db = SessionLocal()
    localized = []
    failed = []
    try:
        target_languages = resolve_target_languages(state.get("target_languages"))
        logger.info(f"Localizing {len(state.get('passed_asset_ids', []))} assets into {target_languages}")
        for asset_id in state.get("passed_asset_ids", []):
            for lang in target_languages:
                try:
                    new_asset = localize_content(db, asset_id, lang)
                    if new_asset.status == ContentStatus.pending_review:
                        localized.append(new_asset.id)
                    else:
                        failed.append(new_asset.id)
                        logger.info(f"Localized asset {new_asset.id} ({lang}) did not pass compliance")
                except Exception as e:  # noqa: BLE001 -- fail-soft: skip this (asset, language), keep localizing
                    logger.error(f"Localization to '{lang}' failed for asset {asset_id}: {e}")
        logger.info(f"Localization results: {len(localized)} passed, {len(failed)} failed compliance")
        return {"localized_asset_ids": localized, "localized_failed_ids": failed}
    finally:
        db.close()

def compliance_router(state: ContentState) -> str:
    """Route to localization when requested, otherwise straight to END.

    Failed assets are kept as draft in DB, passed ones go to the review queue
    (and, when localization is on, become the source for localized versions).
    """
    if state.get("localize") and state.get("passed_asset_ids"):
        return "localize"
    passed = state.get("passed_asset_ids", [])
    failed = state.get("failed_asset_ids", [])
    logger.info(f"Compliance results: {len(passed)} passed, {len(failed)} failed")
    return "done"

# Build Graph
builder = StateGraph(ContentState)
builder.add_node("generate", generate_node)
builder.add_node("compliance", compliance_node)
builder.add_node("localize", localize_node)

builder.add_edge(START, "generate")
builder.add_edge("generate", "compliance")
# Conditional edge: passed assets may flow into localization; failed ones end here.
builder.add_conditional_edges("compliance", compliance_router, {"localize": "localize", "done": END})
builder.add_edge("localize", END)

content_graph = builder.compile()
