import asyncio
import logging
import os
from pathlib import Path

import edge_tts

logger = logging.getLogger(__name__)

# Try MoviePy v2 first, fall back gracefully
try:
    from moviepy import AudioFileClip, ColorClip, CompositeVideoClip, TextClip

    MOVIEPY_V2 = True
except ImportError:
    try:
        from moviepy.editor import (  # type: ignore[no-redef]
            AudioFileClip,
            ColorClip,
            CompositeVideoClip,
            TextClip,
        )

        MOVIEPY_V2 = False
    except ImportError:
        MOVIEPY_V2 = False
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
        except Exception as e:  # noqa: BLE001 -- fail-soft: TTS is optional, log and report failure to caller
            logger.error(f"Failed to generate TTS audio: {e!s}")
            return False

    def assemble_video(self, script_text: str, audio_path: str, output_video_path: str, bg_color: str = "#202020") -> bool:
        """
        Assembles an MP4 using MoviePy: brand background + timed text chunks + TTS audio.
        Compatible with MoviePy v1 and v2.
        """
        if not MOVIEPY_V2:
            logger.error("MoviePy not installed. Cannot assemble video.")
            return False

        def hex_to_rgb(hex_str):
            h = hex_str.lstrip('#')
            if len(h) == 6:
                return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
            return (32, 32, 32)

        try:
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            bg_rgb = hex_to_rgb(bg_color)

            if MOVIEPY_V2:
                bg_clip = ColorClip(size=(1080, 1920), color=bg_rgb).with_duration(duration)
            else:
                bg_clip = ColorClip(size=(1080, 1920), color=bg_rgb).set_duration(duration)

            words = script_text.split()
            if not words:
                words = ["(No", "audio)"]

            chunk_size = 7
            chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
            words_per_sec = len(words) / duration if duration > 0 else 1

            clips = [bg_clip]
            current_time = 0.0

            for chunk in chunks:
                chunk_duration = len(chunk.split()) / words_per_sec
                if current_time >= duration:
                    break
                if current_time + chunk_duration > duration:
                    chunk_duration = duration - current_time

                try:
                    if MOVIEPY_V2:
                        txt_clip = (
                            TextClip(
                                text=chunk,
                                font_size=70,
                                color="white",
                                size=(980, None),
                                method="caption"
                            )
                            .with_position(("center", 1250))
                            .with_start(current_time)
                            .with_duration(chunk_duration)
                        )
                    else:
                        txt_clip = (
                            TextClip(
                                chunk,
                                fontsize=70,
                                color="white",
                                size=(980, None),
                                method="caption"
                            )
                            .set_position(("center", 1250))
                            .set_start(current_time)
                            .set_duration(chunk_duration)
                        )
                    clips.append(txt_clip)
                except Exception as e:  # noqa: BLE001 -- fail-soft: skip one bad caption chunk, keep rendering
                    logger.warning(f"TextClip failed for chunk: {e}")

                current_time += chunk_duration

            if MOVIEPY_V2:
                video = CompositeVideoClip(clips).with_audio(audio_clip)
            else:
                video = CompositeVideoClip(clips).set_audio(audio_clip)

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
        except Exception as e:  # noqa: BLE001 -- fail-soft: video assembly is optional, log and report failure to caller
            logger.error(f"Failed to assemble video: {e!s}")
            return False

    @staticmethod
    def get_media_path(filename: str) -> str:
        """Returns an absolute path inside the project media/ directory."""
        return str(MEDIA_DIR / filename)

tts_video_client = TTSVideoClient()
