import os
import sys

backend_dir = r"c:\Users\sharv\Downloads\hackthon\ja-assure-marketing-agent\backend"
sys.path.append(backend_dir)

from app.services.tts_video_client import tts_video_client


def prove_video_generation():
    print("\n--- PHASE 1: GENERATING TTS AUDIO ---")
    script_text = "Are you a small retail jeweler eager to protect your valuable inventory? Let Jade be your trusted partner for peace of mind."

    audio_filename = "test_audio.mp3"
    audio_path = tts_video_client.get_media_path(audio_filename)

    success = tts_video_client.generate_audio(script_text, audio_path)
    if success:
        print(f"Success! Audio saved to: {audio_path}")
    else:
        print("Failed to generate audio.")
        return

    print("\n--- PHASE 2: ASSEMBLING VIDEO ---")
    video_filename = "test_video.mp4"
    video_path = tts_video_client.get_media_path(video_filename)

    success = tts_video_client.assemble_video(script_text, audio_path, video_path)
    if success:
        print(f"Success! Video assembled and saved to: {video_path}")
    else:
        print("Failed to assemble video.")
        return

    print("\n--- PHASE 3: VERIFYING ASSETS ---")
    if os.path.exists(video_path) and os.path.getsize(video_path) > 10000:  # > 10KB
        print("The MP4 file exists and appears to be a valid video container.")
    else:
        print("The MP4 file does not exist or is suspiciously small.")

if __name__ == "__main__":
    prove_video_generation()
