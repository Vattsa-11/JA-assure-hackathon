from sqlalchemy.orm import Session
from app.models.content import ContentAsset, ContentVersion, ContentStatus
from app.models.media import VideoAsset
from app.models.brand import Brand
from app.services.llm_client import llm_client
from app.services.tts_video_client import tts_video_client
import uuid

def generate_video_script_and_render(db: Session, brand_id: int, topic: str) -> VideoAsset:
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise ValueError("Brand not found")

    system_prompt = f"""You are an expert TikTok/Reels scriptwriter for '{brand.name}'.
Brand Voice: {brand.voice_description}

Write a short, engaging 30-second script about: {topic}.
Return ONLY the exact spoken text, no stage directions, no intro, no emojis. Just the words to be read by the TTS voice.
"""
    script_text = llm_client.generate_text(
        prompt=topic,
        system_prompt=system_prompt,
        model_name="llama3-70b-8192",
        temperature=0.7
    )
    script_text = script_text.strip()
    
    # 1. Save ContentAsset first
    asset = ContentAsset(
        brand_id=brand_id,
        platform="tiktok_reels",
        language="en",
        status=ContentStatus.draft
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    
    version = ContentVersion(
        content_asset_id=asset.id,
        content_text=script_text
    )
    db.add(version)
    
    # 2. Generate Audio
    audio_filename = f"../media/audio_{uuid.uuid4().hex[:8]}.mp3"
    video_filename = f"../media/video_{uuid.uuid4().hex[:8]}.mp4"
    
    tts_video_client.generate_audio(script_text, audio_filename)
    
    # 3. Assemble Video
    tts_video_client.assemble_video(script_text, audio_filename, video_filename)
    
    # 4. Save VideoAsset
    video_asset = VideoAsset(
        content_asset_id=asset.id,
        script_text=script_text,
        video_file_path=video_filename
    )
    db.add(video_asset)
    db.commit()
    db.refresh(video_asset)
    
    return video_asset
