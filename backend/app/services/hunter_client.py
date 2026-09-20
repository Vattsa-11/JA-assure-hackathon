import logging

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


class HunterClient:
    def __init__(self):
        self.base_url = "https://api.hunter.io/v2"

    def find_email_for_domain(self, domain: str) -> str | None:
        if not settings.HUNTER_API_KEY:
            logger.warning("HUNTER_API_KEY not configured. Skipping email discovery.")
            return None

        params: dict[str, str | int] = {
            "domain": domain,
            "api_key": settings.HUNTER_API_KEY,
            "limit": 1,
        }
        try:
            response = requests.get(
                f"{self.base_url}/domain-search",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            emails = data.get("data", {}).get("emails", [])
            if emails:
                return emails[0].get("value")
            return None
        except requests.RequestException as e:
            logger.warning(f"Hunter API request failed for domain {domain}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Hunter client: {str(e)}")
            return None


hunter_client = HunterClient()
