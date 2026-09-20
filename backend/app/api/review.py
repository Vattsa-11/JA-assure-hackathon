from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.content import ContentAsset, ContentStatus, Feedback, ContentVersion
from app.schemas.review import RejectRequest, EditRequest

router = APIRouter(prefix="/review", tags=["Review"])

@router.get("/queue")
def get_review_queue(db: Session = Depends(get_db)):
    assets = db.query(ContentAsset).filter(ContentAsset.status == ContentStatus.pending_review).all()
    
    # Return limited info for the queue
    result = []
    for asset in assets:
        latest_version = db.query(ContentVersion).filter(ContentVersion.content_asset_id == asset.id).order_by(ContentVersion.created_at.desc()).first()
        result.append({
            "id": asset.id,
            "brand_id": asset.brand_id,
            "brand_name": asset.brand.name if asset.brand else "Unknown",
            "platform": asset.platform,
            "language": asset.language,
            "content_text": latest_version.content_text if latest_version else ""
        })
    return result

@router.post("/{asset_id}/approve")
def approve_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.query(ContentAsset).filter(ContentAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    asset.status = ContentStatus.approved
    db.commit()
    return {"message": "Asset approved"}

@router.post("/{asset_id}/edit")
def edit_asset(asset_id: int, request: EditRequest, db: Session = Depends(get_db)):
    asset = db.query(ContentAsset).filter(ContentAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    version = ContentVersion(content_asset_id=asset.id, content_text=request.new_content_text)
    db.add(version)
    asset.status = ContentStatus.approved
    db.commit()
    return {"message": "Asset edited and approved"}

@router.post("/{asset_id}/reject")
def reject_asset(asset_id: int, request: RejectRequest, db: Session = Depends(get_db)):
    asset = db.query(ContentAsset).filter(ContentAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    feedback = Feedback(
        content_asset_id=asset.id,
        reason_tag=request.reason_tag,
        note=request.note
    )
    db.add(feedback)
    
    asset.status = ContentStatus.draft 
    db.commit()
    return {"message": "Asset rejected and feedback recorded"}

@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    from app.agents.lessons import get_rejection_rate, get_edit_intensity
    return {
        "rejection_rate": get_rejection_rate(db),
        "edit_intensity": get_edit_intensity(db)
    }

@router.get("/leads")
def get_leads(db: Session = Depends(get_db)):
    from app.models.lead import Lead
    from app.schemas.review import LeadSchema
    leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
    return [LeadSchema.model_validate(l) for l in leads]

@router.post("/leads/{lead_id}/approve")
def approve_lead(lead_id: int, db: Session = Depends(get_db)):
    from app.models.lead import Lead, LeadStatus
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.status = LeadStatus.approved
    db.commit()
    return {"message": "Lead approved"}

@router.post("/leads/{lead_id}/reject")
def reject_lead(lead_id: int, db: Session = Depends(get_db)):
    from app.models.lead import Lead, LeadStatus
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.status = LeadStatus.rejected
    db.commit()
    return {"message": "Lead rejected"}
