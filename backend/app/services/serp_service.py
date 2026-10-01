import logging
from typing import List, Dict, Any
from serpapi import GoogleSearch
from app.config import settings
from app.api.schemas import GoogleResult

logger = logging.getLogger(__name__)

def search_google(query: str) -> List[GoogleResult]:
    """Search Google using SerpApi."""
    if not settings.SERPAPI_KEY or settings.SERPAPI_KEY == "your_serpapi_key_here":
        logger.warning("SERPAPI_KEY not configured correctly. Skipping web search.")
        return []

    try:
        search = GoogleSearch({
            "q": query,
            "api_key": settings.SERPAPI_KEY,
            "num": 10
        })
        results = search.get_dict()
        
        if "error" in results:
            logger.error(f"SerpApi error: {results['error']}")
            return []
            
        organic_results = results.get("organic_results", [])
        parsed_results = []
        
        for res in organic_results:
            parsed_results.append(GoogleResult(
                rank=res.get("position", 0),
                title=res.get("title", ""),
                snippet=res.get("snippet", ""),
                url=res.get("link", "")
            ))
            
        return parsed_results
    except Exception as e:
        logger.error(f"Error fetching Google SERP: {str(e)}")
        return []
