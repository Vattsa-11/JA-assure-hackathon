from sqlalchemy.orm import Session
from app.models.content import ContentAsset, ContentVersion, ContentStatus
from app.services.llm_client import llm_client

def localize_content(db: Session, asset_id: int, target_language: str) -> ContentAsset:
    """
    Localizes a piece of content, prioritizing cultural relevance over direct translation.
    """
    asset = db.query(ContentAsset).filter(ContentAsset.id == asset_id).first()
    if not asset:
        raise ValueError("Asset not found")
        
    latest_version = db.query(ContentVersion).filter(ContentVersion.content_asset_id == asset.id).order_by(ContentVersion.created_at.desc()).first()
    if not latest_version:
        raise ValueError("No content versions found")
        
    system_prompt = f"""You are an expert localization specialist.
Your task is to localize the following content into {target_language}.
CRITICAL RULE: DO NOT simply translate word-for-word. Adapt the tone, cultural nuances, and phrasing so it feels completely natural to a native {target_language} speaker in their professional environment.
Maintain the original length constraints (e.g. short for X, longer for LinkedIn).

Return ONLY the localized text. Do not wrap in JSON or add any intro/outro sentences.
"""

    localized_text = llm_client.generate_text(
        prompt=latest_version.content_text,
        system_prompt=system_prompt,
        model_name="llama3-70b-8192",
        temperature=0.4
    )

    new_asset = ContentAsset(
        brand_id=asset.brand_id,
        source_asset_id=asset.id,
        platform=asset.platform,
        language=target_language,
        status=ContentStatus.draft
    )
    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)
    
    new_version = ContentVersion(
        content_asset_id=new_asset.id,
        content_text=localized_text.strip()
    )
    db.add(new_version)
    db.commit()
    
    return new_asset
