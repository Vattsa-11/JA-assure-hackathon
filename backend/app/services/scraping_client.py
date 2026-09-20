import logging
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

class ScrapingClient:
    def scrape_url(self, url: str) -> str | None:
        """
        Scrapes the given URL using Playwright, parses with BeautifulSoup,
        and returns clean text. Gracefully returns None on failure.
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                # Fail gracefully if it takes longer than 15s
                page.goto(url, timeout=15000, wait_until="domcontentloaded")
                html = page.content()
                browser.close()
                
                soup = BeautifulSoup(html, "html.parser")
                
                # Strip out unwanted tags
                for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    element.decompose()
                
                text = soup.get_text(separator="\n")
                
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = "\n".join(chunk for chunk in chunks if chunk)
                
                return text[:5000] # Cap length to avoid context window explosion
        except PlaywrightTimeoutError:
            logger.warning(f"Timeout while scraping {url}")
            return None
        except Exception as e:
            logger.warning(f"Failed to scrape {url}: {str(e)}")
            return None

scraping_client = ScrapingClient()
