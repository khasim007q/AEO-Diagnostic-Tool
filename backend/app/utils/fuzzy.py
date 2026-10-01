# fuzzy.py
import re
import logging
from typing import Optional, List, Tuple
from thefuzz import fuzz

from app.utils.entity_resolution import (
    normalize_brand_name,
    normalize_text_for_search,
    resolve_brand_entity,
    extract_domain,
    KNOWN_ALIASES,
)

logger = logging.getLogger(__name__)


def is_same_brand(b1: Optional[str], b2: Optional[str], threshold: int = 88) -> bool:
    """Check if two brand names refer to the same brand entity.

    Uses normalized entity resolution with high confidence priority:
    1. Exact normalized match
    2. Explicit alias match
    3. Strong deterministic containment
    4. Strict fuzzy match
    """
    if not b1 or not b2:
        return False

    n1 = normalize_brand_name(b1)
    n2 = normalize_brand_name(b2)

    if not n1 or not n2:
        return False

    if n1 == n2:
        return True

    # Check explicit alias dictionary
    if KNOWN_ALIASES.get(n1) == n2 or KNOWN_ALIASES.get(n2) == n1:
        return True

    # Word-boundary containment
    w1 = set(n1.split())
    w2 = set(n2.split())
    if len(w1) > 0 and len(w2) > 0:
        if w1 == w2 or (w1.issubset(w2) and len(w1) >= 2) or (w2.issubset(w1) and len(w2) >= 2):
            return True

    score = fuzz.token_sort_ratio(n1, n2)
    return score >= threshold


def is_same_product(p1: Optional[str], p2: Optional[str], threshold: int = 80) -> bool:
    """Check if two product names refer to the same product.

    Uses token_sort_ratio for flexible ordering and checks version
    numbers to prevent merging distinct product models (e.g. iPhone 14 vs 15).
    """
    if not p1 or not p2:
        return False

    p1_clean = p1.lower().strip()
    p2_clean = p2.lower().strip()

    if p1_clean == p2_clean:
        return True

    # Distinct version/model numbers should not be merged
    digits1 = set(re.findall(r'\d+', p1_clean))
    digits2 = set(re.findall(r'\d+', p2_clean))
    if digits1 and digits2 and not (digits1 & digits2):
        return False

    score = fuzz.token_sort_ratio(p1_clean, p2_clean)
    return score >= threshold


def fuzzy_find_in_text(brand_name: Optional[str], text: Optional[str], threshold: int = 85) -> bool:
    """Check if a brand name appears anywhere in a block of text.

    Evaluated independently on single text snippets (not concatenated blobs)
    with symmetric punctuation, apostrophe, and diacritic normalization.
    """
    if not brand_name or not text:
        return False

    norm_brand = normalize_brand_name(brand_name)
    if not norm_brand:
        return False

    norm_text = normalize_text_for_search(text)
    if not norm_text:
        return False

    # Word boundary regex search on symmetrically normalized text
    escaped_brand = re.escape(norm_brand)
    if re.search(r'\b' + escaped_brand + r'\b', norm_text):
        return True

    # For very short brands (< 4 chars), exact word-boundary regex match above is sufficient
    # to avoid false positives like 'Son' matching 'Sony'
    if len(norm_brand) < 4:
        return False

    brand_tokens = norm_brand.split()
    text_tokens = norm_text.split()
    window_size = len(brand_tokens)

    if window_size == 0 or len(text_tokens) < window_size:
        return False

    for i in range(len(text_tokens) - window_size + 1):
        window = " ".join(text_tokens[i:i + window_size])
        if fuzz.token_sort_ratio(norm_brand, window) >= threshold:
            return True

    return False
