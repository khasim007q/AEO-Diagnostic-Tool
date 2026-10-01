# parser_service.py
import json
import re
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Characters preserved in brand names during regex extraction
BRAND_CHARS = r"[A-Za-z0-9 \t\'\-\&\.\%\+\#\(\)]"


def parse_llm_response(raw_text: str) -> List[Dict[str, Any]]:
    """Parse an LLM response into a list of brand/product dicts.

    Tries multiple strategies in order:
    1. Direct JSON array parsing
    2. JSON extraction from markdown/prose
    3. Truncated JSON recovery
    4. Regex-based key extraction from malformed JSON
    5. Numbered/bulleted list regex fallback

    Args:
        raw_text: The raw text from an LLM response.

    Returns:
        List of dicts with keys: brand, product, rank.
    """
    if not raw_text or raw_text.startswith("ERROR:") or raw_text.startswith("API ERROR"):
        return []

    # Try JSON-based parsing first
    json_result = _parse_json(raw_text)
    if json_result:
        return json_result[:5]

    # Fall back to regex extraction from structured text
    regex_result = _extract_brands_regex(raw_text)
    if regex_result:
        return regex_result[:5]

    return []


def _parse_json(text: str) -> Optional[List[Dict[str, Any]]]:
    """Attempt to parse JSON from LLM text using multiple strategies.

    Args:
        text: Raw LLM response text.

    Returns:
        List of parsed brand dicts, or None on failure.
    """
    cleaned = text.strip()

    # Strip markdown code fences
    if cleaned.startswith("```"):
        first_newline = cleaned.find("\n")
        if first_newline != -1:
            cleaned = cleaned[first_newline + 1:]
        else:
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    start = cleaned.find("[")
    end = cleaned.rfind("]")

    # Strategy 1: Standard JSON array extraction
    if start != -1 and end != -1 and end > start:
        json_str = cleaned[start:end + 1]
        try:
            data = json.loads(json_str)
            if isinstance(data, list):
                result = _extract_from_json_list(data)
                if result:
                    return result
        except json.JSONDecodeError:
            pass

    # Strategy 2: Truncated JSON recovery (common with Gemini)
    if start != -1:
        partial = cleaned[start:]
        partial = partial.rstrip().rstrip(",")
        if not partial.endswith("]"):
            # Close any unclosed object
            if partial.count("{") > partial.count("}"):
                partial = partial.rstrip().rstrip(",")
                if not partial.endswith("}"):
                    partial += "}"
            partial += "]"
        try:
            data = json.loads(partial)
            if isinstance(data, list):
                result = _extract_from_json_list(data)
                if result:
                    return result
        except json.JSONDecodeError:
            pass

    # Strategy 3: Extract "brand" and "product" keys via regex from malformed JSON
    brands = _recover_from_json_text(cleaned)
    if brands:
        return brands

    return None


def _extract_from_json_list(data: list) -> Optional[List[Dict[str, Any]]]:
    """Extract brand/product dicts from a parsed JSON list.

    Args:
        data: Parsed JSON list.

    Returns:
        List of normalized dicts, or None if nothing valid found.
    """
    results = []
    for item in data:
        if not isinstance(item, dict):
            continue

        rank_raw = item.get("rank")
        brand_raw = item.get("brand", "")
        product_raw = item.get("product", "")

        # If only "brand" key exists (old format), use it as product too
        if not product_raw and brand_raw:
            product_raw = brand_raw

        if not isinstance(brand_raw, str):
            brand_raw = str(brand_raw) if brand_raw else ""
        if not isinstance(product_raw, str):
            product_raw = str(product_raw) if product_raw else ""

        brand = brand_raw.strip()
        product = product_raw.strip()

        if not brand and not product:
            continue

        # If brand is missing but product exists, try to extract brand
        if not brand and product:
            brand = _extract_brand_from_product(product)

        try:
            rank = int(rank_raw) if rank_raw is not None else len(results) + 1
        except (ValueError, TypeError):
            rank = len(results) + 1

        if 1 <= rank <= 10:
            results.append({
                "brand": brand,
                "product": product,
                "rank": rank,
            })

    return results if results else None


def _recover_from_json_text(text: str) -> Optional[List[Dict[str, Any]]]:
    """Last-resort: extract brand/product from malformed JSON using regex.

    Args:
        text: Text that might contain partial JSON objects.

    Returns:
        List of extracted dicts, or None.
    """
    brand_matches = re.findall(r'"brand"\s*:\s*"([^"]+)"', text)
    product_matches = re.findall(r'"product"\s*:\s*"([^"]+)"', text)
    rank_matches = re.findall(r'"rank"\s*:\s*(\d+)', text)

    if not brand_matches and not product_matches:
        return None

    results = []
    max_len = max(len(brand_matches), len(product_matches))

    for i in range(max_len):
        brand = brand_matches[i].strip() if i < len(brand_matches) else ""
        product = product_matches[i].strip() if i < len(product_matches) else ""
        rank = int(rank_matches[i]) if i < len(rank_matches) else i + 1

        if not brand and product:
            brand = _extract_brand_from_product(product)
        if not product and brand:
            product = brand

        if (brand or product) and 1 <= rank <= 10:
            results.append({"brand": brand, "product": product, "rank": rank})

    return results if results else None


