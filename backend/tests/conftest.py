# conftest.py
import pytest
from typing import Dict, Any
from app.services.llm_service import EngineExecutionResult
from app.services.parser_service import ParseResult, ParsedRecommendation
from app.services.serp_service import GoogleCorroborationSummary, GoogleCorroborationResult


@pytest.fixture
def perfect_five_recommendations():
    """Valid 5-item recommendations structure."""
    return [
        ParsedRecommendation(rank=1, brand="Nike", product="Nike Air Zoom Pegasus 40"),
        ParsedRecommendation(rank=2, brand="Adidas", product="Adidas Ultraboost Light"),
        ParsedRecommendation(rank=3, brand="Brooks", product="Brooks Ghost 15"),
        ParsedRecommendation(rank=4, brand="Asics", product="Asics Gel-Nimbus 25"),
        ParsedRecommendation(rank=5, brand="Hoka", product="Hoka Clifton 9"),
    ]


@pytest.fixture
def multi_product_same_brand_recommendations():
    """Engine returns multiple products for the same brand (Nike Pegasus #1 and Nike Vaporfly #4)."""
    return [
        ParsedRecommendation(rank=1, brand="Nike", product="Nike Air Zoom Pegasus 40"),
        ParsedRecommendation(rank=2, brand="Adidas", product="Adidas Ultraboost Light"),
        ParsedRecommendation(rank=3, brand="Brooks", product="Brooks Ghost 15"),
        ParsedRecommendation(rank=4, brand="Nike", product="Nike Vaporfly 3"),
        ParsedRecommendation(rank=5, brand="Hoka", product="Hoka Clifton 9"),
    ]


@pytest.fixture
def mock_successful_engine_results(perfect_five_recommendations) -> Dict[str, EngineExecutionResult]:
    """3 successful engines with slight variations in ranking."""
    gpt_recs = [
        ParsedRecommendation(rank=1, brand="Nike", product="Nike Pegasus 40"),
        ParsedRecommendation(rank=2, brand="Adidas", product="Adidas Ultraboost"),
        ParsedRecommendation(rank=3, brand="Brooks", product="Brooks Ghost 15"),
        ParsedRecommendation(rank=4, brand="Asics", product="Asics Nimbus"),
        ParsedRecommendation(rank=5, brand="Hoka", product="Hoka Clifton"),
    ]
    claude_recs = [
        ParsedRecommendation(rank=1, brand="Brooks", product="Brooks Ghost 15"),
        ParsedRecommendation(rank=2, brand="Nike", product="Nike Pegasus 40"),
        ParsedRecommendation(rank=3, brand="Saucony", product="Saucony Ride"),
        ParsedRecommendation(rank=4, brand="New Balance", product="New Balance 1080"),
        ParsedRecommendation(rank=5, brand="Asics", product="Asics Nimbus"),
    ]
    gemini_recs = [
        ParsedRecommendation(rank=1, brand="Adidas", product="Adidas Ultraboost"),
        ParsedRecommendation(rank=2, brand="Nike", product="Nike Pegasus 40"),
        ParsedRecommendation(rank=3, brand="Hoka", product="Hoka Clifton"),
        ParsedRecommendation(rank=4, brand="Puma", product="Puma Deviate"),
        ParsedRecommendation(rank=5, brand="Mizuno", product="Mizuno Wave Rider"),
    ]

    return {
        "GPT-5-mini": EngineExecutionResult(
            engine="GPT-5-mini",
            status="success",
            latency_ms=120.0,
            attempts=1,
            parse_result=ParseResult(status="valid", recommendations=gpt_recs),
        ),
        "Claude Sonnet 4": EngineExecutionResult(
            engine="Claude Sonnet 4",
            status="success",
            latency_ms=210.0,
            attempts=1,
            parse_result=ParseResult(status="valid", recommendations=claude_recs),
        ),
        "Gemini 2.5 Flash": EngineExecutionResult(
            engine="Gemini 2.5 Flash",
            status="success",
            latency_ms=180.0,
            attempts=1,
            parse_result=ParseResult(status="valid", recommendations=gemini_recs),
        ),
    }


@pytest.fixture
def mock_google_summary_success() -> GoogleCorroborationSummary:
    """Successful Google search corroboration with target brand present."""
    results = [
        GoogleCorroborationResult(
            rank=1,
            title="Official Nike Running Shoes & Gear",
            snippet="Shop the latest running shoes from Nike with free shipping.",
            url="https://www.nike.com/running",
            domain="nike.com",
            title_match=True,
            snippet_match=True,
            domain_match=True,
            normalized_brand_match=True,
            match_type="domain",
            confidence=1.0,
        ),
        GoogleCorroborationResult(
            rank=2,
            title="Best Running Shoes of 2024 - Runner's World",
            snippet="We tested the top running shoes from Nike, Adidas, and Brooks.",
            url="https://runnersworld.com/shoes",
            domain="runnersworld.com",
            title_match=False,
            snippet_match=True,
            domain_match=False,
            normalized_brand_match=True,
            match_type="snippet",
            confidence=0.60,
        ),
    ]
    return GoogleCorroborationSummary(
        status="success",
        total_results=2,
        brand_found=True,
        best_google_rank=1,
        results=results,
    )
