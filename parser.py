# parser.py
import re
from thefuzz import fuzz
import json


def parse_llm_response(raw_text, json_brands=None):
    """
    Primary entry point for brand extraction.
    Layer 1: Pre-parsed json_brands if passed in
    Layer 2: Parse JSON directly from raw_text
    Layer 3: Regex fallback
    """
    # Layer 1: Use pre-parsed JSON if caller provided it
    if json_brands and len(json_brands) >= 1:
        return json_brands[:5]

    # Layer 2: Try to extract JSON from raw_text ourselves
    json_result = _extract_from_json(raw_text)
    if json_result and len(json_result) >= 1:
        return json_result[:5]

    # Layer 3: Regex fallback
    return extract_brands(raw_text)


def _extract_from_json(text):
    """
    Attempts to parse a JSON array from raw LLM text.
    Handles: clean JSON, JSON inside markdown fences, 
             JSON buried inside prose.
    """
    if not text:
        return []

    # Strip markdown fences
    clean = re.sub(r'```json|```', '', text).strip()

    # Attempt 1: Entire text is a JSON array
    try:
        data = json.loads(clean)
        if isinstance(data, list):
            return [(item["rank"], item["brand"]) 
                    for item in data if "brand" in item]
    except (json.JSONDecodeError, KeyError):
        pass

    # Attempt 2: JSON array buried somewhere in prose
    # e.g. "Here are my picks: [{...}] Hope this helps!"
    match = re.search(r'\[\s*\{.*?\}\s*\]', clean, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            if isinstance(data, list):
                return [(item["rank"], item["brand"]) 
                        for item in data if "brand" in item]
        except (json.JSONDecodeError, KeyError):
            pass

    return []


def extract_brands(text):
    """
    Extracts brand mentions from unstructured LLM text using multiple regex patterns.
    Improved to preserve special characters (%, &, +, #, ™, ®) in brand names.

    Handles formats:
      - "1. BrandName - description"
      - "1. **BrandName** - description"
      - "### 1. BrandName"
      - "**BrandName**: description"
      - "- BrandName" / "• BrandName"

    Returns list of (rank, brand_name) tuples.
    """
    # Skip error responses
    if not text or text.startswith("ERROR:") or text.startswith("API ERROR"):
        return []

    brands = []

    # Expanded character class that preserves %, +, #, ™, ®, etc.
    # This is the key fix for brand names like "Gold Standard 100% Whey"
    # NOTE: Use [ \t] instead of \s to prevent matching across newlines
    BRAND_CHARS = r"[A-Za-z0-9 \t\'\-\&\.\%\+\#\™\®\(\)]"

    # Pattern 1: Numbered list with optional bold "1. **BrandName**" or "1. BrandName"
    pattern1 = re.findall(
        r'^\s*(\d+)[.)]\s*\*{0,2}\s*([A-Z]' + BRAND_CHARS + r'{2,60})',
        text, re.MULTILINE
    )
    for rank, brand in pattern1:
        cleaned = _clean_brand_name(brand)
        if _is_valid_brand(cleaned):
            brands.append((int(rank), cleaned))

    # Pattern 2: Bold mentions "**BrandName**" with surrounding context
    if not brands:
        bold = re.findall(
            r'\*\*([A-Z]' + BRAND_CHARS + r'{2,60})\*\*',
            text
        )
        seen = set()
        for brand in bold:
            cleaned = _clean_brand_name(brand)
            key = cleaned.lower()
            if key not in seen and _is_valid_brand(cleaned):
                seen.add(key)
                brands.append((len(seen), cleaned))
            if len(seen) >= 5:
                break

    # Pattern 3: Markdown heading format "### BrandName" or "## 1. BrandName"
    if not brands:
        headings = re.findall(
            r'^#{1,4}\s*\d*\.?\s*\*{0,2}([A-Z]' + BRAND_CHARS + r'{2,60})',
            text, re.MULTILINE
        )
        for i, brand in enumerate(headings[:5], 1):
            cleaned = _clean_brand_name(brand)
            if _is_valid_brand(cleaned):
                brands.append((i, cleaned))

    # Pattern 4: Dash/bullet list "- BrandName" or "• BrandName"
    if not brands:
        bullets = re.findall(
            r'^\s*[-•]\s+\*{0,2}([A-Z]' + BRAND_CHARS + r'{2,60})',
            text, re.MULTILINE
        )
        for i, brand in enumerate(bullets[:5], 1):
            cleaned = _clean_brand_name(brand)
            if _is_valid_brand(cleaned):
                brands.append((i, cleaned))

    return brands[:5]  # Top 5 only


def _clean_brand_name(raw):
    """
    Clean a raw brand match without destroying meaningful characters.
    Strips markdown artifacts and trailing description fragments,
    but preserves %, &, +, #, ™, ® within the brand name.
    """
    cleaned = raw.strip().rstrip('*').strip()

    # Remove trailing descriptions after common separators,
    # but only split on separator patterns that are clearly delimiters
    # (space-dash-space, colon-space, em-dash) — NOT hyphens within names
    cleaned = re.split(r'\s+[-–—]\s+|\s*:\s+', cleaned, maxsplit=1)[0].strip()

    # Remove trailing common words that are descriptions, not brand parts
    # e.g., "Optimum Nutrition Gold Standard 100% Whey is a great" -> stop at "Whey"
    desc_starters = re.compile(
        r'\s+(?:is|are|has|was|were|offers|provides|features|comes|includes|contains)\s',
        re.IGNORECASE
    )
    m = desc_starters.search(cleaned)
    if m:
        cleaned = cleaned[:m.start()].strip()

    return cleaned


def _is_valid_brand(name):
    """Check if a cleaned string looks like a plausible brand name."""
    return len(name) >= 3 and len(name) <= 80


def fuzzy_match_brand(needle, haystack, threshold=85):
    """
    Check if 'needle' fuzzy-matches 'haystack' using token-set ratio.
    Includes a digit-check to prevent merging distinct product models (e.g. iPhone 14 vs 15).
    """
    if not needle or not haystack:
        return False
        
    n_lower = needle.lower().strip()
    h_lower = haystack.lower().strip()
    
    # Anti-merge rule: If both contain digits, they must share at least one digit
    digits1 = set(re.findall(r'\d+', n_lower))
    digits2 = set(re.findall(r'\d+', h_lower))
    if digits1 and digits2 and not (digits1 & digits2):
        return False
        
    score = fuzz.token_set_ratio(n_lower, h_lower)
    return score >= threshold


def fuzzy_find_in_text(brand_name, text, threshold=80):
    """
    Check if a brand name appears (fuzzily) anywhere in a block of text.
    Uses a sliding-window approach over n-grams of the text.

    Args:
        brand_name: The brand to look for.
        text:       The text block to search in (e.g., Google snippet).
        threshold:  Minimum similarity to count as a match.

    Returns:
        True if any n-gram window in the text fuzzily matches the brand.
    """
    if not brand_name or not text:
        return False

    brand_lower = brand_name.lower().strip()
    text_lower = text.lower()

    # Quick exact substring check first (fast path)
    if brand_lower in text_lower:
        return True

    # Check individual significant words from the brand name
    brand_words = [w for w in brand_lower.split() if len(w) > 2]
    if not brand_words:
        return False

    # If most brand words appear in the text, it's a match
    matches = sum(1 for w in brand_words if w in text_lower)
    if len(brand_words) > 0 and matches / len(brand_words) >= 0.6:
        return True

    # Sliding window fuzzy match for tougher cases
    text_words = text_lower.split()
    window_size = len(brand_lower.split())
    for i in range(len(text_words) - window_size + 1):
        window = " ".join(text_words[i:i + window_size])
        if fuzz.token_set_ratio(brand_lower, window) >= threshold:
            return True

    return False


def normalize_brands(brands_list):
    """Lowercase + strip for comparison across LLMs."""
    return {b.lower().strip() for _, b in brands_list}
