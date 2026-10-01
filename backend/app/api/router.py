import uuid
import time
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from collections import defaultdict
from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.api.schemas import (
    DiagnosticRequest,
    DiagnosticResponse,
    BrandResultSchema,
    ProductEvidenceSchema,
    EngineObservationSchema,
    SupportingMetricsSchema,
    EngineSummarySchema,
    GoogleCorroborationSummarySchema,
    GoogleCorroborationResultSchema,
    GapEntrySchema,
    TypedInsightSchema,
    RequestMetadataSchema,
    RawEvidenceSchema,
)
from app.services.llm_service import query_llms_parallel, MODELS, EngineExecutionResult
from app.services.serp_service import search_google_corroboration, GoogleCorroborationSummary
from app.services.scoring_engine import (
    aggregate_brands,
    calculate_gap_analysis,
    generate_typed_insights,
    get_visibility_label,
)
from app.models.brand import Brand

logger = logging.getLogger(__name__)

api_router = APIRouter()

# Global semaphore to bound concurrent expensive diagnostic runs
CONCURRENCY_SEMAPHORE = asyncio.Semaphore(settings.CONCURRENCY_LIMIT)

# Bounded in-memory sliding window rate limiter: IP -> list of request timestamps
_ip_request_timestamps: Dict[str, List[float]] = defaultdict(list)


def _check_rate_limit(client_ip: str) -> None:
    """Enforce a bounded in-memory sliding window rate limit per client IP."""
    now = time.time()
    cutoff = now - settings.RATE_LIMIT_WINDOW_SECONDS

    # Prune stale entries if map is getting large
    if len(_ip_request_timestamps) > settings.MAX_RATE_LIMIT_ENTRIES:
        stale_ips = [ip for ip, ts_list in _ip_request_timestamps.items() if not ts_list or max(ts_list) <= cutoff]
        for ip in stale_ips:
            _ip_request_timestamps.pop(ip, None)
        # If still over limit, drop oldest
        if len(_ip_request_timestamps) > settings.MAX_RATE_LIMIT_ENTRIES:
            sorted_ips = sorted(_ip_request_timestamps.items(), key=lambda item: max(item[1]) if item[1] else 0)
            for ip, _ in sorted_ips[:len(_ip_request_timestamps) - settings.MAX_RATE_LIMIT_ENTRIES]:
                _ip_request_timestamps.pop(ip, None)

    timestamps = _ip_request_timestamps[client_ip]
    valid_timestamps = [t for t in timestamps if t > cutoff]
    _ip_request_timestamps[client_ip] = valid_timestamps

    if len(valid_timestamps) >= settings.RATE_LIMIT_MAX_REQUESTS:
        logger.warning("Rate limit exceeded for IP: %s", client_ip)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait a minute before running another diagnostic.",
        )

    _ip_request_timestamps[client_ip].append(now)


# Global daily spend protection tracker: tracks requests and LLM calls per UTC day
_daily_budget_tracker: Dict[str, Any] = {
    "date": "",
    "requests": 0,
    "llm_calls": 0,
}


def _check_global_budget(num_engines: int = len(MODELS)) -> None:
    """Enforce daily global limits on total requests and LLM calls to prevent runaway API spend."""
    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Reset counter if day has changed
    if _daily_budget_tracker["date"] != current_date:
        _daily_budget_tracker["date"] = current_date
        _daily_budget_tracker["requests"] = 0
        _daily_budget_tracker["llm_calls"] = 0

    if _daily_budget_tracker["requests"] >= settings.DAILY_REQUEST_BUDGET:
        logger.warning("Global daily request budget reached: %d", _daily_budget_tracker["requests"])
        raise HTTPException(
            status_code=429,
            detail="Global daily diagnostic request budget reached. Please try again tomorrow.",
        )

    if _daily_budget_tracker["llm_calls"] + num_engines > settings.DAILY_LLM_CALL_BUDGET:
        logger.warning("Global daily LLM call budget reached: %d", _daily_budget_tracker["llm_calls"])
        raise HTTPException(
            status_code=429,
            detail="Global daily LLM call budget reached. Please try again tomorrow.",
        )

    _daily_budget_tracker["requests"] += 1
    _daily_budget_tracker["llm_calls"] += num_engines


