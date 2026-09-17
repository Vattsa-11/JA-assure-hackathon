from sqlalchemy.orm import Session
from app.models.brand import Brand
from app.models.content import ContentAsset, ContentVersion, ContentStatus
from app.services.llm_client import llm_client
from app.agents.lessons import get_relevant_lessons

def generate_content(db: Session, brand_id: int, topic: str) -> list[ContentAsset]:
    """
    Generates content variants across platforms.
    """
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise ValueError("Brand not found")

    lessons = get_relevant_lessons(db, brand_id)
    lessons_text = "\n".join(lessons)
    
    system_prompt = f"""You are an expert copywriter for '{brand.name}'.
Brand Voice: {brand.voice_description}

CRITICAL RULES BASED ON PAST FEEDBACK (Avoid these mistakes at all costs):
{lessons_text if lessons_text else "No past feedback yet."}

You must write content for the given topic on three platforms:
1. LinkedIn (Professional, longer, industry-focused)
2. Instagram (Visual caption, engaging, emojis)
3. X/Twitter (Short, hook-first, max 280 chars)

Return the output as a valid JSON object in this format:
{{{{
    "linkedin": "...",
    "instagram": "...",
    "x": "..."
}}}}
"""
    result_json = llm_client.generate_json(
        prompt=f"Topic: {topic}",
        system_prompt=system_prompt,
        model_name="llama3-70b-8192",
        temperature=0.7
    )

    created_assets = []
    for platform, content_text in result_json.items():
        if platform not in ["linkedin", "instagram", "x"]:
            continue
            
        asset = ContentAsset(
            brand_id=brand_id,
            platform=platform,
            language="en",
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
