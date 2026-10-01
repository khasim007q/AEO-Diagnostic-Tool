# scoring_engine.py
import statistics
import logging
from typing import List, Dict, Any, Optional, Tuple

from app.models.brand import Brand, EngineObservation, ProductEvidence
from app.services.llm_service import EngineExecutionResult
from app.services.serp_service import GoogleCorroborationSummary
from app.utils.entity_resolution import (
    normalize_brand_name,
    resolve_brand_entity,
    extract_domain,
)

logger = logging.getLogger(__name__)

# Position score weights for top-5 recommendations
POSITION_SCORE_WEIGHTS = {
    1: 1.00,
    2: 0.80,
    3: 0.60,
    4: 0.40,
    5: 0.20,
}


def get_position_score(rank: Optional[int]) -> float:
    """Return the deterministic position score for a rank (1..5)."""
    if rank is None:
        return 0.0
    return POSITION_SCORE_WEIGHTS.get(rank, 0.0)


def get_visibility_label(score: float, mentioned: bool) -> str:
    """Return an objective descriptive label for an AI Visibility Score."""
    if not mentioned or score <= 0.0:
        return "Not visible"
    if score >= 70.0:
        return "High visibility"
    if score >= 40.0:
        return "Moderate visibility"
    return "Low visibility"


def aggregate_brands(
    engine_results: Dict[str, EngineExecutionResult],
    target_brand_name: Optional[str] = None,
    target_domain: Optional[str] = None,
) -> Tuple[List[Brand], Optional[Brand], List[Brand]]:
    """Aggregate engine results into Brand ranking entities with deterministic AI Visibility Scores.

    Rules:
    - Exactly one scoring observation per brand per successful engine run.
    - If multiple products for the same brand appear in an engine, only the BEST rank is scored.
    - All products remain preserved as supporting evidence.
    - AI Visibility Score = 100 * mean(position_score) across SUCCESSFUL engines.
    - Failed or invalid engines do not penalize the score denominator.
    - No consensus multiplier.
    - No Google search bonus.
    - Guaranteed 0 to 100.

    Returns:
        (all_brands, target_brand, competitors)
    """
    configured_engine_count = len(engine_results)
    successful_engines = [
        engine for engine, res in engine_results.items()
        if res.status == "success"
    ]
    num_successful = len(successful_engines)

    # Master map of normalized_brand_name -> Brand
    brand_map: Dict[str, Brand] = {}
    # Cache of known brands for entity resolution: list of (canonical_name, normalized_name, domain)
    known_entities: List[Tuple[str, str, Optional[str]]] = []

    # If target brand provided, register it first so variations resolve to target
    clean_target_name = target_brand_name.strip() if target_brand_name else None
    if clean_target_name:
        norm_target = normalize_brand_name(clean_target_name)
        target_b = Brand(
            name=clean_target_name,
            normalized_name=norm_target,
            domain=extract_domain(target_domain),
            configured_engine_count=configured_engine_count,
        )
        brand_map[norm_target] = target_b
        known_entities.append((clean_target_name, norm_target, target_b.domain))

    # Process each engine run
    for engine_name, res in engine_results.items():
        is_success = (res.status == "success")

        # Map of resolved_brand_name -> list of product items in this engine run
        engine_brand_products: Dict[str, List[ProductEvidence]] = {}

        if is_success and res.parse_result and res.parse_result.recommendations:
            for rec in res.parse_result.recommendations:
                candidate_brand = rec.brand.strip()
                if not candidate_brand:
                    continue

                # Resolve entity against known brands
                resolved_orig_name = resolve_brand_entity(
                    candidate_brand,
                    known_entities,
                    candidate_domain=target_domain if clean_target_name and candidate_brand.lower() == clean_target_name.lower() else None,
                )

                if resolved_orig_name:
                    canonical_name = resolved_orig_name
                    norm_key = normalize_brand_name(canonical_name)
                else:
                    canonical_name = candidate_brand
                    norm_key = normalize_brand_name(candidate_brand)
                    # Register new entity
                    known_entities.append((canonical_name, norm_key, None))

                if norm_key not in brand_map:
                    brand_map[norm_key] = Brand(
                        name=canonical_name,
                        normalized_name=norm_key,
                        configured_engine_count=configured_engine_count,
                    )

                evidence = ProductEvidence(
                    brand_name=canonical_name,
                    product_name=rec.product,
                    full_name=rec.product,
                    rank=rec.rank,
                    engine=engine_name,
                )

                if norm_key not in engine_brand_products:
                    engine_brand_products[norm_key] = []
                engine_brand_products[norm_key].append(evidence)

        # For every brand known so far, record its observation for this engine
        for norm_key, brand in brand_map.items():
            if norm_key in engine_brand_products:
                products = engine_brand_products[norm_key]
                best_rank = min(p.rank for p in products)
                pos_score = get_position_score(best_rank)
                obs = EngineObservation(
                    engine=engine_name,
                    status=res.status,
                    mentioned=True,
                    best_rank=best_rank,
                    position_score=pos_score,
                    products=products,
                    latency_ms=res.latency_ms,
                    error_type=res.error_type,
                )
                brand.products.extend(products)
            else:
                obs = EngineObservation(
                    engine=engine_name,
                    status=res.status,
                    mentioned=False,
                    best_rank=None,
                    position_score=0.0,
                    products=[],
                    latency_ms=res.latency_ms,
                    error_type=res.error_type,
                )
            brand.observations[engine_name] = obs

    # Calculate deterministic metrics for each brand
    for brand in brand_map.values():
        brand.configured_engine_count = configured_engine_count
        brand.successful_engine_count = num_successful

        # Only evaluate across successful engines
        mentioned_in_successful = [
            obs for obs in brand.observations.values()
            if obs.status == "success" and obs.mentioned and obs.best_rank is not None
        ]
        brand.mentioned_engine_count = len(mentioned_in_successful)

        # Engine availability
        brand.engine_availability = (
            round((num_successful / configured_engine_count) * 100.0, 1)
            if configured_engine_count > 0 else 0.0
        )

        # Mention coverage = engines mentioning brand / successful engines
        brand.mention_coverage = (
            round((brand.mentioned_engine_count / num_successful) * 100.0, 1)
            if num_successful > 0 else 0.0
        )

        # AI Visibility Score = 100 * mean(position_score for successful engines)
        if num_successful > 0:
            total_position_score = sum(
                brand.observations[eng].position_score
                for eng in successful_engines
                if eng in brand.observations
            )
            raw_score = (total_position_score / num_successful) * 100.0
            # Strictly clamp between 0.0 and 100.0
            brand.ai_visibility_score = round(max(0.0, min(100.0, raw_score)), 1)
        else:
            brand.ai_visibility_score = 0.0

        # Rank statistics
        ranks = [obs.best_rank for obs in mentioned_in_successful if obs.best_rank is not None]
        if ranks:
            brand.best_rank = min(ranks)
            brand.worst_rank = max(ranks)
            brand.average_rank = round(sum(ranks) / len(ranks), 1)
            brand.median_rank = round(float(statistics.median(ranks)), 1)
        else:
            brand.best_rank = None
            brand.worst_rank = None
            brand.average_rank = None
            brand.median_rank = None

    # Sort all brands by AI Visibility Score descending, then by mentioned count, then name
    sorted_brands = sorted(
        brand_map.values(),
        key=lambda b: (b.ai_visibility_score, b.mentioned_engine_count, -1 * (b.best_rank or 99)),
        reverse=True,
    )

    # Separate target brand and competitors
    target_brand_obj: Optional[Brand] = None
    competitors: List[Brand] = []

    if clean_target_name:
        norm_target = normalize_brand_name(clean_target_name)
        target_brand_obj = brand_map.get(norm_target)
        competitors = [b for b in sorted_brands if b.normalized_name != norm_target]
    else:
        competitors = sorted_brands

    return sorted_brands, target_brand_obj, competitors


