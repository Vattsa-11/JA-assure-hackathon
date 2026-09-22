import logging
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.compliance import check_compliance
from app.agents.content import generate_content
from app.agents.localization import localize_content, resolve_target_languages
from app.core.db import SessionLocal
from app.models.content import ContentAsset

logger = logging.getLogger(__name__)


class ContentState(TypedDict):
    brand_id: int
    topic: str
    generated_asset_ids: list[int]
    passed_asset_ids: list[int]
    failed_asset_ids: list[int]
    localize: bool
    target_languages: list[str]
    localized_asset_ids: list[int]
    localized_failed_ids: list[int]
    # Native generation language for this campaign ("en" default)
    language: str


def generate_node(state: ContentState) -> dict:
    db = SessionLocal()
    try:
        assets = generate_content(db, state["brand_id"], state["topic"], state.get("language", "en"))
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
            except Exception as e:  # noqa: BLE001 - fail-soft over external service I/O
                logger.error(f"Compliance check error for asset {asset_id}: {e}")
                failed.append(asset_id)
        return {"passed_asset_ids": passed, "failed_asset_ids": failed}
    finally:
        db.close()


def localize_node(state: ContentState) -> dict:
    """Localize passed assets into the requested languages. Fail-soft: an error on one
    asset/language never aborts the whole pipeline run."""
    localized: list[int] = []
    failed: list[int] = []
    if not state.get("localize"):
        return {"localized_asset_ids": [], "localized_failed_ids": []}

    targets = resolve_target_languages(state.get("target_languages"))
    db = SessionLocal()
    try:
        for asset_id in state.get("passed_asset_ids", []):
            # Missing assets are skipped silently — they were likely deleted mid-run.
            if db.query(ContentAsset).filter(ContentAsset.id == asset_id).first() is None:
                logger.warning(f"Localization skipped: asset {asset_id} not found")
                continue
            for lang in targets:
                try:
                    asset = localize_content(db, asset_id, lang)
                    localized.append(asset.id)
                except Exception as e:  # noqa: BLE001 - fail-soft over external service I/O
                    logger.error(f"Localization failed for asset {asset_id} -> {lang}: {e}")
                    failed.append(asset_id)
        return {"localized_asset_ids": localized, "localized_failed_ids": failed}
    finally:
        db.close()


def compliance_router(state: ContentState) -> str:
    """Route to 'localize' when localization is requested, otherwise straight to END.
    Failed assets are kept as draft in DB, passed ones are in queue."""
    passed = state.get("passed_asset_ids", [])
    failed = state.get("failed_asset_ids", [])
    logger.info(f"Compliance results: {len(passed)} passed, {len(failed)} failed")
    if state.get("localize") and passed:
        return "localize"
    return "done"


# Build Graph
builder = StateGraph(ContentState)
builder.add_node("generate", generate_node)
builder.add_node("compliance", compliance_node)
builder.add_node("localize", localize_node)

builder.add_edge(START, "generate")
builder.add_edge("generate", "compliance")
builder.add_conditional_edges("compliance", compliance_router, {"localize": "localize", "done": END})
builder.add_edge("localize", END)

content_graph = builder.compile()
