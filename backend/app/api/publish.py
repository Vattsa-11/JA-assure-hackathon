"""Social publishing endpoints backed by Postiz.

The dashboard review modal calls these to publish approved campaign content
to connected social channels. The Postiz API key never leaves the backend.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.content import ContentAsset, ContentStatus, ContentVersion
from app.services.postiz_client import postiz_client

router = APIRouter(prefix="/publish", tags=["Publish"])


@router.get("/status")
def publish_status():
    """Whether Postiz publishing is configured (drives UI hints)."""
    return {"configured": postiz_client.configured}


@router.get("/integrations")
def list_integrations():
    """Connected social channels for the channel picker."""
    return postiz_client.list_integrations()


class PublishRequest(BaseModel):
    asset_id: int
    integration_ids: list[str]
    content_override: str | None = None
    image_urls: list[str] | None = None
    publish_type: str = "now"  # now | schedule | draft
    date: str | None = None


def _latest_content(db: Session, asset_id: int) -> tuple[ContentAsset, str]:
    asset = db.query(ContentAsset).filter(ContentAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    version = (
        db.query(ContentVersion)
        .filter(ContentVersion.content_asset_id == asset.id)
        .order_by(ContentVersion.created_at.desc())
        .first()
    )
    return asset, (version.content_text if version else "")


@router.post("/posts")
def publish_posts(request: PublishRequest, db: Session = Depends(get_db)):
    """Publish (or schedule/draft) a campaign asset's content via Postiz.

    Only approved assets can be published — the compliance/human gate stays intact.
    """
    asset, latest_text = _latest_content(db, request.asset_id)

    if asset.status != ContentStatus.approved:
        raise HTTPException(status_code=400, detail="Only approved assets can be published")

    content = (request.content_override or latest_text or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Asset has no content to publish")

    result = postiz_client.create_post(
        integration_ids=request.integration_ids,
        content=content,
        image_urls=request.image_urls,
        publish_type=request.publish_type,
        date=request.date,
        platform=asset.platform,
    )
    if result and isinstance(result[0], dict) and "error" in result[0]:
        raise HTTPException(status_code=502, detail=result[0]["error"])

    return {
        "published": True,
        "asset_id": asset.id,
        "channels": request.integration_ids,
        "postiz": result,
    }
