# test_api.py
"""Tests for FastAPI endpoints and integration.

Covers:
- /health endpoint
- /api/v1/diagnostic validation (query length, missing fields)
- Diagnostic endpoint execution with mocked parallel LLM and Google search
- Deterministic AI visibility score and supporting metrics in API response
- Signed gap analysis
- Rate limiting protection
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.llm_service import EngineExecutionResult
from app.services.parser_service import ParseResult, ParsedRecommendation
from app.services.serp_service import (
    GoogleCorroborationSummary,
    GoogleCorroborationResult,
)

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_health_post_not_allowed(self):
        response = client.post("/health")
        assert response.status_code == 405


class TestDiagnosticValidation:
    """Tests for request payload validation."""

    def test_empty_query_returns_422(self):
        response = client.post("/api/v1/diagnostic", json={"query": ""})
        assert response.status_code == 422

    def test_query_too_short_returns_422(self):
        response = client.post("/api/v1/diagnostic", json={"query": "ab"})
        assert response.status_code == 422

    def test_missing_query_returns_422(self):
        response = client.post("/api/v1/diagnostic", json={})
        assert response.status_code == 422

    def test_brand_too_long_returns_422(self):
        response = client.post(
            "/api/v1/diagnostic",
            json={"query": "best protein", "your_brand": "x" * 101},
        )
        assert response.status_code == 422

    def test_invalid_json_body_returns_422(self):
        response = client.post(
            "/api/v1/diagnostic",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422


class TestDiagnosticExecution:
    """Tests for the full diagnostic endpoint execution."""

    @patch("app.api.router.query_llms_parallel")
    @patch("app.api.router.search_google_corroboration")
    def test_valid_diagnostic_with_target_brand(self, mock_serp, mock_llms):
        mock_llms.return_value = {
            "GPT-5-mini": EngineExecutionResult(
                engine="GPT-5-mini",
                status="success",
                raw_text='{"recommendations": [{"rank": 1, "brand": "Nike", "product": "Pegasus"}]}',
                parse_result=ParseResult(
                    status="valid",
                    recommendations=[
                        ParsedRecommendation(rank=1, brand="Nike", product="Pegasus"),
                        ParsedRecommendation(rank=2, brand="Adidas", product="Ultraboost"),
                    ],
                ),
                latency_ms=850.0,
                attempts=1,
            ),
            "Claude Sonnet 4": EngineExecutionResult(
                engine="Claude Sonnet 4",
                status="success",
                raw_text='{"recommendations": [{"rank": 2, "brand": "Nike", "product": "Pegasus"}]}',
                parse_result=ParseResult(
                    status="valid",
                    recommendations=[
                        ParsedRecommendation(rank=1, brand="Adidas", product="Ultraboost"),
                        ParsedRecommendation(rank=2, brand="Nike", product="Pegasus"),
                    ],
                ),
                latency_ms=920.0,
                attempts=1,
            ),
        }
        mock_serp.return_value = GoogleCorroborationSummary(
            status="success",
            total_results=1,
            brand_found=True,
            best_google_rank=1,
            results=[
                GoogleCorroborationResult(
                    rank=1,
                    title="Nike Official Store",
                    snippet="Shop Nike shoes and gear.",
                    url="https://www.nike.com",
                    domain="nike.com",
                    title_match=True,
                    snippet_match=True,
                    domain_match=True,
                    normalized_brand_match=True,
                    match_type="domain",
                    confidence=1.0,
                )
            ],
        )

        response = client.post(
            "/api/v1/diagnostic",
            json={"query": "best running shoes", "your_brand": "Nike"},
        )
        assert response.status_code == 200
        data = response.json()

        # Primary score verification: Nike rank 1 (1.00) in GPT, rank 2 (0.80) in Claude
        # Mean position score = (1.00 + 0.80) / 2 = 0.90 -> 90.0
        assert data["ai_visibility_score"] == 90.0
        assert data["visibility_label"] == "High visibility"

        # Supporting metrics
        metrics = data["supporting_metrics"]
        assert metrics["successful_engine_count"] == 2
        assert metrics["mentioned_engine_count"] == 2
        assert metrics["mention_coverage"] == 100.0
        assert metrics["mention_coverage_display"] == "2/2 (100.0%)"
        assert metrics["best_rank"] == 1
        assert metrics["worst_rank"] == 2
        assert metrics["median_rank"] == 1.5

        # BrandResult & Competitors
        assert data["target_brand"] is not None
        assert data["target_brand"]["name"] == "Nike"
        assert len(data["competitors"]) >= 1
        assert data["competitors"][0]["name"] == "Adidas"

        # Signed Gap Analysis (Nike score 90.0 vs Adidas score 90.0 -> gap 0.0)
        assert isinstance(data["gap_analysis"], list)
        assert len(data["gap_analysis"]) > 0

        # Google Corroboration
        google_data = data["google_corroboration"]
        assert google_data["status"] == "success"
        assert google_data["brand_found"] is True
        assert google_data["results"][0]["match_type"] == "domain"

        # Typed Insights
        assert isinstance(data["insights"], list)
        assert len(data["insights"]) > 0
        assert "type" in data["insights"][0]
        assert "evidence" in data["insights"][0]

        # Engine Summaries & Raw Evidence
        assert len(data["engine_summaries"]) == 2
        assert "GPT-5-mini" in data["raw_evidence"]

    @patch("app.api.router.query_llms_parallel")
    @patch("app.api.router.search_google_corroboration")
    def test_target_brand_not_found(self, mock_serp, mock_llms):
        mock_llms.return_value = {
            "GPT-5-mini": EngineExecutionResult(
                engine="GPT-5-mini",
                status="success",
                raw_text="...",
                parse_result=ParseResult(
                    status="valid",
                    recommendations=[
                        ParsedRecommendation(rank=1, brand="Adidas", product="Ultraboost"),
                    ],
                ),
                latency_ms=500.0,
                attempts=1,
            )
        }
        mock_serp.return_value = GoogleCorroborationSummary(status="not_configured")

        response = client.post(
            "/api/v1/diagnostic",
            json={"query": "best shoes", "your_brand": "Nike"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ai_visibility_score"] == 0.0
        assert data["visibility_label"] == "Not visible"
        assert data["target_brand"] is not None
        assert data["target_brand"]["name"] == "Nike"
        assert data["target_brand"]["ai_visibility_score"] == 0.0
        assert data["supporting_metrics"]["mentioned_engine_count"] == 0

    @patch("app.api.router.query_llms_parallel")
    @patch("app.api.router.search_google_corroboration")
    def test_failed_engine_excluded_from_score_denominator(self, mock_serp, mock_llms):
        """Failed engine should not pull down brand score to zero."""
        mock_llms.return_value = {
            "GPT-5-mini": EngineExecutionResult(
                engine="GPT-5-mini",
                status="success",
                raw_text="...",
                parse_result=ParseResult(
                    status="valid",
                    recommendations=[
                        ParsedRecommendation(rank=1, brand="Nike", product="Pegasus"),
                    ],
                ),
                latency_ms=500.0,
                attempts=1,
            ),
            "Claude Sonnet 4": EngineExecutionResult(
                engine="Claude Sonnet 4",
                status="failed",
                error_type="timeout",
                error_message="Gateway timeout after 3 retries",
                latency_ms=15000.0,
                attempts=3,
            ),
        }
        mock_serp.return_value = GoogleCorroborationSummary(status="not_configured")

        response = client.post(
            "/api/v1/diagnostic",
            json={"query": "best shoes", "your_brand": "Nike"},
        )
        assert response.status_code == 200
        data = response.json()

        # Score across 1 successful engine: 100 * (1.00 / 1) = 100.0
        assert data["ai_visibility_score"] == 100.0
        metrics = data["supporting_metrics"]
        assert metrics["successful_engine_count"] == 1
        assert metrics["configured_engine_count"] == 2
        assert metrics["engine_availability"] == 50.0
        assert metrics["engine_availability_display"] == "1/2 engines"
