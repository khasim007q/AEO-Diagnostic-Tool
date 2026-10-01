# scoring_engine.py
import logging
from typing import List, Dict, Any, Optional

from app.models.brand import Brand, Product
from app.api.schemas import GoogleResult, GradeResult
from app.utils.fuzzy import is_same_brand, is_same_product, fuzzy_find_in_text

logger = logging.getLogger(__name__)

# Exponential rank weighting: rank 1 is worth 10x more than rank 5
RANK_WEIGHTS: Dict[int, float] = {
    1: 10.0,
    2: 6.0,
    3: 4.0,
    4: 2.0,
    5: 1.0,
}

# Consensus multiplier: more LLMs agreeing = higher bonus
CONSENSUS_MULTIPLIERS: Dict[int, float] = {
    1: 1.0,
    2: 1.15,
    3: 1.30,
}


def get_rank_weight(rank: int) -> float:
    """Get the point weight for a given rank position.

    Args:
        rank: Rank position (1-5).

    Returns:
        Point weight for that rank, or 0 for invalid ranks.
    """
    return RANK_WEIGHTS.get(rank, 0.0)


def get_consensus_multiplier(llm_count: int) -> float:
    """Get the consensus multiplier based on how many LLMs recommend a brand.

    Args:
        llm_count: Number of LLMs that mention this brand.

    Returns:
        Multiplier value (1.0, 1.15, or 1.30).
    """
    if llm_count >= 3:
        return CONSENSUS_MULTIPLIERS[3]
    return CONSENSUS_MULTIPLIERS.get(llm_count, 1.0)


def get_web_bonus(rank: Optional[int]) -> float:
    """Get web authority bonus based on Google search rank position.

    Higher bonus for appearing higher in Google results,
    instead of the binary validated/not-validated approach.

    Args:
        rank: Google search result position (1-10), or None if not found.

    Returns:
        Bonus points (0.0 to 2.0).
    """
    if rank is None or rank <= 0:
        return 0.0
    if rank <= 3:
        return 2.0
    if rank <= 7:
        return 1.0
    if rank <= 10:
        return 0.5
    return 0.0


def merge_products(
    parsed_data: Dict[str, List[Dict[str, Any]]],
    web_results: List[GoogleResult],
) -> List[Brand]:
    """Process parsed LLM data and web results into scored, grouped brands.

    This is the core scoring pipeline:
    1. Aggregate products from all LLMs, grouping by brand with fuzzy dedup
    2. Apply exponential rank weights
    3. Apply consensus multiplier
    4. Cross-validate against Google results for web authority bonus
    5. Sort by total score descending

    Args:
        parsed_data: Dict mapping LLM name to list of parsed brand/product dicts.
        web_results: List of Google search results.

    Returns:
        Sorted list of Brand objects with computed scores.
    """
    brands_map: Dict[str, Brand] = {}
    total_llm_count = len(parsed_data) if parsed_data else 1

    # Step 1: Aggregate products from LLMs, grouping by brand
    for llm_name, items in parsed_data.items():
        for item in items:
            brand_name = item.get("brand", "").strip() or "Unknown"
            product_name = item.get("product", "").strip() or brand_name
            rank = item.get("rank", 5)

            # Find existing brand via fuzzy match
            target_brand = _find_existing_brand(brand_name, brands_map)

            if not target_brand:
                target_brand = Brand(name=brand_name)
                brands_map[brand_name.lower()] = target_brand

            # Track LLM coverage (avoid duplicates)
            if llm_name not in target_brand.llm_coverage:
                target_brand.llm_coverage.append(llm_name)

            # Find existing product via fuzzy match, but only if
            # the product has NOT already been scored by this LLM
            target_product = _find_existing_product(
                product_name, target_brand, llm_name
            )

            if not target_product:
                full_name = product_name
                if brand_name.lower() not in product_name.lower():
                    full_name = f"{brand_name} {product_name}"

                target_product = Product(
                    brand_name=target_brand.name,
                    product_name=product_name,
                    full_name=full_name.strip(),
                )
                target_brand.products.append(target_product)

            # Record the rank for this LLM
            if llm_name not in target_product.ranks:
                target_product.ranks[llm_name] = rank

    # Step 2: Compute scores with consensus multiplier and web bonus
    for brand in brands_map.values():
        brand.consensus_pct = (len(brand.llm_coverage) / total_llm_count) * 100.0
        consensus_mult = get_consensus_multiplier(len(brand.llm_coverage))
        brand.total_score = 0.0

        for product in brand.products:
            # Base score from exponential rank weights
            base_score = sum(
                get_rank_weight(r) for r in product.ranks.values()
            )

            # Web validation: check if product/brand appears in Google results
            best_web_rank = _find_web_rank(
                product.product_name, brand.name, web_results
            )
            product.web_rank = best_web_rank
            product.web_validated = best_web_rank is not None

            web_bonus = get_web_bonus(best_web_rank)

            # Final score: (base * consensus) + web bonus
            product.score = round((base_score * consensus_mult) + web_bonus, 2)
            brand.total_score += product.score

        brand.total_score = round(brand.total_score, 2)

    # Step 3: Sort by total score descending
    sorted_brands = sorted(
        brands_map.values(),
        key=lambda b: b.total_score,
        reverse=True,
    )
    return sorted_brands


