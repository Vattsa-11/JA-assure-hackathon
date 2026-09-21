
from sqlalchemy.orm import Session

from app.models.content import ContentAsset, ContentVersion, Feedback


def get_relevant_lessons(db: Session, brand_id: int, limit: int = 5) -> list[str]:
    """
    Fetches recent rejection notes/lessons for a brand to avoid repeating mistakes.
    Cross-brand contamination is prevented by filtering on brand_id.
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
        lessons.append(f"- Tag: [{f.reason_tag}] Note: {f.note}")
    return lessons

def get_rejection_rate(db: Session) -> float:
    """Returns the percentage of assets that received at least one rejection feedback."""
    total_assets = db.query(ContentAsset).count()
    if total_assets == 0:
        return 0.0
    rejected_count = (
        db.query(ContentAsset)
        .join(Feedback, ContentAsset.id == Feedback.content_asset_id)
        .distinct()
        .count()
    )
    return round((rejected_count / total_assets) * 100, 1)

def get_edit_intensity(db: Session) -> float:
    """
    Returns the average number of ContentVersion rows per ContentAsset.
    > 1.0 means assets required editing after initial generation.
    """
    total_assets = db.query(ContentAsset).count()
    if total_assets == 0:
        return 0.0
    total_versions = db.query(ContentVersion).count()
    return round(total_versions / total_assets, 2)
