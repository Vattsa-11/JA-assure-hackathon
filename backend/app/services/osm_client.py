import requests
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class OSMClient:
    def __init__(self):
        self.endpoint = "http://overpass-api.de/api/interpreter"

    def find_businesses(self, niche: str, region: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Queries OSM Overpass API for businesses in a region.
        Example niche map: 'jewellery' -> 'shop=jewelry'
        """
        # Map some common niches to OSM tags
        niche_tag = "shop" # fallback
        niche_value = "jewelry" # fallback
        
        if "jewel" in niche.lower():
            niche_value = "jewelry"
        elif "clinic" in niche.lower() or "medical" in niche.lower() or "doctor" in niche.lower():
            niche_tag = "amenity"
            niche_value = "clinic"
        elif "logistics" in niche.lower() or "transit" in niche.lower():
            niche_tag = "office"
            niche_value = "logistics"

        # Overpass QL
        query = f"""
        [out:json][timeout:25];
        area[name="{region}"]->.searchArea;
        node["{niche_tag}"="{niche_value}"]["name"](area.searchArea);
        out center {limit};
        """
        
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                headers = {"User-Agent": "JAAssureMarketingAgent/1.0"}
                response = requests.post(self.endpoint, data={"data": query}, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for el in data.get("elements", []):
                    tags = el.get("tags", {})
                    name = tags.get("name")
                    if not name:
                        continue
                        
                    results.append({
                        "name": name,
                        "website": tags.get("website", tags.get("contact:website")),
                        "phone": tags.get("phone", tags.get("contact:phone")),
                        "street": tags.get("addr:street"),
                        "city": tags.get("addr:city"),
                    })
                return results
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt * 5
                    logger.warning(f"OSM Overpass API request failed. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries}): {str(e)}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"OSM Overpass API request failed after {max_retries} attempts: {str(e)}")
                    return []
            except Exception as e:
                logger.error(f"Unexpected error in OSM client: {str(e)}")
                return []
        
        return []

osm_client = OSMClient()
