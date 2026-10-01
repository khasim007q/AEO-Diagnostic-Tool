# serp_service.py
import re
import logging
import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from serpapi import GoogleSearch
from app.config import settings
from app.utils.entity_resolution import (
    extract_domain,
    normalize_brand_name,
    normalize_text_for_search,
    is_domain_match,
    get_brand_search_variants,
    is_variant_in_text,
)

logger = logging.getLogger(__name__)

MARKET_PRESETS: Dict[str, Dict[str, str]] = {
    "US": {"gl": "us", "hl": "en", "google_domain": "google.com"},
    "UK": {"gl": "uk", "hl": "en", "google_domain": "google.co.uk"},
    "India": {"gl": "in", "hl": "en", "google_domain": "google.co.in"},
    "Canada": {"gl": "ca", "hl": "en", "google_domain": "google.ca"},
    "Australia": {"gl": "au", "hl": "en", "google_domain": "google.com.au"},
    "Germany": {"gl": "de", "hl": "de", "google_domain": "google.de"},
}


@dataclass
class GoogleCorroborationResult:
    """Individual organic Google search result evaluated independently."""
    rank: int
    title: str
    snippet: str
    url: str
    domain: str
    title_match: bool = False
    snippet_match: bool = False
    domain_match: bool = False
    normalized_brand_match: bool = False
    match_type: str = "none"  # "domain" | "title" | "snippet" | "none"
    confidence: float = 0.0


@dataclass
class GoogleCorroborationSummary:
    """Status-aware Google Search Corroboration summary."""
    status: str  # "success" | "not_configured" | "failed"
    error_message: Optional[str] = None
    total_results: int = 0
    brand_found: bool = False
    best_google_rank: Optional[int] = None
    results: List[GoogleCorroborationResult] = field(default_factory=list)


def _evaluate_single_result(
    res: Dict[str, Any],
    idx: int,
    target_brand: Optional[str],
    target_domain: Optional[str],
) -> GoogleCorroborationResult:
    """Independently evaluate a single organic search result without concatenating text.

    Applies strict domain matching, alias-aware search terms, and symmetric text normalization.
    """
    rank = res.get("position", idx + 1)
    title = res.get("title") or ""
    snippet = res.get("snippet") or ""
    url = res.get("link") or ""
    domain = extract_domain(url) or ""

    clean_target_domain = extract_domain(target_domain) if target_domain else None
    search_variants = get_brand_search_variants(target_brand) if target_brand else []

    # 1. Strict domain match check (hostname or legitimate subdomain)
    domain_match = False
    if clean_target_domain and domain:
        domain_match = is_domain_match(clean_target_domain, domain)

    # 2. Title word match with alias awareness and symmetric normalization
    title_match = False
    if search_variants and title:
        norm_title = normalize_text_for_search(title)
        for variant in search_variants:
            if is_variant_in_text(variant, title, norm_title):
                title_match = True
                break

    # 3. Snippet word match with alias awareness and symmetric normalization
    snippet_match = False
    if search_variants and snippet:
        norm_snippet = normalize_text_for_search(snippet)
        for variant in search_variants:
            if is_variant_in_text(variant, snippet, norm_snippet):
                snippet_match = True
                break

    normalized_brand_match = title_match or snippet_match

    # Determine match type and confidence hierarchy
    if domain_match:
        match_type = "domain"
        confidence = 1.0
    elif title_match:
        match_type = "title"
        confidence = 0.85
    elif snippet_match:
        match_type = "snippet"
        confidence = 0.60
    else:
        match_type = "none"
        confidence = 0.0

    return GoogleCorroborationResult(
        rank=rank,
        title=title,
        snippet=snippet,
        url=url,
        domain=domain,
        title_match=title_match,
        snippet_match=snippet_match,
        domain_match=domain_match,
        normalized_brand_match=normalized_brand_match,
        match_type=match_type,
        confidence=confidence,
    )


def _execute_serpapi_sync(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the synchronous SerpApi call in a worker thread."""
    search = GoogleSearch(params)
    return search.get_dict()


async def search_google_corroboration(
    query: str,
    target_brand: Optional[str] = None,
    website_or_domain: Optional[str] = None,
    market: Optional[str] = "US",
    location: Optional[str] = None,
    language: Optional[str] = None,
    google_domain: Optional[str] = None,
) -> GoogleCorroborationSummary:
    """Perform Google Search Corroboration asynchronously without blocking the event loop."""
    if not settings.SERPAPI_KEY or settings.SERPAPI_KEY in ("your_serpapi_key_here", ""):
        logger.info("SERPAPI_KEY not configured. Returning not_configured status.")
        return GoogleCorroborationSummary(
            status="not_configured",
            error_message="SERPAPI_KEY is not configured on the server",
        )

    # Resolve localization params from preset or explicit inputs
    preset = MARKET_PRESETS.get(market or "US", MARKET_PRESETS["US"])
    gl = preset["gl"]
    hl = language or preset["hl"]
    g_domain = google_domain or preset["google_domain"]

    params: Dict[str, Any] = {
        "q": query,
        "api_key": settings.SERPAPI_KEY,
        "num": 10,
        "gl": gl,
        "hl": hl,
        "google_domain": g_domain,
    }
    if location:
        params["location"] = location

    try:
        # Run blocking network call in background thread via asyncio.to_thread
        results = await asyncio.to_thread(_execute_serpapi_sync, params)

        if "error" in results:
            err_msg = str(results["error"])
            logger.error("SerpApi returned error: %s", err_msg)
            return GoogleCorroborationSummary(
                status="failed",
                error_message=f"SerpApi error: {err_msg}",
            )

        organic_results = results.get("organic_results", [])
        evaluated_results: List[GoogleCorroborationResult] = []

        brand_found = False
        best_rank: Optional[int] = None

        for idx, res in enumerate(organic_results):
            eval_res = _evaluate_single_result(res, idx, target_brand, website_or_domain)
            evaluated_results.append(eval_res)

            if eval_res.match_type != "none":
                brand_found = True
                if best_rank is None or eval_res.rank < best_rank:
                    best_rank = eval_res.rank

        return GoogleCorroborationSummary(
            status="success",
            total_results=len(evaluated_results),
            brand_found=brand_found,
            best_google_rank=best_rank,
            results=evaluated_results,
        )

    except Exception as exc:
        logger.error("Exception occurred during Google search: %s", exc, exc_info=True)
        return GoogleCorroborationSummary(
            status="failed",
            error_message=f"Network or service error during search: {str(exc)}",
        )
