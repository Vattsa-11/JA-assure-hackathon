from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from app.core.db import SessionLocal
from app.agents.content import generate_content
from app.agents.compliance import check_compliance

class ContentState(TypedDict):
    brand_id: int
    topic: str
    generated_asset_ids: list[int]

def generate_node(state: ContentState):
    db = SessionLocal()
    try:
        assets = generate_content(db, state["brand_id"], state["topic"])
        asset_ids = [a.id for a in assets]
        return {"generated_asset_ids": asset_ids}
    finally:
        db.close()

def compliance_node(state: ContentState):
    db = SessionLocal()
    try:
        for asset_id in state.get("generated_asset_ids", []):
            check_compliance(db, asset_id)
        return state
    finally:
        db.close()

# Build Graph
builder = StateGraph(ContentState)
builder.add_node("generate", generate_node)
builder.add_node("compliance", compliance_node)

builder.add_edge(START, "generate")
builder.add_edge("generate", "compliance")
builder.add_edge("compliance", END)

content_graph = builder.compile()
