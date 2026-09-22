import logging
import uuid

from sqlalchemy.orm import Session

from app.agents.compliance import check_compliance
from app.models.brand import Brand
from app.models.content import ContentAsset, ContentStatus, ContentVersion
from app.models.media import VideoAsset
from app.services.llm_client import llm_client
from app.services.tts_video_client import tts_video_client
from app.services.translation_service import TARGET_LANGUAGES

logger = logging.getLogger(__name__)

def generate_video_script_and_render(db: Session, brand_id: int, topic: str, language: str = "en") -> VideoAsset:
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise ValueError(f"Brand {brand_id} not found")

    language_instruction = ""
    if language != "en" and language in TARGET_LANGUAGES:
        language_full = TARGET_LANGUAGES[language]
        language_instruction = (
            f"\nLANGUAGE REQUIREMENT: Write the script natively in {language_full} — not "
            f"translated English. Adapt tone and cultural context for a native {language_full} speaker.\n"
        )

    system_prompt = f"""You are an expert TikTok/Reels scriptwriter for '{brand.name}'.
Brand Voice: {brand.voice_description}
{language_instruction}
Write a short, engaging 30-second voiceover script about: {topic}.
Return ONLY the exact spoken words — no stage directions, no scene labels, no emojis, no formatting. Just the narration text.
"""
    script_text = llm_client.generate_text(
        prompt=topic,
        system_prompt=system_prompt,
        model_name="qwen/qwen3.8-27b",
        temperature=0.7
    ).strip()

    # 1. Save ContentAsset + version (must happen before compliance check)
    asset = ContentAsset(
        brand_id=brand_id,
        platform="tiktok_reels",
        language=language if (language in TARGET_LANGUAGES) else "en",
        topic=topic,
        status=ContentStatus.draft
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    version = ContentVersion(content_asset_id=asset.id, content_text=script_text)
    db.add(version)
    db.commit()

    # 2. Run compliance on the script text — master plan requires this
    review = check_compliance(db, asset.id)
    if not review.passed:
        logger.warning(f"Video script failed compliance for asset {asset.id}: {review.flagged_phrases}")
        raise ValueError(f"Video script did not pass compliance. Flagged: {review.flagged_phrases}")

    # 3. Generate TTS audio
    audio_filename = tts_video_client.get_media_path(f"audio_{uuid.uuid4().hex[:8]}.mp3")
    video_filename = tts_video_client.get_media_path(f"video_{uuid.uuid4().hex[:8]}.mp4")

    if not tts_video_client.generate_audio(script_text, audio_filename):
        raise RuntimeError("TTS audio generation failed")

    # 4. Assemble video
    tts_video_client.assemble_video(script_text, audio_filename, video_filename, bg_color=brand.color)

    # 5. Save VideoAsset record
    video_asset = VideoAsset(
        content_asset_id=asset.id,
        topic=topic,
        script_text=script_text,
        video_file_path=video_filename
    )
    db.add(video_asset)
    db.commit()
    db.refresh(video_asset)

    return video_asset
