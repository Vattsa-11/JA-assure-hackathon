from sqlalchemy.orm import Session

from app.agents.lessons import get_relevant_lessons
from app.models.brand import Brand
from app.models.content import ContentAsset, ContentStatus, ContentVersion
from app.services.llm_client import llm_client


def generate_content(db: Session, brand_id: int, topic: str) -> list[ContentAsset]:
    """
    Generates 2 A/B content variants per platform (6 assets total for LinkedIn, Instagram, X).
    Injects past rejection lessons to prevent repeating mistakes.
    """
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise ValueError(f"Brand {brand_id} not found")

    lessons = get_relevant_lessons(db, brand_id)
    lessons_text = "\n".join(lessons) if lessons else "No past feedback yet."

    system_prompt = f"""You are an expert copywriter for '{brand.name}'.
Brand Voice: {brand.voice_description}

CRITICAL RULES BASED ON PAST FEEDBACK — Avoid these mistakes at all costs:
{lessons_text}

Generate TWO (2) distinct A/B variants for each of the three platforms below for the given topic.
Variant A and Variant B should have meaningfully different hooks, angles, or tone while staying on-brand.

Platform rules:
- LinkedIn: Professional, longer-form (3-5 paragraphs), industry-focused. No emojis.
- Instagram: Visual, engaging caption (2-3 short paragraphs), relevant emojis, ends with a question or CTA.
- X/Twitter: Short hook-first copy, max 280 characters, punchy and direct.

Return a valid JSON object with this exact structure:
{{{{
    "linkedin_a": "...",
    "linkedin_b": "...",
    "instagram_a": "...",
    "instagram_b": "...",
    "x_a": "...",
    "x_b": "..."
}}}}
"""

    result_json = llm_client.generate_json(
        prompt=f"Topic: {topic}",
        system_prompt=system_prompt,
        model_name="qwen/qwen3.8-27b",
        temperature=0.7
    )

    platform_map = {
        "linkedin_a": "linkedin", "linkedin_b": "linkedin",
        "instagram_a": "instagram", "instagram_b": "instagram",
        "x_a": "x", "x_b": "x"
    }

    created_assets = []
    for key, platform in platform_map.items():
        content_text = result_json.get(key)
        if not content_text:
            continue

        asset = ContentAsset(
            brand_id=brand_id,
            platform=platform,
            language="en",
            topic=topic,
            status=ContentStatus.draft
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)

        version = ContentVersion(
            content_asset_id=asset.id,
            content_text=content_text
        )
        db.add(version)
        db.commit()

        created_assets.append(asset)

    return created_assets
