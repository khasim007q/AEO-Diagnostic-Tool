# fuzzy.py
import re
import logging
from thefuzz import fuzz

logger = logging.getLogger(__name__)


def is_same_brand(b1: str, b2: str, threshold: int = 85) -> bool:
    """Check if two brand names refer to the same brand using fuzzy matching.

    Uses token_set_ratio for order-independent comparison and includes
    a digit check to prevent merging distinct product versions.

    Args:
        b1: First brand name.
        b2: Second brand name.
        threshold: Minimum similarity score (0-100).

    Returns:
        True if the names are considered the same brand.
    """
    if not b1 or not b2:
        return False

    b1_clean = b1.lower().strip()
    b2_clean = b2.lower().strip()

    if b1_clean == b2_clean:
        return True

    # Anti-merge: if both contain numbers, they must share at least one
    digits1 = set(re.findall(r'\d+', b1_clean))
    digits2 = set(re.findall(r'\d+', b2_clean))
    if digits1 and digits2 and not (digits1 & digits2):
        return False

    score = fuzz.token_set_ratio(b1_clean, b2_clean)
    return score >= threshold


def is_same_product(p1: str, p2: str, threshold: int = 80) -> bool:
    """Check if two product names refer to the same product.

    Uses token_sort_ratio for flexible ordering and includes
    a digit check for version/model number differentiation.

    Args:
        p1: First product name.
        p2: Second product name.
        threshold: Minimum similarity score (0-100).

    Returns:
        True if the names are considered the same product.
    """
    if not p1 or not p2:
        return False

    p1_clean = p1.lower().strip()
    p2_clean = p2.lower().strip()

    if p1_clean == p2_clean:
        return True

    # Anti-merge: different version/model numbers should not match
    digits1 = set(re.findall(r'\d+', p1_clean))
    digits2 = set(re.findall(r'\d+', p2_clean))
    if digits1 and digits2 and not (digits1 & digits2):
        return False

    score = fuzz.token_sort_ratio(p1_clean, p2_clean)
    return score >= threshold


def fuzzy_find_in_text(brand_name: str, text: str, threshold: int = 80) -> bool:
    """Check if a brand name appears (fuzzily) anywhere in a block of text.

    Uses a sliding-window approach over n-grams of the text for robust matching.

    Args:
        brand_name: The brand to look for.
        text: The text block to search in (e.g., Google snippet).
        threshold: Minimum similarity to count as a match.

    Returns:
        True if any n-gram window in the text fuzzily matches the brand.
    """
    if not brand_name or not text:
        return False

    brand_lower = brand_name.lower().strip()
    text_lower = text.lower()

    # Fast path: exact substring match
    if brand_lower in text_lower:
        return True

    # Check if most significant brand words appear in the text
    brand_words = [w for w in brand_lower.split() if len(w) > 2]
    if not brand_words:
        return False

    matches = sum(1 for w in brand_words if w in text_lower)
    if len(brand_words) > 0 and matches / len(brand_words) >= 0.6:
        return True

    # Sliding window fuzzy match
    text_words = text_lower.split()
    window_size = len(brand_lower.split())
    for i in range(len(text_words) - window_size + 1):
        window = " ".join(text_words[i:i + window_size])
        if fuzz.token_set_ratio(brand_lower, window) >= threshold:
            return True

    return False