def _find_existing_brand(
    brand_name: str, brands_map: Dict[str, Brand]
) -> Optional[Brand]:
    """Find an existing brand in the map via fuzzy matching.

    Args:
        brand_name: Brand name to search for.
        brands_map: Current mapping of brand keys to Brand objects.

    Returns:
        Matching Brand object, or None.
    """
    for existing_brand in brands_map.values():
        if is_same_brand(existing_brand.name, brand_name):
            return existing_brand
    return None


def _find_existing_product(
    product_name: str, brand: Brand, current_llm: str
) -> Optional[Product]:
    """Find an existing product under a brand, avoiding self-merge.

    A product should not be merged with one that already has a score
    from the current LLM, since each LLM's list items are distinct.

    Args:
        product_name: Product name to search for.
        brand: The parent Brand object.
        current_llm: The LLM name currently being processed.

    Returns:
        Matching Product object, or None.
    """
    for existing_product in brand.products:
        if current_llm in existing_product.ranks:
            continue
        if is_same_product(existing_product.product_name, product_name):
            return existing_product
    return None


def _find_web_rank(
    product_name: str,
    brand_name: str,
    web_results: List[GoogleResult],
) -> Optional[int]:
    """Find the best Google rank position where a product/brand appears.

    Searches through Google result titles and snippets using fuzzy matching.

    Args:
        product_name: Product name to search for.
        brand_name: Brand name to search for.
        web_results: List of Google search results.

    Returns:
        Google result rank (1-10) or None if not found.
    """
    product_lower = product_name.lower()
    brand_lower = brand_name.lower()

    for result in web_results:
        text = f"{result.title} {result.snippet}".lower()
        if brand_lower in text or product_lower in text:
            return result.rank

    # Fuzzy fallback for near-matches
    for result in web_results:
        text = f"{result.title} {result.snippet}"
        if fuzzy_find_in_text(brand_name, text, threshold=75):
            return result.rank

    return None


