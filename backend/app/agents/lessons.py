from sqlalchemy.orm import Session
from app.models.content import Feedback
from app.models.content import ContentAsset
from sqlalchemy import func
from typing import List

def get_relevant_lessons(db: Session, brand_id: int, limit: int = 5) -> List[str]:
    """
    Fetches recent rejection notes/lessons for a brand to avoid repeating mistakes.
    """
    feedbacks = (
        db.query(Feedback)
        .join(ContentAsset, Feedback.content_asset_id == ContentAsset.id)
        .filter(ContentAsset.brand_id == brand_id)
        .order_by(Feedback.created_at.desc())
        .limit(limit)
        .all()
    )
    
    lessons = []
    for f in feedbacks:
        lessons.append(f"- Tag: {f.reason_tag}, Note: {f.note}")
    return lessons

def get_rejection_rate(db: Session) -> float:
    """Returns the percentage of content that has feedback/rejections."""
    total_assets = db.query(ContentAsset).count()
    if total_assets == 0:
        return 0.0
        
    rejected_count = db.query(ContentAsset).join(Feedback, ContentAsset.id == Feedback.content_asset_id).distinct().count()
    return (rejected_count / total_assets) * 100

def get_edit_intensity(db: Session) -> float:
    # Dummy metric for now, could be average number of versions per asset
    return 0.0
