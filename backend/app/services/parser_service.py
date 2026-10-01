# parser_service.py
import json
import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple

logger = logging.getLogger(__name__)

BRAND_CHARS = r"[A-Za-z0-9 \t\'\-\&\.\%\+\#\(\)]"


@dataclass
class ParsedRecommendation:
    rank: int
    brand: str
    product: str


@dataclass
class ParseResult:
    status: str  # "valid" | "partial" | "invalid" | "low_confidence"
    recommendations: List[ParsedRecommendation] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def is_usable(self) -> bool:
        """A response is usable if it has at least one valid recommendation."""
        return len(self.recommendations) > 0 and self.status in ("valid", "partial", "low_confidence")


def parse_llm_response_detailed(raw_text: Optional[str]) -> ParseResult:
    """Parse and strictly validate an LLM response into structured recommendations.

    Rejects:
    - rank 0 or rank 6+
    - duplicate ranks
    - missing ranks
    - malformed objects
    - empty brand or empty product strings
    Does NOT silently repair invalid ranks into guessed sequential numbers.

    Returns:
        ParseResult with status, recommendations, and diagnostic errors.
    """
    if not raw_text or not isinstance(raw_text, str):
        return ParseResult(status="invalid", errors=["Empty or non-string response"])

    trimmed = raw_text.strip()
    if trimmed.startswith("ERROR:") or trimmed.startswith("API ERROR"):
        return ParseResult(status="invalid", errors=[trimmed])

    # Strip markdown code fences if present
    cleaned = trimmed
    if cleaned.startswith("```"):
        first_newline = cleaned.find("\n")
        if first_newline != -1:
            cleaned = cleaned[first_newline + 1:]
        else:
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    # Attempt JSON parsing
    parsed_json, json_err = _extract_json_object_or_array(cleaned)
    if parsed_json is not None:
        return _validate_recommendations_json(parsed_json)

    # Fallback to regex extraction as low-confidence recovery
    regex_recs, regex_errs = _extract_regex_low_confidence(cleaned)
    if regex_recs:
        return ParseResult(
            status="low_confidence",
            recommendations=regex_recs,
            errors=["JSON parsing failed; extracted using low-confidence regex fallback"] + regex_errs,
        )

    return ParseResult(status="invalid", errors=["Failed to parse JSON and regex fallback found no items", json_err or "Unknown error"])


def parse_llm_response(raw_text: Optional[str]) -> List[Dict[str, Any]]:
    """Legacy helper returning a list of dicts for backward compatibility with tests/services.

    Returns:
        List of dicts with 'rank', 'brand', and 'product' keys.
    """
    result = parse_llm_response_detailed(raw_text)
    return [
        {"rank": r.rank, "brand": r.brand, "product": r.product}
        for r in result.recommendations
    ]


def _extract_json_object_or_array(text: str) -> Tuple[Optional[Any], Optional[str]]:
    """Try to extract JSON object (wrapper with 'recommendations') or array."""
    # Try direct parse
    try:
        data = json.loads(text)
        return data, None
    except json.JSONDecodeError:
        pass

    # Look for object wrapper {"recommendations": [...]}
    obj_match = re.search(r'\{\s*"recommendations"\s*:\s*\[.*?\]\s*\}', text, re.DOTALL)
    if obj_match:
        try:
            return json.loads(obj_match.group(0)), None
        except json.JSONDecodeError:
            pass

    # Look for standalone JSON array [...]
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        snippet = text[start:end + 1]
        try:
            return json.loads(snippet), None
        except json.JSONDecodeError as e:
            return None, f"JSON array decode error: {e}"

    return None, "No valid JSON structure found"


