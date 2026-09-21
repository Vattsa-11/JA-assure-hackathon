import asyncio
import logging
import os
from pathlib import Path

import edge_tts

logger = logging.getLogger(__name__)

# Try MoviePy v2 first, fall back gracefully
MOVIEPY_V2: bool | None
try:
    from moviepy import AudioFileClip, ColorClip, CompositeVideoClip, TextClip
    MOVIEPY_V2 = True
except ImportError:
    try:
        from moviepy.editor import AudioFileClip, ColorClip, CompositeVideoClip, TextClip
        MOVIEPY_V2 = False
    except ImportError:
        MOVIEPY_V2 = None
        logger.warning("MoviePy not available. Video assembly will be skipped.")

# Resolve the media directory relative to the project root (two levels up from backend/app/services/)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
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
        except Exception as e:  # noqa: BLE001 - fail-soft over external service I/O
            logger.error(f"Failed to generate TTS audio: {e!s}")
            return False

    def assemble_video(self, script_text: str, audio_path: str, output_video_path: str, bg_color: str = "#202020") -> bool:
        """
        Assembles an MP4 using MoviePy: loads premium animated background + sliding text chunks + TTS audio.
        Compatible with MoviePy v1 and v2.
        """
        if MOVIEPY_V2 is None:
            logger.error("MoviePy not installed. Cannot assemble video.")
            return False

        try:
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            bg_path = str(MEDIA_DIR / "bg.jpg")

            if MOVIEPY_V2:
                from moviepy.video.VideoClip import ImageClip
                if os.path.exists(bg_path):
                    bg_clip = ImageClip(bg_path).with_duration(duration)
                else:
                    bg_clip = ColorClip(size=(1080, 1920), color=(32, 32, 32)).with_duration(duration)
            else:
                from moviepy.editor import ImageClip
                if os.path.exists(bg_path):
                    bg_clip = ImageClip(bg_path).set_duration(duration)
                else:
                    bg_clip = ColorClip(size=(1080, 1920), color=(32, 32, 32)).set_duration(duration)

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
                    # Dynamic slide-up animation: Starts slightly lower, slides to center
                    def pos_func(t):
                        # Slides from y=1200 up to y=900 (center-ish) over the first 0.5s
                        y_pos = max(900, int(1200 - (600 * t)))
                        return ("center", y_pos)

                    if MOVIEPY_V2:
                        txt_clip = (
                            TextClip(
                                text=chunk,
                                font_size=80,
                                color="white",
                                size=(900, None),
                                method="caption"
                            )
                            .with_position(pos_func)
                            .with_start(current_time)
                            .with_duration(chunk_duration)
                        )
                    else:
                        txt_clip = (
                            TextClip(
                                chunk,
                                fontsize=80,
                                color="white",
                                size=(900, None),
                                method="caption"
                            )
                            .set_position(pos_func)
                            .set_start(current_time)
                            .set_duration(chunk_duration)
                        )
                    clips.append(txt_clip)
                except Exception as e:  # noqa: BLE001 - fail-soft over external service I/O
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
        except Exception as e:  # noqa: BLE001 - fail-soft over external service I/O
            logger.error(f"Failed to assemble video: {e!s}")
            return False

    @staticmethod
    def get_media_path(filename: str) -> str:
        """Returns an absolute path inside the project media/ directory."""
        return str(MEDIA_DIR / filename)

tts_video_client = TTSVideoClient()
