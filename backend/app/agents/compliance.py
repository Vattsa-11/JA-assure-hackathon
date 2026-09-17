from sqlalchemy.orm import Session
from app.models.content import ContentAsset, ContentVersion, ComplianceReview, ContentStatus
from app.services.llm_client import llm_client

def check_compliance(db: Session, asset_id: int) -> ComplianceReview:
    """
    Checks an asset against a strict compliance rubric.
    """
    asset = db.query(ContentAsset).filter(ContentAsset.id == asset_id).first()
    if not asset:
        raise ValueError("Asset not found")
        
    latest_version = db.query(ContentVersion).filter(ContentVersion.content_asset_id == asset.id).order_by(ContentVersion.created_at.desc()).first()
    if not latest_version:
        raise ValueError("No content versions found for asset")

    system_prompt = """You are a strict legal and compliance reviewer for insurance marketing material.
Evaluate the content against the following rubric. If ANY rule is broken, passed=false.

RUBRIC:
1. NO ABSOLUTE GUARANTEES: Cannot say "guarantees 100% payout, always" or "guaranteed approval".
2. NO FALSE URGENCY: Cannot use manipulative urgency like "Buy now before it's too late!"
3. CLEAR EXCLUSIONS: Must not imply coverage for everything without exceptions.
4. PROFESSIONAL TONE: No defamatory language against competitors.

Return JSON in this format:
{{
    "passed": true_or_false,
    "flagged_phrases": ["phrase 1", "phrase 2"],
    "reasons": ["reason for phrase 1", "reason for phrase 2"]
}}
"""

    result = llm_client.generate_json(
        prompt=f"Content to review:\n{latest_version.content_text}",
        system_prompt=system_prompt,
        model_name="llama3-8b-8192",
        temperature=0.0
    )

    review = ComplianceReview(
        content_asset_id=asset.id,
        passed=result.get("passed", False),
        flagged_phrases=result.get("flagged_phrases", []),
        reasons=result.get("reasons", [])
    )
    db.add(review)
    
    if review.passed:
        asset.status = ContentStatus.pending_review
    
    db.commit()
    db.refresh(review)
    return review
