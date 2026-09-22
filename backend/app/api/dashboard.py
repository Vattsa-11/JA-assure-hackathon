from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.lessons import get_relevant_lessons
from app.core.db import get_db
from app.models.brand import Brand
from app.models.content import (
    ComplianceReview,
    ContentAsset,
    ContentStatus,
    ContentVersion,
    Feedback,
)
from app.models.lead import Lead, LeadStatus
from app.models.media import VideoAsset

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

@router.get("/competitors")
def get_competitor_digests(db: Session = Depends(get_db)):
    """Latest competitor-intelligence digest per tracked URL."""
    from app.models.research import CompetitorDigestEntry

    entries = (
        db.query(CompetitorDigestEntry)
        .order_by(CompetitorDigestEntry.updated_at.desc())
        .all()
    )
    seen: set[str] = set()
    result = []
    for entry in entries:
        if entry.competitor_url in seen:
            continue  # keep only the newest entry per URL
        seen.add(entry.competitor_url)
        result.append({
            "id": entry.id,
            "competitor_url": entry.competitor_url,
            "suggested_action": entry.suggested_action,
            "updated_at": entry.updated_at.isoformat(),
        })
    return result


@router.get("/competitors/tracked")
def list_tracked_competitors(db: Session = Depends(get_db)):
    """The automated watchlist."""
    from app.models.research import TrackedCompetitor

    tracked = db.query(TrackedCompetitor).order_by(TrackedCompetitor.created_at.asc()).all()
    return [{
        "id": t.id,
        "competitor_url": t.competitor_url,
        "name": t.name,
        "source": t.source,       # manual | major | ai
        "status": t.status,       # active | unreachable
        "created_at": t.created_at.isoformat(),
    } for t in tracked]


@router.post("/competitors/tracked")
def add_tracked_competitor(payload: dict, db: Session = Depends(get_db)):
    """Add one URL to the automated watchlist (idempotent)."""
    from app.models.research import TrackedCompetitor

    url = str(payload.get("url", "")).strip()
    if not url:
        return {"error": "url is required"}, 400
    if not url.startswith("http"):
        url = f"https://{url}"

    existing = db.query(TrackedCompetitor).filter(
        TrackedCompetitor.competitor_url == url
    ).first()
    if existing:
        return {"id": existing.id, "competitor_url": existing.competitor_url,
                "name": existing.name, "source": existing.source,
                "status": existing.status, "already": True}

    tracked = TrackedCompetitor(
        competitor_url=url,
        name=str(payload.get("name") or "")[:80] or None,
        source=str(payload.get("source") or "manual")[:16],
    )
    db.add(tracked)
    db.commit()
    db.refresh(tracked)
    return {"id": tracked.id, "competitor_url": tracked.competitor_url,
            "name": tracked.name, "source": tracked.source,
            "status": tracked.status, "already": False}


@router.delete("/competitors/tracked/{tracked_id}")
def remove_tracked_competitor(tracked_id: int, db: Session = Depends(get_db)):
    from app.models.research import TrackedCompetitor

    tracked = db.query(TrackedCompetitor).filter(TrackedCompetitor.id == tracked_id).first()
    if not tracked:
        return {"error": "not found"}, 404
    db.delete(tracked)
    db.commit()
    return {"removed": tracked.competitor_url}


@router.post("/competitors/scan")
def scan_competitors(payload: dict, db: Session = Depends(get_db)):
    """SYNCHRONOUS scan of the given URLs (or the whole watchlist when omitted).

    Returns the real per-URL report so the UI always shows what happened —
    digested / unchanged / unreachable — instead of guessing client-side.
    """
    from app.agents.research import scan_tracked_competitors

    urls = payload.get("urls") or None
    if urls is not None and not isinstance(urls, list):
        return {"error": "urls must be a list"}, 400
    try:
        return scan_tracked_competitors(db, urls=urls)
    except Exception as e:  # noqa: BLE001 - report failure instead of hanging the UI
        return {"scanned_at": None, "results": [], "error": str(e)}


@router.post("/competitors/discover")
def discover_competitors(db: Session = Depends(get_db)):
    """Ask the LLM to suggest real competitor websites for JA Assure
    (insurance for jewellers, clinics, transit/logistics businesses).
    Only returns suggestions; nothing is stored or scraped here — the user
    picks which ones to track, then runs a scan."""
    from app.agents.research import discover_competitors as _discover

    return {"competitors": _discover()}


@router.post("/competitors/research-new")
def research_new_competitors_endpoint(db: Session = Depends(get_db)):
    """Search the market for NEW competitors we don't track yet, scrape each
    candidate, and return a full intelligence digest for the promising ones."""
    from app.agents.research import research_new_competitors as _research

    return _research(db)

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
    feed.sort(key=lambda x: str(x["created_at"]), reverse=True)
    return feed