def _extract_brands_regex(text: str) -> List[Dict[str, Any]]:
    """Extract brands from unstructured text using regex patterns.

    Handles formats like:
    - "1. BrandName ProductName - description"
    - "1. **BrandName ProductName** - description"
    - "### 1. BrandName"
    - "- BrandName ProductName"

    Args:
        text: Unstructured LLM response text.

    Returns:
        List of brand/product dicts.
    """
    results: List[Dict[str, Any]] = []

    # Pattern 1: Numbered list "1. Brand Product" or "1. **Brand Product**"
    pattern1 = re.findall(
        r'^\s*(\d+)[.)]\s*\*{0,2}\s*([A-Za-z0-9]' + BRAND_CHARS + r'{2,60})',
        text,
        re.MULTILINE,
    )
    for rank_str, raw_name in pattern1:
        cleaned = _clean_brand_name(raw_name)
        if _is_valid_brand(cleaned):
            brand = _extract_brand_from_product(cleaned)
            results.append({
                "brand": brand,
                "product": cleaned,
                "rank": int(rank_str),
            })

    # Pattern 2: Bold mentions **BrandName**
    if not results:
        bold = re.findall(
            r'\*\*([A-Za-z0-9]' + BRAND_CHARS + r'{2,60})\*\*',
            text,
        )
        seen: set = set()
        for raw_name in bold:
            cleaned = _clean_brand_name(raw_name)
            key = cleaned.lower()
            if key not in seen and _is_valid_brand(cleaned):
                seen.add(key)
                brand = _extract_brand_from_product(cleaned)
                results.append({
                    "brand": brand,
                    "product": cleaned,
                    "rank": len(seen),
                })
            if len(seen) >= 5:
                break

    # Pattern 3: Markdown headings "### BrandName"
    if not results:
        headings = re.findall(
            r'^#{1,4}\s*\d*\.?\s*\*{0,2}([A-Za-z0-9]' + BRAND_CHARS + r'{2,60})',
            text,
            re.MULTILINE,
        )
        for i, raw_name in enumerate(headings[:5], 1):
            cleaned = _clean_brand_name(raw_name)
            if _is_valid_brand(cleaned):
                brand = _extract_brand_from_product(cleaned)
                results.append({"brand": brand, "product": cleaned, "rank": i})

    # Pattern 4: Bullet list "- BrandName"
    if not results:
        bullets = re.findall(
            r'^\s*[-\u2022]\s+\*{0,2}([A-Za-z0-9]' + BRAND_CHARS + r'{2,60})',
            text,
            re.MULTILINE,
        )
        for i, raw_name in enumerate(bullets[:5], 1):
            cleaned = _clean_brand_name(raw_name)
            if _is_valid_brand(cleaned):
                brand = _extract_brand_from_product(cleaned)
                results.append({"brand": brand, "product": cleaned, "rank": i})

    return results


def _extract_brand_from_product(full_name: str) -> str:
    """Heuristic: extract the brand/company name from a full product name.

    Splits on common patterns. For "Optimum Nutrition Gold Standard 100% Whey",
    returns "Optimum Nutrition". For single-word names like "Apple", returns "Apple".

    Args:
        full_name: The full product/brand name string.

    Returns:
        The extracted brand name.
    """
    if not full_name:
        return ""

    words = full_name.strip().split()
    if len(words) <= 2:
        return full_name.strip()

    # Common brand patterns: first 1-3 words are typically the brand
    # Check if the third word looks like a product descriptor
    product_indicators = {
        "gold", "standard", "pro", "max", "ultra", "plus", "edge",
        "impact", "nitro", "iso", "100%", "whey", "protein", "tech",
        "series", "edition", "model", "version", "lite", "air",
        "syntha", "syntha-6",
    }

    # If word 2 (0-indexed) is a product indicator, brand is first 1 word
    if len(words) >= 3 and words[1].lower() in product_indicators:
        return words[0]

    # If word 3 (0-indexed) is a product indicator, brand is first 2 words
    if len(words) >= 3 and words[2].lower() in product_indicators:
        return " ".join(words[:2])

    # Default: first two words are the brand
    return " ".join(words[:2])


def _clean_brand_name(raw: str) -> str:
    """Clean a raw brand match without destroying meaningful characters.

    Args:
        raw: Raw regex match string.

    Returns:
        Cleaned brand name.
    """
    cleaned = raw.strip().rstrip("*").strip()

    # Remove trailing descriptions after delimiters
    cleaned = re.split(r'\s+[-\u2013\u2014]\s+|\s*:\s+', cleaned, maxsplit=1)[0].strip()

    # Remove trailing description words
    desc_starters = re.compile(
        r'\s+(?:is|are|has|was|were|offers|provides|features|comes|includes|contains)\s',
        re.IGNORECASE,
    )
    m = desc_starters.search(cleaned)
    if m:
        cleaned = cleaned[:m.start()].strip()

    return cleaned


def _is_valid_brand(name: str) -> bool:
    """Check if a cleaned string looks like a plausible brand name.

    Args:
        name: Cleaned brand name string.

    Returns:
        True if the name is between 3 and 80 characters.
    """
    return 3 <= len(name) <= 80
