# entity_resolution.py
import re
from typing import List, Optional, Tuple, Dict
from thefuzz import fuzz

# Common legal and corporate entity suffixes to normalize away
LEGAL_SUFFIXES = [
    r'\binc\.?\b',
    r'\bincorporated\b',
    r'\bcorp\.?\b',
    r'\bcorporation\b',
    r'\bllc\b',
    r'\bltd\.?\b',
    r'\blimited\b',
    r'\bco\.?\b',
    r'\bcompany\b',
    r'\bgmbh\b',
    r'\bpvt\.?\b',
    r'\bplc\b',
]

# Known brand aliases for high-confidence canonical resolution
KNOWN_ALIASES: Dict[str, str] = {
    "on": "optimum nutrition",
    "optimum": "optimum nutrition",
    "apple computer": "apple",
    "sony electronics": "sony",
    "nike athletic": "nike",
    "microsoft corp": "microsoft",
    "msft": "microsoft",
    "google llc": "google",
    "alphabet": "google",
    "meta platforms": "meta",
    "facebook": "meta",
    "aws": "amazon",
    "amazon web services": "amazon",
    "nature made vitamins": "nature made",
    "dymatize nutrition": "dymatize",
    "myprotein uk": "myprotein",
    "bsn supplements": "bsn",
    "muscletech research": "muscletech",
}


def normalize_brand_name(name: str) -> str:
    """Normalize a brand name for consistent entity resolution.

    Strips common corporate suffixes, punctuation, and extraneous whitespace.
    """
    if not name:
        return ""

    lowered = name.lower().strip()

    # Remove quotes, trademarks, and parenthesis content
    cleaned = re.sub(r'[\'\"®™©]', '', lowered)
    cleaned = re.sub(r'\([^)]*\)', '', cleaned)

    # Remove common corporate suffixes
    for suffix_pattern in LEGAL_SUFFIXES:
        cleaned = re.sub(suffix_pattern, '', cleaned, flags=re.IGNORECASE)

    # Replace hyphens and slashes with space, remove symbols
    cleaned = re.sub(r'[-_/&+,.]', ' ', cleaned)

    # Collapse multiple whitespaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # Check known aliases
    if cleaned in KNOWN_ALIASES:
        return KNOWN_ALIASES[cleaned]

    return cleaned


def extract_domain(url_or_domain: Optional[str]) -> Optional[str]:
    """Extract clean domain name from URL or host string."""
    if not url_or_domain:
        return None

    cleaned = url_or_domain.lower().strip()
    # Strip protocol
    cleaned = re.sub(r'^https?://', '', cleaned)
    # Strip paths, queries, ports
    cleaned = re.split(r'[/?:#]', cleaned)[0]
    # Strip www
    cleaned = re.sub(r'^www\.', '', cleaned)
    return cleaned if cleaned else None


def resolve_brand_entity(
    candidate_name: str,
    known_brands: List[Tuple[str, str, Optional[str]]],
    candidate_domain: Optional[str] = None,
) -> Optional[str]:
    """Resolve a candidate brand name against a list of known brands.

    Known brands is a list of tuples: (original_name, normalized_name, optional_domain).

    Priority order:
    1. Exact normalized match
    2. Explicit alias match
    3. Domain match
    4. Strong deterministic containment (word boundaries)
    5. High-confidence fuzzy match (threshold >= 88)
    6. Ambiguity check (reject if multiple candidates are equally close)

    Returns:
        The matching original_name, or None if no unambiguous match.
    """
    norm_candidate = normalize_brand_name(candidate_name)
    if not norm_candidate:
        return None

    norm_cand_domain = extract_domain(candidate_domain)

    # 1. Exact normalized match
    for orig_name, norm_name, _ in known_brands:
        if norm_candidate == norm_name:
            return orig_name

    # 2. Explicit alias match
    alias_candidate = KNOWN_ALIASES.get(norm_candidate, norm_candidate)
    for orig_name, norm_name, _ in known_brands:
        if alias_candidate == norm_name:
            return orig_name

    # 3. Domain match
    if norm_cand_domain:
        for orig_name, norm_name, known_domain in known_brands:
            if known_domain and norm_cand_domain == extract_domain(known_domain):
                return orig_name
            # Check if domain root matches brand
            domain_root = norm_cand_domain.split('.')[0]
            if domain_root == norm_name:
                return orig_name

    # 4. Strong deterministic containment
    # Ensure word boundaries so "Nike" matches "Nike Running", but "Son" does not match "Sony"
    containment_matches: List[str] = []
    for orig_name, norm_name, _ in known_brands:
        # Check if one is a complete whole-word component of the other
        cand_words = set(norm_candidate.split())
        brand_words = set(norm_name.split())
        if cand_words.issubset(brand_words) or brand_words.issubset(cand_words):
            containment_matches.append(orig_name)

    if len(containment_matches) == 1:
        return containment_matches[0]
    elif len(containment_matches) > 1:
        # Ambiguous containment, continue to fuzzy scoring
        pass

    # 5. Fuzzy match with ambiguity detection
    fuzzy_candidates: List[Tuple[str, int]] = []
    for orig_name, norm_name, _ in known_brands:
        # Use token_sort_ratio for robust word ordering
        score = fuzz.token_sort_ratio(norm_candidate, norm_name)
        if score >= 88:
            fuzzy_candidates.append((orig_name, score))

    if not fuzzy_candidates:
        return None

    # Sort descending by score
    fuzzy_candidates.sort(key=lambda x: x[1], reverse=True)

    # 6. Ambiguity check: if top 2 candidates are within 5 points, reject
    if len(fuzzy_candidates) > 1:
        top_score = fuzzy_candidates[0][1]
        runner_up_score = fuzzy_candidates[1][1]
        if top_score - runner_up_score < 5:
            # Ambiguous resolution, do not guess
            return None

    return fuzzy_candidates[0][0]
