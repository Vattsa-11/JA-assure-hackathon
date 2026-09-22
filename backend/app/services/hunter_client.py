import logging
import re

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

# Generic role addresses tried in order when guessing from a domain.
_ROLE_PREFIXES = ["info", "contact", "hello", "sales", "enquiries", "admin"]


class HunterClient:
    def __init__(self):
        self.base_url = "https://api.hunter.io/v2"

    def find_email_for_domain(self, domain: str) -> str | None:
        """Best-effort email discovery for a website domain.

        Chain (stops at first hit):
          1. Hunter.io domain-search (if HUNTER_API_KEY configured)
          2. mailto: links on the site (scraped with Playwright)
          3. Pattern guess (info@domain, contact@domain, ...) verified by MX lookup
        Returns None when everything fails — callers treat leads as
        'no email found' and the UI shows a plain note instead of a send button.
        """
        if not domain:
            return None

        # 1. Hunter (only when an API key exists)
        api_key = settings.HUNTER_API_KEY
        if api_key:
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
            except requests.RequestException as e:
                logger.warning(f"Hunter API request failed for domain {domain}: {e!s}")
            except Exception as e:  # noqa: BLE001 - fail-soft over external service I/O
                logger.error(f"Unexpected error in Hunter client: {e!s}")

        # 2. mailto: links on the site itself
        email = self._email_from_site(domain)
        if email:
            return email

        # 3. Pattern guess, verified with an MX record so we don't invent dead addresses
        return self._guess_role_email(domain)

    def _email_from_site(self, domain: str) -> str | None:
        """Scrape the homepage for mailto: links and plain email addresses."""
        try:
            from bs4 import BeautifulSoup
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(f"https://{domain}", timeout=15000, wait_until="domcontentloaded")
                html = page.content()
                browser.close()

            soup = BeautifulSoup(html, "html.parser")
            candidates: list[str] = []

            for a in soup.find_all("a", href=True):
                href = a["href"].strip().lower()
                if href.startswith("mailto:"):
                    addr = href[len("mailto:"):].split("?")[0].strip()
                    if self._valid_shape(addr):
                        candidates.append(addr)

            if not candidates:
                text = soup.get_text(" ", strip=True)
                for m in re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", text):
                    if self._valid_shape(m):
                        candidates.append(m)

            if candidates:
                return candidates[0]
        except Exception as e:  # noqa: BLE001 - fail-soft over external service I/O
            logger.warning(f"mailto scrape failed for {domain}: {e!s}")
        return None

    def _guess_role_email(self, domain: str) -> str | None:
        """Guess info@/contact@/... and keep it only if the domain accepts mail (MX)."""
        if not self._has_mx(domain):
            return None
        for prefix in _ROLE_PREFIXES:
            candidate = f"{prefix}@{domain}"
            if self._valid_shape(candidate):
                logger.info(f"Guessed contact email {candidate} for {domain} (MX verified)")
                return candidate
        return None

    @staticmethod
    def _valid_shape(email: str) -> bool:
        """Basic shape check; rejects image filenames and junk that regex scrape picks up."""
        if not re.match(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$", email):
            return False
        bad_ext = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")
        return not email.lower().endswith(bad_ext)

    @staticmethod
    def _has_mx(domain: str) -> bool:
        try:
            import dns.resolver  # type: ignore[import-untyped]
            return bool(dns.resolver.resolve(domain, "MX", lifetime=5))
        except Exception:  # noqa: BLE001 - no dnspython / no MX / timeout -> don't guess
            return False


hunter_client = HunterClient()