def calculate_grade(score: float, max_possible: float = 50.0) -> GradeResult:
    """Calculate a letter grade based on score as a percentage of max possible.

    Grade thresholds:
    - A: >= 80% (Excellent AI visibility)
    - B: >= 60% (Good AI visibility)
    - C: >= 40% (Average AI visibility)
    - D: >= 20% (Poor AI visibility)
    - F: < 20% (Not visible to AI engines)

    Args:
        score: The brand's total score.
        max_possible: Maximum achievable score.

    Returns:
        GradeResult with grade letter, label, score, and max_score.
    """
    if max_possible <= 0:
        pct = 0.0
    else:
        pct = (score / max_possible) * 100.0

    if pct >= 80:
        grade, label = "A", "Excellent AI visibility across all engines"
    elif pct >= 60:
        grade, label = "B", "Good visibility, room for improvement"
    elif pct >= 40:
        grade, label = "C", "Average visibility, significant gaps exist"
    elif pct >= 20:
        grade, label = "D", "Poor visibility, major improvements needed"
    else:
        grade, label = "F", "Not visible to AI engines for this query"

    return GradeResult(
        grade=grade,
        label=label,
        score=round(score, 2),
        max_score=round(max_possible, 2),
    )


def generate_insights(
    brands: List[Brand], your_brand_name: Optional[str]
) -> List[str]:
    """Generate actionable text insights based on diagnostic results.

    Args:
        brands: Sorted list of Brand objects.
        your_brand_name: The user's brand name (may be None).

    Returns:
        List of insight strings.
    """
    insights: List[str] = []

    if not brands:
        return ["No brands were found in AI recommendations for this query."]

    top_brand = brands[0]
    insights.append(
        f"The top performing brand is {top_brand.name} "
        f"with a total score of {top_brand.total_score:.1f}."
    )

    # Count how many brands have web validation
    web_validated_count = sum(
        1 for b in brands
        if any(p.web_validated for p in b.products)
    )
    insights.append(
        f"{web_validated_count} out of {len(brands)} brands are validated "
        f"in Google search results."
    )

    if not your_brand_name:
        return insights

    # Find the user's brand
    your_brand: Optional[Brand] = None
    for b in brands:
        if is_same_brand(b.name, your_brand_name):
            your_brand = b
            break

    if not your_brand:
        insights.append(
            f"{your_brand_name} was not mentioned by any AI engine "
            f"for this query. The dominant brand is {top_brand.name}."
        )
        insights.append(
            "Consider improving your content strategy and web presence "
            "to increase AI recommendation visibility."
        )
        return insights

    # Which LLMs mention the user vs which do not
    all_llm_names = set()
    for b in brands:
        all_llm_names.update(b.llm_coverage)

    mentioned_in = set(your_brand.llm_coverage)
    not_mentioned_in = all_llm_names - mentioned_in

    if not_mentioned_in:
        for missing_llm in not_mentioned_in:
            # Find who dominates in that LLM
            dominant = "competitors"
            for b in brands:
                if b != your_brand and missing_llm in b.llm_coverage:
                    dominant = b.name
                    break
            insights.append(
                f"{missing_llm} does not mention your brand. "
                f"{dominant} dominates there instead."
            )

    # Score gap vs top competitor
    competitors = [b for b in brands if b != your_brand]
    if competitors:
        top_comp = competitors[0]
        gap = top_comp.total_score - your_brand.total_score
        if gap > 0:
            insights.append(
                f"{top_comp.name} outscores you by {gap:.1f} points "
                f"across AI engines."
            )
        elif gap < 0:
            insights.append(
                f"You outscore your nearest competitor ({top_comp.name}) "
                f"by {abs(gap):.1f} points."
            )
        else:
            insights.append(
                f"You are tied with {top_comp.name} at {your_brand.total_score:.1f} points."
            )

    # Web validation insight
    has_web = any(p.web_validated for p in your_brand.products)
    if not has_web:
        insights.append(
            "Your brand does not appear in top Google results for this query. "
            "Improving SEO may help boost your AI recommendation visibility."
        )
    else:
        insights.append(
            "Your brand appears in Google search results, "
            "which likely supports your AI recommendation visibility."
        )

    # Consensus insight
    if your_brand.consensus_pct >= 100:
        insights.append(
            "All AI engines agree on your brand, a strong consensus signal."
        )
    elif your_brand.consensus_pct >= 66:
        insights.append(
            "2 out of 3 AI engines mention you. "
            "There is room to grow on the remaining engine."
        )

    return insights
