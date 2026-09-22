"""Replicate image generation client.

Runs a text-to-image model on Replicate (default: Flux 1.1 Quick via
`black-forest-labs/flux-1.1-pro-ultra` — configurable via REPLICATE_IMAGE_MODEL)
and saves the result into the shared media/ directory, mirroring how
tts_video_client stores rendered videos.

Fail-soft: generate_image returns None on any failure and logs the reason.
"""

import logging
import re
import time
from pathlib import Path

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MEDIA_DIR = PROJECT_ROOT / "media"
MEDIA_DIR.mkdir(exist_ok=True)

# Default text-to-image model (Tencent HunyuanImage 2.1 — 2K resolution).
DEFAULT_IMAGE_MODEL = "tencent/hunyuan-image-2.1"
# HunyuanVideo text-to-video on Replicate (HunyuanVideo-1.5 itself is
# Hugging-Face weights only — swap the env slot when an API host exists).
DEFAULT_VIDEO_MODEL = "tencent/hunyuan-video"


class ReplicateImageClient:
    def __init__(self) -> None:
        self.api_token = settings.REPLICATE_API_TOKEN
        self.model_version = settings.REPLICATE_IMAGE_MODEL or DEFAULT_IMAGE_MODEL
        self.video_model = settings.REPLICATE_VIDEO_MODEL or DEFAULT_VIDEO_MODEL
        self.last_error: str | None = None

    def _client(self):
        """Authenticated Replicate client.

        The token comes from backend/.env via pydantic settings — the SDK does
        NOT read that file itself, so we must pass it explicitly (otherwise
        every call 401s).
        """
        import replicate

        return replicate.Client(api_token=self.api_token)

    @staticmethod
    def _image_inputs(model: str, prompt: str) -> dict:
        """Per-model input payloads — Replicate rejects inputs a model doesn't
        declare (e.g. flux's `output_format` is invalid for hunyuan-image)."""
        if model.startswith("tencent/hunyuan-image"):
            return {"prompt": prompt, "aspect_ratio": "1:1"}
        # Flux family (and sensible default for unknown models)
        return {"prompt": prompt, "aspect_ratio": "1:1", "output_format": "jpg"}

    @property
    def configured(self) -> bool:
        return bool(self.api_token)

    def _extract_bytes(self, output) -> bytes | None:
        """Normalize Replicate outputs (FileOutput / URL / list) into bytes."""
        url: str | None = None
        if isinstance(output, str):
            url = output
        elif isinstance(output, list) and output:
            first = output[0]
            url = first if isinstance(first, str) else None
            if url is None:
                output = first
        if url is None:
            read = getattr(output, "read", None)
            if callable(read):
                data = read()
                return data if isinstance(data, bytes) else None
            url = str(output) if output is not None else None
        if not url:
            return None
        if url.startswith("http"):
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            return response.content
        return None

    def generate_image(self, prompt: str, output_filename: str) -> str | None:
        """Generate an image from `prompt`, save to media/<output_filename>.

        Returns the filename on success, None on failure.
        """
        if not self.configured:
            logger.warning("Replicate not configured — set REPLICATE_API_TOKEN in backend/.env")
            return None
        if not prompt.strip():
            return None

        try:
            # Minimal input set shared by flux-1.1-pro-ultra and flux-schnell
            # (extra params like safety_tolerance are model-specific and error out).
            # Small retry loop: flaky DNS/networks (Errno 11001) are transient.
            output = None
            last_err: Exception | None = None
            client = self._client()
            inputs = self._image_inputs(self.model_version, prompt.strip())
            for attempt in range(3):
                try:
                    output = client.run(
                        self.model_version,
                        input=inputs,
                    )
                    break
                except Exception as e:  # noqa: BLE001 - retry transient network errors
                    last_err = e
                    logger.warning(f"Replicate attempt {attempt + 1}/3 failed: {e}")
                    # Auth/billing errors will never succeed on retry — stop early
                    msg = str(e)
                    if any(k in msg for k in ("401", "Unauthenticated", "402", "Insufficient credit")):
                        break
                    time.sleep(2 ** attempt)
            if output is None:
                self.last_error = str(last_err) if last_err else "no output"
                raise last_err if last_err else RuntimeError("Replicate run produced no output")
            data = self._extract_bytes(output)
            if not data:
                logger.error("Replicate returned no usable image output")
                return None
            return self._save_bytes(data, output_filename)
        except Exception as e:  # noqa: BLE001 - fail-soft over external service I/O
            logger.error(f"Replicate image generation failed: {e}")
            return None

    def generate_video(self, prompt: str, output_filename: str) -> str | None:
        """Generate a short AI video clip (default: HunyuanVideo on Replicate).

        Model is configurable via REPLICATE_VIDEO_MODEL so newer releases
        (e.g. a hosted HunyuanVideo-1.5) are a one-line .env change.
        Returns the saved filename or None on failure.
        """
        if not self.configured:
            self.last_error = "REPLICATE_API_TOKEN is not set in backend/.env"
            logger.warning(f"Replicate not configured — {self.last_error}")
            return None
        if not prompt.strip():
            return None

        try:
            output = None
            last_err: Exception | None = None
            client = self._client()
            for attempt in range(3):
                try:
                    output = client.run(
                        self.video_model,
                        input={"prompt": prompt.strip()},
                    )
                    break
                except Exception as e:  # noqa: BLE001 - retry transient network errors
                    last_err = e
                    logger.warning(f"Replicate video attempt {attempt + 1}/3 failed: {e}")
                    msg = str(e)
                    if any(k in msg for k in ("401", "Unauthenticated", "402", "Insufficient credit")):
                        break
                    time.sleep(2 ** attempt)
            if output is None:
                raise last_err if last_err else RuntimeError("Replicate run produced no output")
            data = self._extract_bytes(output)
            if not data:
                logger.error("Replicate returned no usable video output")
                return None
            return self._save_bytes(data, output_filename, video=True)
        except Exception as e:  # noqa: BLE001 - fail-soft over external service I/O
            logger.error(f"Replicate video generation failed: {e}")
            return None

    def _save_bytes(self, data: bytes, output_filename: str, video: bool = False) -> str | None:
        """Persist bytes into media/ with a light extension sanity check."""
        ext = Path(output_filename).suffix.lower()
        allowed = {".mp4", ".webm"} if video else {".jpg", ".jpeg", ".png", ".webp"}
        if ext not in allowed:
            output_filename = f"{Path(output_filename).stem}{'.mp4' if video else '.jpg'}"
        path = MEDIA_DIR / output_filename
        path.write_bytes(data)
        return output_filename


