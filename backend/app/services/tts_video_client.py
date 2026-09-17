import os
import asyncio
import logging
import edge_tts
from moviepy import TextClip, ColorClip, CompositeVideoClip, AudioFileClip

logger = logging.getLogger(__name__)

class TTSVideoClient:
    def __init__(self, media_dir: str = "media"):
        self.media_dir = media_dir
        os.makedirs(self.media_dir, exist_ok=True)

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
        Assembles a simple video using MoviePy: 
        Solid background, text overlay, and the generated TTS audio track.
        """
        try:
            # Load audio to determine duration
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration

            # Create a simple background
            bg_clip = ColorClip(size=(1080, 1920), color=(20, 20, 20)).set_duration(duration)
            
            # Simple text overlay (word wrapping is tricky with basic MoviePy TextClip, 
            # so we just show a title or a chunk of the script).
            display_text = script_text[:100] + "..." if len(script_text) > 100 else script_text
            
            # Note: MoviePy TextClip depends on ImageMagick. If it fails, fallback to no text.
            try:
                txt_clip = TextClip(display_text, fontsize=70, color='white', size=(900, None), method='caption')
                txt_clip = txt_clip.set_position('center').set_duration(duration)
                video = CompositeVideoClip([bg_clip, txt_clip])
            except Exception as e:
                logger.warning(f"TextClip failed (ImageMagick missing?): {str(e)}")
                video = bg_clip
                
            video = video.set_audio(audio_clip)
            
            # Write out
            video.write_videofile(
                output_video_path,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                preset="ultrafast",
                logger=None # Silence MoviePy output
            )
            
            audio_clip.close()
            video.close()
            return os.path.exists(output_video_path)
        except Exception as e:
            logger.error(f"Failed to assemble video: {str(e)}")
            return False

tts_video_client = TTSVideoClient()
