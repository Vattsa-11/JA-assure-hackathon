from sqlalchemy.orm import Session
from app.models.content import ContentAsset, ContentVersion, ContentStatus
from app.services.llm_client import llm_client
from app.agents.compliance import check_compliance
import logging

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {
    "ms": "Malay (Bahasa Melayu)",
    "id": "Indonesian (Bahasa Indonesia)",
    "th": "Thai",
    "zh": "Simplified Chinese (Mandarin)"
}

def localize_content(db: Session, asset_id: int, target_language: str) -> ContentAsset:
    """
    Localizes a piece of content with cultural adaptation (not word-for-word translation).
    Runs the localized version through the Compliance Agent independently.
    """
    if target_language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {target_language}. Supported: {list(SUPPORTED_LANGUAGES.keys())}")

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

    language_full = SUPPORTED_LANGUAGES[target_language]

    system_prompt = f"""You are an expert localization specialist for insurance marketing in Southeast Asia.
Your task is to localize the following content into {language_full}.

CRITICAL RULES:
- DO NOT translate word-for-word. Adapt the tone, idioms, and cultural context for a native {language_full} speaker.
- The output must feel completely natural and professional — as if originally written in {language_full}.
- Maintain the original content's intent, platform format, and length constraints.
- For Simplified Chinese: use simplified characters (不要用繁體字).
- Return ONLY the localized text. No explanations, no labels, no English mixed in.
"""

    localized_text = llm_client.generate_text(
        prompt=latest_version.content_text,
        system_prompt=system_prompt,
        model_name="qwen/qwen3.8-27b",
        temperature=0.4
    ).strip()

    if not localized_text:
        raise ValueError("LLM returned empty localized text")

    # Create the localized ContentAsset
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
        content_text=localized_text
    )
    db.add(new_version)
    db.commit()

    # Run independent compliance check on the localized version — master plan requirement
    review = check_compliance(db, new_asset.id)
    if not review.passed:
        logger.warning(
            f"Localized asset {new_asset.id} ({target_language}) failed compliance: {review.flagged_phrases}"
        )
    # Asset status is updated inside check_compliance (passed → pending_review)

    return new_asset