@api_router.post("/diagnostic", response_model=DiagnosticResponse)
async def run_diagnostic(request: DiagnosticRequest, req: Request):
    """Run an AI Visibility Diagnostic with parallel model execution and search corroboration."""
    # 1. API Protection: Rate limiting and global spend protection
    client_ip = req.client.host if req.client else "unknown"
    _check_rate_limit(client_ip)
    _check_global_budget(len(MODELS))

    # 2. Concurrency limiting and time budgeting
    deadline = time.monotonic() + settings.DIAGNOSTIC_TIMEOUT_SECONDS

    async with CONCURRENCY_SEMAPHORE:
        try:
            # 3. Concurrent execution: LLM queries and Google Search run in parallel
            llm_task = asyncio.create_task(query_llms_parallel(request.query, deadline=deadline))
            google_task = asyncio.create_task(
                search_google_corroboration(
                    query=request.query,
                    target_brand=request.your_brand,
                    website_or_domain=request.website_or_domain,
                    market=request.market,
                    location=request.location,
                    language=request.language,
                    google_domain=request.google_domain,
                )
            )

            # Wait for both tasks concurrently with a hard timeout
            llm_results, google_summary = await asyncio.wait_for(
                asyncio.gather(llm_task, google_task),
                timeout=settings.DIAGNOSTIC_TIMEOUT_SECONDS + 5.0,
            )

        except asyncio.TimeoutError:
            req_id = str(uuid.uuid4())
            logger.error("Diagnostic execution timed out [req_id=%s]", req_id)
            raise HTTPException(
                status_code=504,
                detail=f"Diagnostic request timed out while contacting evaluation models. Request ID: {req_id}",
            )
        except HTTPException:
            raise
        except Exception as exc:
            req_id = str(uuid.uuid4())
            logger.error("Diagnostic execution failed [req_id=%s]: %s", req_id, exc, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"An internal error occurred during diagnostic execution. Request ID: {req_id}",
            )

    # 4. Deterministic Brand Aggregation & Scoring
    all_brands, target_brand, competitors = aggregate_brands(
        engine_results=llm_results,
        target_brand_name=request.your_brand,
        target_domain=request.website_or_domain,
    )

    # 5. Determine Primary AI Visibility Score & Label
    # If target brand was provided, the primary score is the target brand's score.
    # Otherwise, it reflects the category leader's score.
    if target_brand:
        primary_score = target_brand.ai_visibility_score
        primary_label = get_visibility_label(primary_score, target_brand.mentioned_engine_count > 0)
        primary_metrics = _map_supporting_metrics(target_brand)
    elif all_brands:
        leader = all_brands[0]
        primary_score = leader.ai_visibility_score
        primary_label = get_visibility_label(primary_score, leader.mentioned_engine_count > 0)
        primary_metrics = _map_supporting_metrics(leader)
    else:
        primary_score = 0.0
        primary_label = "Not visible"
        primary_metrics = SupportingMetricsSchema(
            engine_availability=0.0,
            engine_availability_display="0/0 engines",
            mention_coverage=0.0,
            mention_coverage_display="0/0 (0%)",
            median_rank=None,
            average_rank=None,
            best_rank=None,
            worst_rank=None,
            successful_engine_count=0,
            configured_engine_count=len(llm_results),
            mentioned_engine_count=0,
        )

    # 6. Gap Analysis
    engine_names = [m["name"] for m in MODELS]
    gaps = calculate_gap_analysis(target_brand, competitors, engine_names)

    # 7. Typed, Evidence-Only Insights
    insights = generate_typed_insights(
        target_brand=target_brand,
        all_brands=all_brands,
        engine_results=llm_results,
        google_summary=google_summary,
    )

    # 8. Assemble Engine Summaries & Raw Evidence
    engine_summaries: List[EngineSummarySchema] = []
    raw_evidence_dict: Dict[str, RawEvidenceSchema] = {}

    for eng_name, res in llm_results.items():
        recs_count = len(res.parse_result.recommendations) if res.parse_result else 0
        engine_summaries.append(
            EngineSummarySchema(
                engine=eng_name,
                status=res.status,
                latency_ms=res.latency_ms,
                attempts=res.attempts,
                recommendations_count=recs_count,
                error_type=res.error_type,
                error_message=res.error_message,
            )
        )
        raw_evidence_dict[eng_name] = RawEvidenceSchema(
            engine=eng_name,
            status=res.status,
            raw_content=res.raw_text,
            parsed_count=recs_count,
            latency_ms=res.latency_ms,
            attempts=res.attempts,
            error=res.error_message,
        )

    # 9. Format Google Corroboration Summary
    google_corroboration_schema = GoogleCorroborationSummarySchema(
        status=google_summary.status,
        error_message=google_summary.error_message,
        total_results=google_summary.total_results,
        brand_found=google_summary.brand_found,
        best_google_rank=google_summary.best_google_rank,
        results=[
            GoogleCorroborationResultSchema(
                rank=r.rank,
                title=r.title,
                snippet=r.snippet,
                url=r.url,
                domain=r.domain,
                title_match=r.title_match,
                snippet_match=r.snippet_match,
                domain_match=r.domain_match,
                normalized_brand_match=r.normalized_brand_match,
                match_type=r.match_type,
                confidence=r.confidence,
            )
            for r in google_summary.results
        ],
    )

    # 10. Map Brands to Output Schemas
    all_brand_schemas = [_map_brand_to_schema(b) for b in all_brands]
    target_brand_schema = _map_brand_to_schema(target_brand) if target_brand else None
    competitor_schemas = [_map_brand_to_schema(b) for b in competitors[:10]]

    # 11. Metadata
    metadata = RequestMetadataSchema(
        query=request.query,
        target_brand=request.your_brand,
        website_or_domain=request.website_or_domain,
        market=request.market or "US",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    return DiagnosticResponse(
        metadata=metadata,
        ai_visibility_score=primary_score,
        visibility_label=primary_label,
        supporting_metrics=primary_metrics,
        target_brand=target_brand_schema,
        all_brands=all_brand_schemas,
        competitors=competitor_schemas,
        engine_summaries=engine_summaries,
        gap_analysis=[GapEntrySchema(**g) for g in gaps],
        google_corroboration=google_corroboration_schema,
        insights=[TypedInsightSchema(**i) for i in insights],
        raw_evidence=raw_evidence_dict,
    )


def _map_supporting_metrics(brand: Brand) -> SupportingMetricsSchema:
    """Build SupportingMetricsSchema for a Brand."""
    succ = brand.successful_engine_count
    conf = brand.configured_engine_count
    ment = brand.mentioned_engine_count

    avail_display = f"{succ}/{conf} engines"
    cov_display = f"{ment}/{succ} ({brand.mention_coverage}%)" if succ > 0 else "0/0 (0%)"

    return SupportingMetricsSchema(
        engine_availability=brand.engine_availability,
        engine_availability_display=avail_display,
        mention_coverage=brand.mention_coverage,
        mention_coverage_display=cov_display,
        median_rank=brand.median_rank,
        average_rank=brand.average_rank,
        best_rank=brand.best_rank,
        worst_rank=brand.worst_rank,
        successful_engine_count=succ,
        configured_engine_count=conf,
        mentioned_engine_count=ment,
    )


def _map_brand_to_schema(brand: Brand) -> BrandResultSchema:
    """Map internal Brand domain model to BrandResultSchema."""
    products_schema = [
        ProductEvidenceSchema(
            brand_name=p.brand_name,
            product_name=p.product_name,
            full_name=p.full_name,
            rank=p.rank,
            engine=p.engine,
        )
        for p in brand.products
    ]

    observations_schema = {
        eng: EngineObservationSchema(
            engine=obs.engine,
            status=obs.status,
            mentioned=obs.mentioned,
            best_rank=obs.best_rank,
            position_score=obs.position_score,
            products=[
                ProductEvidenceSchema(
                    brand_name=p.brand_name,
                    product_name=p.product_name,
                    full_name=p.full_name,
                    rank=p.rank,
                    engine=p.engine,
                )
                for p in obs.products
            ],
            latency_ms=obs.latency_ms,
            error_type=obs.error_type,
        )
        for eng, obs in brand.observations.items()
    }

    return BrandResultSchema(
        name=brand.name,
        normalized_name=brand.normalized_name,
        domain=brand.domain,
        ai_visibility_score=brand.ai_visibility_score,
        visibility_label=get_visibility_label(brand.ai_visibility_score, brand.mentioned_engine_count > 0),
        supporting_metrics=_map_supporting_metrics(brand),
        observations=observations_schema,
        products=products_schema,
    )
