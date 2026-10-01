# router.py
import logging
from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    DiagnosticRequest,
    DiagnosticResponse,
    BrandResult,
    ProductResult,
    GapEntry,
    GoogleResult,
)
from app.services.llm_service import query_llms, MODELS
from app.services.serp_service import search_google
from app.services.parser_service import parse_llm_response
from app.services.scoring_engine import (
    merge_products,
    calculate_grade,
    generate_insights,
)
from app.utils.fuzzy import is_same_brand

logger = logging.getLogger(__name__)

api_router = APIRouter()


@api_router.post("/diagnostic", response_model=DiagnosticResponse)
async def run_diagnostic(request: DiagnosticRequest):
    """Run a full AEO diagnostic for the given query.

    Orchestrates the entire pipeline:
    1. Query all LLMs in parallel
    2. Search Google via SerpApi
    3. Parse and extract brands/products from LLM responses
    4. Score, group, and cross-validate
    5. Generate grade, insights, and gap analysis

    Args:
        request: DiagnosticRequest with query and optional brand name.

    Returns:
        DiagnosticResponse with all results.
    """
    try:
        # 1. Fetch data from LLMs and Google in parallel
        llm_responses = await query_llms(request.query)
        web_results = search_google(request.query)

        # 2. Parse LLM responses into brand/product structures
        parsed_data = {}
        for model_name, res in llm_responses.items():
            if res.get("error"):
                logger.warning("Error from %s: %s", model_name, res["error"])
                continue
            raw_text = res.get("raw_text", "")
            parsed = parse_llm_response(raw_text)
            if parsed:
                parsed_data[model_name] = parsed
                res["parsed_count"] = len(parsed)
            else:
                res["parsed_count"] = 0

        # 3. Merge, score, and group by brand
        brands = merge_products(parsed_data, web_results)

        # 4. Map domain models to response schemas
        all_brands = _brands_to_results(brands)

        # 5. Separate user's brand from competitors
        your_brand_result = None
        competitors = []

        if request.your_brand:
            your_brand_lower = request.your_brand.strip().lower()
            for brand_result in all_brands:
                if is_same_brand(brand_result.name, your_brand_lower, threshold=70):
                    if your_brand_result is None:
                        your_brand_result = brand_result
                    else:
                        competitors.append(brand_result)
                else:
                    competitors.append(brand_result)
        else:
            competitors = list(all_brands)

        # 6. Calculate grade
        # Max possible: rank 1 (10pts) x 3 LLMs x 1.30 consensus + 2.0 web = 41.0
        max_possible = (10.0 * 3 * 1.30) + 2.0
        score = your_brand_result.total_score if your_brand_result else 0.0
        grade = calculate_grade(score, max_possible)

        # 7. Generate insights
        insights = generate_insights(brands, request.your_brand)

        # 8. Build gap analysis (per-LLM comparison with top competitors)
        gap_analysis = _build_gap_analysis(
            your_brand_result, competitors, brands
        )

        # 9. Convert GoogleResult schemas for the response
        google_result_schemas = [
            GoogleResult(
                rank=r.rank,
                title=r.title,
                snippet=r.snippet,
                url=r.url,
            )
            for r in web_results[:10]
        ]

        llm_names = [m["name"] for m in MODELS]

        return DiagnosticResponse(
            grade=grade,
            your_brand=your_brand_result,
            all_brands=all_brands,
            competitors=competitors[:10],
            gap_analysis=gap_analysis,
            insights=insights,
            google_results=google_result_schemas,
            raw_llm_responses={
                name: {
                    "raw": res.get("raw_text", ""),
                    "parsed_count": res.get("parsed_count", 0),
                }
                for name, res in llm_responses.items()
            },
            llm_names=llm_names,
        )

    except ValueError as e:
        logger.error("Validation error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Diagnostic error: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while running the diagnostic.",
        )


def _brands_to_results(brands: list) -> list[BrandResult]:
    """Convert domain Brand objects to BrandResult schemas.

    Args:
        brands: List of Brand domain objects.

    Returns:
        List of BrandResult Pydantic models.
    """
    results = []
    for b in brands:
        products = [
            ProductResult(
                brand_name=p.brand_name,
                product_name=p.product_name,
                full_name=p.full_name,
                ranks=p.ranks,
                score=p.score,
                web_validated=p.web_validated,
                web_rank=p.web_rank,
            )
            for p in b.products
        ]
        results.append(
            BrandResult(
                name=b.name,
                products=products,
                total_score=b.total_score,
                llm_coverage=list(b.llm_coverage),
                consensus_pct=round(b.consensus_pct, 1),
            )
        )
    return results


def _build_gap_analysis(
    your_brand: BrandResult | None,
    competitors: list[BrandResult],
    brands: list,
) -> list[GapEntry]:
    """Build per-LLM gap analysis between user's brand and competitors.

    Args:
        your_brand: The user's brand result (may be None).
        competitors: List of competitor brand results.
        brands: Raw Brand domain objects (for LLM coverage lookup).

    Returns:
        List of GapEntry objects.
    """
    if not your_brand or not competitors:
        return []

    gap_entries = []

    # Get all LLM names from the brands data
    all_llms: set[str] = set()
    for b in brands:
        all_llms.update(b.llm_coverage)

    for comp in competitors[:5]:
        for llm in sorted(all_llms):
            # Find scores for this LLM from products
            your_llm_score = _get_llm_score(your_brand, llm)
            comp_llm_score = _get_llm_score(comp, llm)
            diff = your_llm_score - comp_llm_score

            if diff > 0:
                status = "winning"
            elif diff < 0:
                status = "losing"
            else:
                status = "tied"

            gap_entries.append(
                GapEntry(
                    competitor=comp.name,
                    llm=llm,
                    your_score=your_llm_score,
                    their_score=comp_llm_score,
                    gap=round(abs(diff), 2),
                    status=status,
                )
            )

    return gap_entries


def _get_llm_score(brand: BrandResult, llm_name: str) -> float:
    """Get a brand's total score contribution from a specific LLM.

    Args:
        brand: BrandResult to inspect.
        llm_name: Name of the LLM.

    Returns:
        Sum of scores from products that have ranks for this LLM.
    """
    total = 0.0
    for product in brand.products:
        if llm_name in product.ranks:
            # The product's score already includes consensus multiplier,
            # so we use the raw rank weight for per-LLM comparison
            from app.services.scoring_engine import get_rank_weight
            total += get_rank_weight(product.ranks[llm_name])
    return total