def _validate_recommendations_json(data: Any) -> ParseResult:
    """Strictly validate parsed JSON data against ranking and entity requirements."""
    items: List[Any] = []
    if isinstance(data, dict):
        if "recommendations" in data and isinstance(data["recommendations"], list):
            items = data["recommendations"]
        else:
            return ParseResult(status="invalid", errors=["JSON object missing 'recommendations' list"])
    elif isinstance(data, list):
        items = data
    else:
        return ParseResult(status="invalid", errors=["JSON root is neither list nor object"])

    if not items:
        return ParseResult(status="invalid", errors=["Empty recommendations list"])

    errors: List[str] = []
    valid_recs: List[ParsedRecommendation] = []
    seen_ranks: Set[int] = set()
    has_duplicate_rank = False
    has_invalid_rank = False
    has_malformed_item = False

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"Item #{idx + 1} is not an object")
            has_malformed_item = True
            continue

        raw_rank = item.get("rank")
        raw_brand = item.get("brand")
        raw_product = item.get("product")

        # Validate brand non-empty string
        if not isinstance(raw_brand, str) or not raw_brand.strip():
            errors.append(f"Item #{idx + 1} has empty or non-string brand")
            has_malformed_item = True
            continue
        brand = raw_brand.strip()

        # Validate product non-empty string
        if not isinstance(raw_product, str) or not raw_product.strip():
            errors.append(f"Item #{idx + 1} has empty or non-string product")
            has_malformed_item = True
            continue
        product = raw_product.strip()

        # Validate rank is integer and strictly 1..5
        if raw_rank is None or not isinstance(raw_rank, int) or isinstance(raw_rank, bool):
            errors.append(f"Item #{idx + 1} ({brand}) has non-integer rank: {raw_rank}")
            has_invalid_rank = True
            continue

        if raw_rank < 1 or raw_rank > 5:
            errors.append(f"Item #{idx + 1} ({brand}) has out-of-bounds rank {raw_rank} (must be 1..5)")
            has_invalid_rank = True
            continue

        if raw_rank in seen_ranks:
            errors.append(f"Duplicate rank {raw_rank} for brand '{brand}'")
            has_duplicate_rank = True
            continue

        seen_ranks.add(raw_rank)
        valid_recs.append(ParsedRecommendation(rank=raw_rank, brand=brand, product=product))

    # Check completeness
    expected_ranks = {1, 2, 3, 4, 5}
    missing_ranks = expected_ranks - seen_ranks

    # Sort by rank ascending
    valid_recs.sort(key=lambda r: r.rank)

    if has_duplicate_rank or has_invalid_rank or has_malformed_item or missing_ranks:
        if valid_recs and not has_duplicate_rank and not has_invalid_rank and not has_malformed_item:
            # Missing ranks only (partial response)
            errors.append(f"Missing ranks: {sorted(list(missing_ranks))}")
            return ParseResult(status="partial", recommendations=valid_recs, errors=errors)
        else:
            return ParseResult(status="invalid", recommendations=valid_recs, errors=errors)

    if len(valid_recs) == 5:
        return ParseResult(status="valid", recommendations=valid_recs, errors=errors)

    return ParseResult(status="invalid", recommendations=valid_recs, errors=errors)


def _extract_regex_low_confidence(text: str) -> Tuple[List[ParsedRecommendation], List[str]]:
    """Extract recommendations from raw text using regex patterns as a low-confidence fallback."""
    results: List[ParsedRecommendation] = []
    errors: List[str] = []
    seen_ranks: Set[int] = set()

    # Pattern: "1. Brand Product" or "1) Brand Product"
    pattern = re.findall(
        r'^\s*(\d+)[.)]\s*\*{0,2}\s*([A-Za-z0-9]' + BRAND_CHARS + r'{2,60})',
        text,
        re.MULTILINE,
    )

    for rank_str, raw_name in pattern:
        try:
            rank = int(rank_str)
        except ValueError:
            continue

        if rank < 1 or rank > 5:
            errors.append(f"Regex match ignored out-of-bounds rank {rank}")
            continue

        if rank in seen_ranks:
            errors.append(f"Regex match duplicate rank {rank}")
            continue

        cleaned = _clean_brand_name(raw_name)
        if len(cleaned) < 2:
            continue

        brand = _extract_brand_from_product(cleaned)
        seen_ranks.add(rank)
        results.append(ParsedRecommendation(rank=rank, brand=brand, product=cleaned))

    results.sort(key=lambda r: r.rank)
    return results, errors


def _extract_brand_from_product(full_name: str) -> str:
    """Heuristic helper to extract company name from product string."""
    if not full_name:
        return ""

    words = full_name.strip().split()
    if len(words) <= 2:
        return full_name.strip()

    product_indicators = {
        "gold", "standard", "pro", "max", "ultra", "plus", "edge",
        "impact", "nitro", "iso", "100%", "whey", "protein", "tech",
        "series", "edition", "model", "version", "lite", "air",
        "syntha", "syntha-6", "running", "shoes", "shoe", "headphone", "headphones",
        "iphone", "ipad", "macbook", "galaxy", "pixel", "thinkpad", "surface",
        "playstation", "xbox", "bravia", "eos", "lumix"
    }

    if len(words) >= 3 and words[1].lower() in product_indicators:
        return words[0]

    if len(words) >= 3 and words[2].lower() in product_indicators:
        return " ".join(words[:2])

    return " ".join(words[:2])


def _clean_brand_name(raw: str) -> str:
    """Clean raw regex string."""
    cleaned = raw.strip().strip("*_#:-")
    # Split on description separators
    cleaned = re.split(r'\s+-\s+|\s*:\s+', cleaned, maxsplit=1)[0].strip()
    return cleaned
