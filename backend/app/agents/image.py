"""Image generation agent: LLM image brief -> Replicate text-to-image -> ImageAsset.

Follows the same pattern as the media (video) agent: a ContentAsset is created
for review-queue visibility, compliance runs on the image *prompt* (the only
text a regulator would see), then the image is generated and stored in media/.
"""

import logging
import uuid

from sqlalchemy.orm import Session

from app.agents.compliance import check_compliance
from app.core.config import settings
from app.models.brand import Brand
from app.models.content import ContentAsset, ContentStatus, ContentVersion
from app.models.media import ImageAsset
from app.services.llm_client import llm_client
from app.services.replicate_client import (
    build_image_prompt,
    generate_image_with_fallback,
)

logger = logging.getLogger(__name__)


def _image_brief(brand: Brand, topic: str, language: str) -> str:
    """Ask the LLM for a short visual brief describing the scene to render."""
    system_prompt = f"""You are an art director for '{brand.name}', an insurance brand.
Brand voice: {brand.voice_description}
Write a 2-3 sentence visual brief for a social media image about: {topic}.
Describe ONLY what is visible in the scene (subject, setting, mood, colors).
No text/letters/logos in the image. No people's faces in close-up. No claims or promises.
"""
    try:
        brief = llm_client.generate_text(
            prompt=topic,
            system_prompt=system_prompt,
            model_name="qwen/qwen3.8-27b",
            temperature=0.6,
        )
        return (brief or topic).strip()[:600]
    except Exception as e:  # noqa: BLE001 - fail-soft: fall back to the raw topic
        logger.warning(f"Image brief LLM call failed, using topic directly: {e}")
        return topic[:600]


def generate_campaign_image(db: Session, brand_id: int, topic: str, language: str = "en") -> ImageAsset:
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise ValueError(f"Brand {brand_id} not found")

    # 1. Visual brief from the LLM (falls back to topic on failure)
    brief = _image_brief(brand, topic, language)

    # 2. Deterministic, style-consistent prompt
    prompt = build_image_prompt(brief)

    # 3. ContentAsset + version so the image appears in the review flow
    asset = ContentAsset(
        brand_id=brand_id,
        platform="image",
        language=language if language else "en",
        topic=topic,
        status=ContentStatus.pending_review,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    db.add(ContentVersion(content_asset_id=asset.id, content_text=prompt))
    db.commit()

    # 4. Compliance gate on the prompt text (mirrors the video flow)
    review = check_compliance(db, asset.id)
    if not review.passed:
        logger.warning(f"Image prompt failed compliance for asset {asset.id}: {review.flagged_phrases}")
        raise ValueError(f"Image prompt did not pass compliance. Flagged: {review.flagged_phrases}")

    # 5. Generate the image (Pollinations free tier first, Replicate fallback)
    filename = f"image_{uuid.uuid4().hex[:8]}.jpg"
    saved, provider = generate_image_with_fallback(prompt, filename)
    if not saved:
        image_asset = ImageAsset(
            content_asset_id=asset.id, topic=topic, prompt=prompt,
            model=f"provider:{settings.IMAGE_PROVIDER}", status="failed",
        )
        db.add(image_asset)
        db.commit()
        db.refresh(image_asset)
        raise RuntimeError(f"Image generation failed: {provider}")

    image_asset = ImageAsset(
        content_asset_id=asset.id, topic=topic, prompt=prompt,
        model=provider, image_file_path=saved,
        status="generated",
    )
    db.add(image_asset)
    db.commit()
    db.refresh(image_asset)
    logger.info(f"Image generated for asset {asset.id}: {saved}")
    return image_asset