def generate_image_free(prompt: str, output_filename: str) -> str | None:
    """Free image generation via Pollinations (Flux, no API key, rate-limited).

    GET https://image.pollinations.ai/prompt/<prompt>?width=&height=&nologo=true
    Returns the saved filename or None.
    """
    if not prompt.strip():
        return None
    url = (
        "https://image.pollinations.ai/prompt/"
        + requests.utils.quote(prompt.strip()[:1800])
        + "?width=1024&height=1024&nologo=true&model=flux"
    )
    # The free endpoint throws random 500s — retry a few times.
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=150)
            response.raise_for_status()
            if "image" in (response.headers.get("content-type") or ""):
                return replicate_image_client._save_bytes(response.content, output_filename)
            logger.warning(f"Pollinations non-image response (attempt {attempt + 1}/3): {response.text[:120]}")
        except Exception as e:  # noqa: BLE001 - fail-soft over external service I/O
            logger.warning(f"Pollinations attempt {attempt + 1}/3 failed: {e}")
        time.sleep(2 * (attempt + 1))
    return None


def generate_image_with_fallback(prompt: str, output_filename: str) -> tuple[str | None, str]:
    """Provider chain based on IMAGE_PROVIDER setting (default: auto).

    auto:       Pollinations (free) -> Replicate (paid, needs credit)
    pollinations: Pollinations only
    replicate:  Replicate only
    Returns (filename | None, provider_used_or_error).
    """
    provider = (settings.IMAGE_PROVIDER or "auto").lower()
    errors: list[str] = []

    if provider in ("auto", "pollinations"):
        result = generate_image_free(prompt, output_filename)
        if result:
            return result, "pollinations"
        errors.append("pollinations failed")
        if provider == "pollinations":
            return None, "Pollinations unavailable"

    if provider in ("auto", "replicate"):
        result = replicate_image_client.generate_image(prompt, output_filename)
        if result:
            return result, "replicate"
        errors.append(replicate_image_client.last_error or "replicate failed")

    return None, "; ".join(errors) or "all providers failed"


def build_image_prompt(brief: str) -> str:
    """LLM-free deterministic prompt builder: keeps style words + cleans junk."""
    cleaned = re.sub(r"\s+", " ", brief).strip()
    return (
        f"Premium social media marketing visual for an insurance brand. "
        f"Scene: {cleaned}. "
        f"Style: modern, clean, luxury pastel palette, soft studio lighting, "
        f"photorealistic, no text, no watermark, no people faces close-up."
    )


def build_video_prompt(script_text: str) -> str:
    """Cinematic prompt for text-to-video models, derived from the narration."""
    cleaned = re.sub(r"\s+", " ", script_text).strip()[:400]
    return (
        f"Cinematic vertical social media video for an insurance brand. "
        f"Scene: {cleaned}. "
        f"Style: smooth camera motion, premium corporate look, warm lighting, "
        f"high detail, no text overlays, no watermark."
    )


replicate_image_client = ReplicateImageClient()
