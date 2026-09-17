from sqlalchemy.orm import Session
from app.models.content import ContentAsset, ContentVersion, ComplianceReview, ContentStatus
from app.services.llm_client import llm_client

def check_compliance(db: Session, asset_id: int) -> ComplianceReview:
    """
    Checks an asset against a strict 10-rule compliance rubric.
    Passed assets move to pending_review. Failed assets stay as draft.
    """
    asset = db.query(ContentAsset).filter(ContentAsset.id == asset_id).first()
    if not asset:
        raise ValueError(f"Asset {asset_id} not found")

    latest_version = (
        db.query(ContentVersion)
        .filter(ContentVersion.content_asset_id == asset.id)
        .order_by(ContentVersion.created_at.desc())
        .first()
    )
    if not latest_version:
        raise ValueError(f"No content versions found for asset {asset_id}")

    system_prompt = """You are a strict legal and compliance reviewer for insurance marketing material in Southeast Asia.
Evaluate the content against ALL of the following 10 rules. If ANY rule is broken, return passed=false.

RUBRIC (10 rules):
1. NO ABSOLUTE GUARANTEES: Cannot use phrases like "guarantees 100% payout", "guaranteed approval", "always pays out", or "certain payout".
2. NO FALSE URGENCY: Cannot use manipulative urgency like "Buy now before it's too late!", "Limited time only — don't miss out!", or "Act now or lose your chance!".
3. NO MISLEADING SCOPE: Must not imply the policy covers everything without exceptions (e.g., "covers all losses", "total protection from everything").
4. PROFESSIONAL TONE: No defamatory, mocking, or disparaging language about competitors by name or implication.
5. NO INCOME PROMISES: Cannot promise specific monetary returns, specific payout amounts, or investment-like gains (e.g., "earn 10% returns", "guaranteed income").
6. LICENSED ADVICE DISCLAIMER: Must not present insurance advice as a substitute for professional consultation without any appropriate context.
7. NO FEAR MONGERING: Cannot use excessively alarming language to manipulate decisions (e.g., "you WILL lose everything if you don't act now").
8. CULTURALLY APPROPRIATE: Content must not contain language or imagery inappropriate for a professional Southeast Asian business audience.
9. FACTUAL ACCURACY: Must not contain claims that are demonstrably false about insurance products in general (e.g., "all insurance pays within 24 hours").
10. CLEAR CALL-TO-ACTION: If a CTA is present, it must be clear and not deceptive (no hidden costs implied, no bait-and-switch language).

Return JSON ONLY in this exact format:
{
    "passed": true,
    "flagged_phrases": [],
    "reasons": []
}

Or if failed:
{
    "passed": false,
    "flagged_phrases": ["exact phrase from content that violates a rule"],
    "reasons": ["which rule number and why it was violated"]
}
"""

    result = llm_client.generate_json(
        prompt=f"Content to review:\n\n{latest_version.content_text}",
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
    # Failed assets remain as 'draft' — they never reach the queue

    db.commit()
    db.refresh(review)
    return review
