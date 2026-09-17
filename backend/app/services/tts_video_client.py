import os
import asyncio
import logging
import edge_tts
from pathlib import Path

logger = logging.getLogger(__name__)

# Try MoviePy v2 first, fall back gracefully
try:
    from moviepy import ColorClip, CompositeVideoClip, AudioFileClip, TextClip
    MOVIEPY_V2 = True
except ImportError:
    try:
        from moviepy.editor import ColorClip, CompositeVideoClip, AudioFileClip, TextClip
        MOVIEPY_V2 = False
    except ImportError:
        MOVIEPY_V2 = None
        logger.warning("MoviePy not available. Video assembly will be skipped.")

# Resolve the media directory relative to the project root (two levels up from backend/app/services/)
PROJECT_ROOT = Path(__file__).resolve().parents[4]
MEDIA_DIR = PROJECT_ROOT / "media"
MEDIA_DIR.mkdir(exist_ok=True)

class TTSVideoClient:
    async def _generate_audio_async(self, text: str, output_path: str, voice: str = "en-US-ChristopherNeural"):
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

    def generate_audio(self, text: str, output_path: str, voice: str = "en-US-ChristopherNeural") -> bool:
        """Synchronous wrapper for edge-tts."""
        try:
            asyncio.run(self._generate_audio_async(text, output_path, voice))
            return os.path.exists(output_path)
        except Exception as e:
            logger.error(f"Failed to generate TTS audio: {str(e)}")
            return False

    def assemble_video(self, script_text: str, audio_path: str, output_video_path: str) -> bool:
        """
        Assembles an MP4 using MoviePy: dark background + text overlay + TTS audio.
        Compatible with MoviePy v1 and v2.
        """
        if MOVIEPY_V2 is None:
            logger.error("MoviePy not installed. Cannot assemble video.")
            return False

        try:
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration

            display_text = (script_text[:120] + "...") if len(script_text) > 120 else script_text

            if MOVIEPY_V2:
                # MoviePy v2 API
                bg_clip = ColorClip(size=(1080, 1920), color=(20, 20, 20)).with_duration(duration)
                try:
                    txt_clip = (
                        TextClip(
                            text=display_text,
                            font_size=60,
                            color="white",
                            size=(900, None),
                            method="caption",
                        )
                        .with_position("center")
                        .with_duration(duration)
                    )
                    video = CompositeVideoClip([bg_clip, txt_clip])
                except Exception as e:
                    logger.warning(f"TextClip failed (font/ImageMagick missing?): {e}. Using plain background.")
                    video = bg_clip
                video = video.with_audio(audio_clip)
            else:
                # MoviePy v1 API
                bg_clip = ColorClip(size=(1080, 1920), color=(20, 20, 20)).set_duration(duration)
                try:
                    txt_clip = (
                        TextClip(display_text, fontsize=60, color="white", size=(900, None), method="caption")
                        .set_position("center")
                        .set_duration(duration)
                    )
                    video = CompositeVideoClip([bg_clip, txt_clip])
                except Exception as e:
                    logger.warning(f"TextClip failed: {e}. Using plain background.")
                    video = bg_clip
                video = video.set_audio(audio_clip)

            video.write_videofile(
                output_video_path,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                preset="ultrafast",
                logger=None
            )

            audio_clip.close()
            video.close()
            return os.path.exists(output_video_path)
        except Exception as e:
            logger.error(f"Failed to assemble video: {str(e)}")
            return False

    @staticmethod
    def get_media_path(filename: str) -> str:
        """Returns an absolute path inside the project media/ directory."""
        return str(MEDIA_DIR / filename)

tts_video_client = TTSVideoClient()
