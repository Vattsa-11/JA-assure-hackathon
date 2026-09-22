"""Thin Postiz Public API client (https://docs.postiz.com/public-api).

Used by the review modal to list connected social channels and publish
approved campaign content. Fail-soft: every method returns a safe fallback
on error so the publish popup never hard-crashes.
"""

import logging

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


class PostizClient:
    def __init__(self) -> None:
        self.api_key = settings.POSTIZ_API_KEY
        self.base_url = settings.POSTIZ_API_URL.rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"{self.api_key}", "Content-Type": "application/json"}

    def list_integrations(self) -> list[dict]:
        """Connected social channels: [{id, name, identifier, picture, disabled}]."""
        if not self.configured:
            return []
        try:
            response = requests.get(f"{self.base_url}/integrations", headers=self._headers(), timeout=15)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else []
        except Exception as e:  # noqa: BLE001 - fail-soft over external service I/O
            logger.warning(f"Postiz list_integrations failed: {e}")
            return []

    def create_post(
        self,
        integration_ids: list[str],
        content: str,
        image_urls: list[str] | None = None,
        publish_type: str = "now",
        date: str | None = None,
        platform: str | None = None,
    ) -> list[dict]:
        """Create/publish a post to the given integrations.

        publish_type: "now" (immediate), "schedule" (needs date), "draft".
        Returns Postiz response: [{postId, integration}] or [{error}] on failure.
        """
        if not self.configured:
            return [{"error": "Postiz is not configured — set POSTIZ_API_KEY in backend/.env"}]
        if not integration_ids:
            return [{"error": "No social channel selected"}]

        payload: dict = {
            "type": publish_type,
            "date": date or "1970-01-01T00:00:00.000Z",
            "shortLink": False,
            "tags": [],
            "posts": [
                {
                    "integration": {"id": iid},
                    "value": [{"content": content, "image": image_urls or []}],
                    "settings": {"__type": platform} if platform else {},
                }
                for iid in integration_ids
            ],
        }
        try:
            response = requests.post(
                f"{self.base_url}/posts", headers=self._headers(), json=payload, timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else [{"error": "Unexpected Postiz response"}]
        except requests.RequestException as e:
            detail = ""
            if getattr(e, "response", None) is not None and e.response is not None:
                detail = e.response.text[:300]
            logger.warning(f"Postiz create_post failed: {e} {detail}")
            return [{"error": f"Postiz API error: {e} {detail}"}]


postiz_client = PostizClient()