def calculate_gap_analysis(
    target_brand: Optional[Brand],
    competitors: List[Brand],
    engine_names: List[str],
) -> List[Dict[str, Any]]:
    """Compute deterministic gap analysis: your_score - competitor_score.

    CRITICAL:
    - Gap sign must be preserved (your_score - competitor_score).
    - Do NOT apply abs().
    - +4.0 means target is ahead.
    - -6.0 means competitor is ahead.
    - 0.0 means tied.
    - Status is derived directly from the sign.
    """
    if not target_brand:
        return []

    gaps: List[Dict[str, Any]] = []

    # Head-to-head overall gap vs top 5 competitors
    for comp in competitors[:5]:
        overall_gap = round(target_brand.ai_visibility_score - comp.ai_visibility_score, 1)
        if overall_gap > 0:
            status = "winning"
        elif overall_gap < 0:
            status = "losing"
        else:
            status = "tied"

        gaps.append({
            "competitor": comp.name,
            "engine": "Overall",
            "your_score": target_brand.ai_visibility_score,
            "their_score": comp.ai_visibility_score,
            "gap": overall_gap,
            "status": status,
        })

        # Per-engine breakdown
        for eng in engine_names:
            target_obs = target_brand.observations.get(eng)
            comp_obs = comp.observations.get(eng)

            # Score in this engine out of 100
            target_pos = round((target_obs.position_score * 100.0), 1) if target_obs else 0.0
            comp_pos = round((comp_obs.position_score * 100.0), 1) if comp_obs else 0.0

            eng_gap = round(target_pos - comp_pos, 1)
            if eng_gap > 0:
                eng_status = "winning"
            elif eng_gap < 0:
                eng_status = "losing"
            else:
                eng_status = "tied"

            gaps.append({
                "competitor": comp.name,
                "engine": eng,
                "your_score": target_pos,
                "their_score": comp_pos,
                "gap": eng_gap,
                "status": eng_status,
            })

    return gaps


