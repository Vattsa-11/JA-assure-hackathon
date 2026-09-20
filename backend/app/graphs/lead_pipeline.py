import logging
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.compliance import check_lead_compliance
from app.agents.lead import find_leads
from app.core.db import SessionLocal

logger = logging.getLogger(__name__)

class LeadState(TypedDict):
    brand_id: int
    niche: str
    region: str
    generated_lead_ids: list[int]
    passed_lead_ids: list[int]
    failed_lead_ids: list[int]

def find_leads_node(state: LeadState):
    db = SessionLocal()
    try:
        leads = find_leads(db, state["brand_id"], state["niche"], state["region"])
        lead_ids = [lead.id for lead in leads]
        return {"generated_lead_ids": lead_ids, "passed_lead_ids": [], "failed_lead_ids": []}
    finally:
        db.close()

def compliance_node(state: LeadState):
    db = SessionLocal()
    passed = []
    failed = []
    try:
        for lead_id in state.get("generated_lead_ids", []):
            try:
                is_passed = check_lead_compliance(db, lead_id)
                if is_passed:
                    passed.append(lead_id)
                else:
                    failed.append(lead_id)
                    logger.info(f"Lead {lead_id} outreach failed compliance.")
            except Exception as e:  # noqa: BLE001 -- fail-soft: route the failed lead through, keep the graph alive
                logger.error(f"Lead compliance error for lead {lead_id}: {e}")
                failed.append(lead_id)
        return {"passed_lead_ids": passed, "failed_lead_ids": failed}
    finally:
        db.close()

def compliance_router(state: LeadState) -> str:
    passed = state.get("passed_lead_ids", [])
    failed = state.get("failed_lead_ids", [])
    logger.info(f"Lead compliance results: {len(passed)} passed, {len(failed)} failed")
    return "done"

builder = StateGraph(LeadState)
builder.add_node("find_leads", find_leads_node)
builder.add_node("compliance", compliance_node)

builder.add_edge(START, "find_leads")
builder.add_edge("find_leads", "compliance")
builder.add_conditional_edges("compliance", compliance_router, {"done": END})

lead_graph = builder.compile()
