# entity_resolution.py
import re
import unicodedata
from typing import List, Optional, Tuple, Dict, Set
from thefuzz import fuzz

# Common legal and corporate entity suffixes to normalize away only when trailing
TRAILING_LEGAL_SUFFIX_PATTERN = (
    r'(?:,\s*|\s+)(?:inc|incorporated|corp|corporation|llc|ltd|limited|gmbh|pvt|plc)\.?$'
)
TRAILING_CO_PATTERN = r'(?:,\s*|\s+)(?:co|company)\.?$'

# Explicit canonical brand aliases
# Conservative list: only defensible identical consumer-facing brand identities (acronyms / abbreviations)
# Excludes legal entities, divisions, and historical names (e.g. Sony Electronics, Apple Computer, Nike Athletic).
KNOWN_ALIASES: Dict[str, str] = {
    "on": "optimum nutrition",
    "optimum": "optimum nutrition",
    "msft": "microsoft",
}


def normalize_brand_name(name: str) -> str:
    """Normalize a brand name for consistent entity resolution.

    - Decomposes Unicode diacritics (e.g. é -> e in L'Oréal).
    - Unifies Unicode apostrophes and punctuation variations.
    - Preserves internal meaningful characters (e.g. 'Co-op', 'Coca-Cola').
    - Removes corporate legal suffixes (Inc, LLC) strictly in trailing position.
    """
    if not name:
        return ""

    # Remove quotes, trademarks, and parenthesis content BEFORE unicode NFKD decomposition
    # because NFKD decomposes ™ into 'TM'
    pre_cleaned = re.sub(r'[\"®™©\u2122\u00ae\u00a9\u201c\u201d]', '', name)
    pre_cleaned = re.sub(r'\((?:tm|r|c)\)', '', pre_cleaned, flags=re.IGNORECASE)
    pre_cleaned = re.sub(r'\([^)]*\)', '', pre_cleaned)

    # Decompose Unicode accents
    decomposed = unicodedata.normalize("NFKD", pre_cleaned)
    stripped_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    lowered = stripped_accents.lower().strip()

    # Handle apostrophe variations: 's -> s, otherwise replace with space (e.g. L'Oreal -> l oreal)
    cleaned = re.sub(r"['’‘`ʻ]s\b", "s", lowered)
    cleaned = re.sub(r"['’‘`ʻ]", " ", cleaned)

    # Context-aware trailing legal suffix removal (only at the end of the brand string)
    # E.g. "Apple Inc." -> "apple", "Nike LLC" -> "nike", but "Co-op" or "Company A" is preserved
    m_legal = re.search(TRAILING_LEGAL_SUFFIX_PATTERN, cleaned, flags=re.IGNORECASE)
    if m_legal and len(cleaned[:m_legal.start()].strip()) >= 2:
        cleaned = cleaned[:m_legal.start()].strip()

    # Trailing "co" or "company" removal only if preceded by multiple words (e.g. "Coca-Cola Co.")
    m_co = re.search(TRAILING_CO_PATTERN, cleaned, flags=re.IGNORECASE)
    if m_co:
        prefix = cleaned[:m_co.start()].strip()
        # Only remove if the prefix is substantive (at least 4 chars and not a standalone single word)
        if len(prefix) >= 4 and len(prefix.split()) >= 1:
            cleaned = prefix

    # Replace hyphens, slashes, and symbols with space
    cleaned = re.sub(r'[-_/&+,.]', ' ', cleaned)

    # Collapse multiple whitespaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # Check known aliases
    if cleaned in KNOWN_ALIASES:
        return KNOWN_ALIASES[cleaned]

    return cleaned


def normalize_text_for_search(text: str) -> str:
    """Normalize a title or snippet text for symmetric brand containment search."""
    if not text:
        return ""
    pre_cleaned = re.sub(r'[\"®™©\u2122\u00ae\u00a9\u201c\u201d]', '', text)
    decomposed = unicodedata.normalize("NFKD", pre_cleaned)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    lowered = stripped.lower()
    lowered = re.sub(r"['’‘`ʻ]s\b", "s", lowered)
    lowered = re.sub(r"['’‘`ʻ]", " ", lowered)
    lowered = re.sub(r'[^a-z0-9\s]', ' ', lowered)
    return re.sub(r'\s+', ' ', lowered).strip()


