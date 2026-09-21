from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.content import ContentAsset, ContentStatus, ContentVersion, ComplianceReview, Feedback
from app.models.lead import Lead, LeadStatus
from app.models.media import VideoAsset
from app.models.brand import Brand
from app.agents.lessons import get_relevant_lessons

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    # ContentAsset aggregates
    content_pending = db.query(ContentAsset).filter(ContentAsset.status == ContentStatus.pending_review).count()
    content_approved = db.query(ContentAsset).filter(ContentAsset.status == ContentStatus.approved).count()
    
    # We consider rejected if a Feedback row exists for a given asset
    content_rejected = db.query(ContentAsset).join(Feedback).distinct().count()

    # Lead aggregates
    lead_pending = db.query(Lead).filter(Lead.status == LeadStatus.pending_review).count()
    lead_approved = db.query(Lead).filter(Lead.status == LeadStatus.approved).count()
    
    # Video counts
    video_count = db.query(VideoAsset).count()

    return {
        "pending": content_pending + lead_pending,
        "approved": content_approved + lead_approved,
        "rejected": content_rejected,
        "videos": video_count
    }

@router.get("/brands")
def get_brands(db: Session = Depends(get_db)):
    brands = db.query(Brand).all()
    return [{"id": b.id, "name": b.name} for b in brands]

@router.get("/feed")
def get_feed(db: Session = Depends(get_db)):
    feed = []

    # 1. Content Assets
    content_assets = db.query(ContentAsset).order_by(ContentAsset.created_at.desc()).all()
    for asset in content_assets:
        review = db.query(ComplianceReview).filter(ComplianceReview.content_asset_id == asset.id).order_by(ComplianceReview.created_at.desc()).first()
        is_blocked = (asset.status == ContentStatus.draft) and (review is not None and not review.passed)
        has_feedback = db.query(Feedback).filter(Feedback.content_asset_id == asset.id).first() is not None
        
        # Only include if pending_review, approved, blocked, or rejected with feedback
        if asset.status == ContentStatus.draft and not is_blocked and not has_feedback:
            continue

        latest_version = db.query(ContentVersion).filter(ContentVersion.content_asset_id == asset.id).order_by(ContentVersion.created_at.desc()).first()
        lessons = get_relevant_lessons(db, asset.brand_id)
        
        status_label = asset.status.value
        if is_blocked:
            status_label = "blocked"
        elif has_feedback and asset.status == ContentStatus.draft:
            status_label = "rejected"
            
        feed.append({
            "id": asset.id,
            "type": "TEXT",
            "topic": asset.topic,
            "status": status_label,
            "brand_name": asset.brand.name if asset.brand else "Unknown",
            "platform": asset.platform,
            "language": asset.language,
            "content_text": latest_version.content_text if latest_version else "",
            "created_at": asset.created_at.isoformat(),
            "compliance": {
                "passed": review.passed,
                "flagged_phrases": review.flagged_phrases,
                "reasons": review.reasons
            } if review else None,
            "lessons": lessons
        })

    # 2. Leads
    leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
    for lead in leads:
        if lead.status == LeadStatus.draft:
            continue
        feed.append({
            "id": lead.id,
            "type": "LEAD",
            "topic": lead.niche,
            "status": lead.status.value,
            "business_name": lead.business_name,
            "niche": lead.niche,
            "fit_reason": lead.fit_reason,
            "draft_outreach": lead.draft_outreach,
            "created_at": lead.created_at.isoformat(),
        })

    # 3. Videos
    videos = db.query(VideoAsset).order_by(VideoAsset.created_at.desc()).all()
    for video in videos:
        stage = "Script Generated"
        # Since we use moviepy, if video_file_path is populated, it's rendered.
        if video.video_file_path:
            stage = "Video Rendered"
            
        c_asset = db.query(ContentAsset).filter(ContentAsset.id == video.content_asset_id).first()
        brand_name = c_asset.brand.name if (c_asset and c_asset.brand) else "Unknown"

        feed.append({
            "id": video.id,
            "type": "VIDEO",
            "topic": video.topic,
            "status": "approved", # Videos don't have a status enum in VideoAsset currently
            "brand_name": brand_name,
            "script_text": video.script_text,
            "video_file_path": video.video_file_path,
            "stage": stage,
            "created_at": video.created_at.isoformat(),
        })

    # Sort unified feed by created_at desc
    feed.sort(key=lambda x: x["created_at"], reverse=True)
    return feed
