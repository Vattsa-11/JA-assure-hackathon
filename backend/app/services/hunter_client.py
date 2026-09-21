import logging

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

class HunterClient:
    def __init__(self):
        self.base_url = "https://api.hunter.io/v2"

    def find_email_for_domain(self, domain: str) -> str | None:
        api_key = settings.HUNTER_API_KEY
        if not api_key:
            logger.warning("HUNTER_API_KEY not configured. Skipping email discovery.")
            return None

        try:
            params: dict[str, str | int] = {
                "domain": domain,
                "api_key": api_key,
                "limit": 1,
            }
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
            logger.warning(f"Hunter API request failed for domain {domain}: {e!s}")
            return None
        except Exception as e:  # noqa: BLE001 - fail-soft over external service I/O
            logger.error(f"Unexpected error in Hunter client: {e!s}")
            return None

hunter_client = HunterClient()
