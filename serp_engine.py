# serp_engine.py
from serpapi import GoogleSearch
import os

SERPAPI_KEY = os.getenv("SERPAPI_KEY")


def get_google_results(query):
    """Search Google via SerpApi and return top 10 organic results."""
    params = {
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": 10,
        "hl": "en",
        "gl": "us"
    }
    search = GoogleSearch(params)
    results = search.get_dict()

    organic = results.get("organic_results", [])

    google_brands = []
    for i, result in enumerate(organic[:10], 1):
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        link = result.get("link", "")
        google_brands.append({
            "rank": i,
            "title": title,
            "snippet": snippet,
            "url": link
        })

    return google_brands