def generate_typed_insights(
    target_brand: Optional[Brand],
    all_brands: List[Brand],
    engine_results: Dict[str, EngineExecutionResult],
    google_summary: GoogleCorroborationSummary,
) -> List[Dict[str, Any]]:
    """Generate typed, evidence-based insights without unsupported causal claims.

    Rules:
    - Never say 'Improving SEO will boost AI visibility'.
    - Never say 'Google validates the AI recommendation'.
    - Provide factual, evidence-backed statements with attached metadata.
    """
    insights: List[Dict[str, Any]] = []
    configured_count = len(engine_results)
    successful_count = sum(1 for res in engine_results.values() if res.status == "success")
    failed_engines = [eng for eng, res in engine_results.items() if res.status == "failed"]
    invalid_engines = [eng for eng, res in engine_results.items() if res.status == "invalid"]

    # 1. Engine Availability Insight
    if failed_engines or invalid_engines:
        affected = failed_engines + invalid_engines
        insights.append({
            "type": "warning",
            "title": "Incomplete Engine Diagnostic",
            "message": f"{len(affected)} of {configured_count} models ({', '.join(affected)}) encountered connectivity or parsing failures during this run.",
            "evidence": {
                "configured": configured_count,
                "successful": successful_count,
                "failed": failed_engines,
                "invalid": invalid_engines,
            },
        })
    else:
        insights.append({
            "type": "info",
            "title": "Complete Multi-Model Consensus",
            "message": f"Successfully gathered recommendations across all {configured_count} configured evaluation models.",
            "evidence": {"configured": configured_count, "successful": successful_count},
        })

    # 2. Market Leader Overview
    if all_brands:
        leader = all_brands[0]
        insights.append({
            "type": "info",
            "title": "Category Leader",
            "message": f"{leader.name} leads with an AI Visibility Score of {leader.ai_visibility_score}/100 across {leader.mentioned_engine_count} of {successful_count} responsive engines.",
            "evidence": {
                "leader": leader.name,
                "score": leader.ai_visibility_score,
                "mentions": leader.mentioned_engine_count,
                "best_rank": leader.best_rank,
            },
        })

    # 3. Target Brand Specific Findings
    if target_brand:
        if target_brand.mentioned_engine_count > 0:
            insights.append({
                "type": "positive" if target_brand.ai_visibility_score >= 60 else "info",
                "title": f"Target Brand Presence: {target_brand.name}",
                "message": f"{target_brand.name} achieves an AI Visibility Score of {target_brand.ai_visibility_score}/100, appearing in {target_brand.mentioned_engine_count} of {successful_count} responsive models with a median rank of #{target_brand.median_rank}.",
                "evidence": {
                    "score": target_brand.ai_visibility_score,
                    "coverage": target_brand.mention_coverage,
                    "median_rank": target_brand.median_rank,
                    "best_rank": target_brand.best_rank,
                },
            })

            # Check individual engine misses
            missed_engines = [
                eng for eng, obs in target_brand.observations.items()
                if obs.status == "success" and not obs.mentioned
            ]
            if missed_engines:
                insights.append({
                    "type": "warning",
                    "title": "Model Coverage Gap",
                    "message": f"{', '.join(missed_engines)} did not include {target_brand.name} in its top-5 product recommendations.",
                    "evidence": {"missed_engines": missed_engines},
                })
        else:
            insights.append({
                "type": "warning",
                "title": f"Target Brand Not Recommended: {target_brand.name}",
                "message": f"{target_brand.name} was not featured among the top-5 recommendations across any responsive evaluation model for this query.",
                "evidence": {"score": 0.0, "mentioned_engine_count": 0},
            })

    # 4. Search Corroboration Findings (Independent Signal)
    if google_summary.status == "success":
        if google_summary.brand_found:
            insights.append({
                "type": "positive",
                "title": "Search Corroboration Detected",
                "message": f"Organic Google Search contains references matching the target brand at position #{google_summary.best_google_rank}.",
                "evidence": {
                    "best_google_rank": google_summary.best_google_rank,
                    "total_organic_results": google_summary.total_results,
                },
            })
        elif target_brand:
            insights.append({
                "type": "info",
                "title": "Search Corroboration Absent",
                "message": f"No organic Google Page 1 result matched {target_brand.name} or its domain for this specific query.",
                "evidence": {"total_organic_results": google_summary.total_results},
            })
    elif google_summary.status == "not_configured":
        insights.append({
            "type": "info",
            "title": "Search Corroboration Not Configured",
            "message": "Google organic search corroboration is disabled because SERPAPI_KEY is not configured.",
            "evidence": {"status": "not_configured"},
        })
    elif google_summary.status == "failed":
        insights.append({
            "type": "warning",
            "title": "Search Corroboration Unavailable",
            "message": f"Google Search request failed: {google_summary.error_message}",
            "evidence": {"status": "failed", "error": google_summary.error_message},
        })

    return insights
