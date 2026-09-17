from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from app.core.db import SessionLocal
from app.agents.lead import find_leads

class LeadState(TypedDict):
    brand_id: int
    niche: str
    region: str
    generated_lead_ids: list[int]

def find_leads_node(state: LeadState):
    db = SessionLocal()
    try:
        leads = find_leads(db, state["brand_id"], state["niche"], state["region"])
        lead_ids = [l.id for l in leads]
        return {"generated_lead_ids": lead_ids}
    finally:
        db.close()

builder = StateGraph(LeadState)
builder.add_node("find_leads", find_leads_node)

builder.add_edge(START, "find_leads")
builder.add_edge("find_leads", END)

lead_graph = builder.compile()