def get_brand_search_variants(brand_name: Optional[str]) -> List[str]:
    """Return all search term variants for a brand, including its canonical form and safe aliases.

    Variants are sorted from longest to shortest so that specific multi-word phrases
    are evaluated with priority.
    """
    if not brand_name:
        return []

    variants: Set[str] = set()

    # 1. Direct search normalization of the raw brand input
    raw_norm = normalize_text_for_search(brand_name)
    if raw_norm:
        variants.add(raw_norm)

    # 2. Canonical normalized brand name
    canon_norm = normalize_brand_name(brand_name)
    if canon_norm:
        variants.add(canon_norm)

    # 3. Known safe aliases in both directions
    # If the brand is an alias (e.g. "on" -> "optimum nutrition"), add the canonical target
    if canon_norm in KNOWN_ALIASES:
        canonical_target = KNOWN_ALIASES[canon_norm]
        variants.add(normalize_text_for_search(canonical_target))

    # If the brand is the canonical target (e.g. "optimum nutrition"), add any aliases that map to it
    for alias_key, canon_val in KNOWN_ALIASES.items():
        if canon_norm == canon_val:
            variants.add(normalize_text_for_search(alias_key))

    return sorted(list(variants), key=lambda v: len(v), reverse=True)


def is_variant_in_text(variant: str, raw_text: str, norm_text: str) -> bool:
    """Evaluate whether a search variant is present in a block of text.

    For substantive terms (length > 2), word boundary matching on normalized text is used.
    For short acronyms (length <= 2, e.g. 'ON'), uppercase word boundary matching in raw
    text is enforced to avoid false positives on English prepositions ('on').
    """
    if not variant or not raw_text or not norm_text:
        return False

    if len(variant) > 2:
        return bool(re.search(r'\b' + re.escape(variant) + r'\b', norm_text))

    # For short 1-2 character variants, require case-sensitive uppercase whole-word match
    target_caps = variant.upper()
    return bool(re.search(r'\b' + re.escape(target_caps) + r'\b', raw_text))


def extract_domain(url_or_domain: Optional[str]) -> Optional[str]:
    """Extract clean domain hostname from URL or host string."""
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


def is_domain_match(target_domain: Optional[str], candidate_domain: Optional[str]) -> bool:
    """Evaluate exact hostname or valid subdomain matching.

    Prevents false positives such as:
    target: nike.com
    matching: nike.com.example.com or faknike.com
    """
    if not target_domain or not candidate_domain:
        return False

    t = extract_domain(target_domain)
    c = extract_domain(candidate_domain)
    if not t or not c:
        return False

    # Exact hostname match
    if t == c:
        return True

    # Valid subdomain match (e.g. store.nike.com or running.nike.com matches nike.com)
    if c.endswith("." + t):
        return True

    return False


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
    3. Exact/subdomain domain match
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

    # 3. Domain match (using strict hostname/subdomain check)
    if norm_cand_domain:
        for orig_name, norm_name, known_domain in known_brands:
            if known_domain and is_domain_match(known_domain, norm_cand_domain):
                return orig_name
            # Check if domain root exactly equals the normalized brand name
            domain_root = norm_cand_domain.split('.')[0]
            if domain_root == norm_name:
                return orig_name

    # 4. Strong deterministic containment
    # Ensure word boundaries so "Nike" matches "Nike Running", but "Son" does not match "Sony"
    containment_matches: List[str] = []
    cand_words = set(norm_candidate.split())
    for orig_name, norm_name, _ in known_brands:
        brand_words = set(norm_name.split())
        if cand_words and brand_words:
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
        score = fuzz.token_sort_ratio(norm_candidate, norm_name)
        if score >= 88:
            fuzzy_candidates.append((orig_name, score))

    if not fuzzy_candidates:
        return None

    fuzzy_candidates.sort(key=lambda x: x[1], reverse=True)

    # 6. Ambiguity check: if top 2 candidates are within 5 points, reject
    if len(fuzzy_candidates) > 1:
        top_score = fuzzy_candidates[0][1]
        runner_up_score = fuzzy_candidates[1][1]
        if top_score - runner_up_score < 5:
            return None

    return fuzzy_candidates[0][0]
