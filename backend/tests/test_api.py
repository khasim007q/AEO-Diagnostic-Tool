# test_api.py
"""Tests for the FastAPI API endpoints.

Uses TestClient with mocked services for integration testing.
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_health_is_get_only(self):
        response = client.post("/health")
        assert response.status_code == 405


class TestDiagnosticEndpoint:
    """Tests for the /api/v1/diagnostic endpoint."""

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

    @patch("app.api.router.query_llms")
    @patch("app.api.router.search_google")
    def test_valid_request_returns_200(self, mock_serp, mock_llms):
        mock_llms.return_value = {
            "GPT-5-mini": {
                "raw_text": '[{"rank": 1, "brand": "TestBrand", "product": "TestProduct"}]',
                "parsed_count": 0,
                "error": None,
            }
        }
        mock_serp.return_value = []

        response = client.post(
            "/api/v1/diagnostic",
            json={"query": "best whey protein"},
        )
        assert response.status_code == 200

        data = response.json()
        assert "grade" in data
        assert "all_brands" in data
        assert "insights" in data
        assert "llm_names" in data
        assert "google_results" in data

    @patch("app.api.router.query_llms")
    @patch("app.api.router.search_google")
    def test_response_schema_structure(self, mock_serp, mock_llms):
        mock_llms.return_value = {
            "GPT-5-mini": {
                "raw_text": '[{"rank": 1, "brand": "A", "product": "A Pro"}, {"rank": 2, "brand": "B", "product": "B Pro"}]',
                "parsed_count": 0,
                "error": None,
            }
        }
        mock_serp.return_value = []

        response = client.post(
            "/api/v1/diagnostic",
            json={"query": "best protein powder"},
        )
        data = response.json()

        # Verify grade structure
        assert "grade" in data["grade"]
        assert "label" in data["grade"]
        assert "score" in data["grade"]
        assert "max_score" in data["grade"]

        # Verify brands structure
        assert isinstance(data["all_brands"], list)
        if data["all_brands"]:
            brand = data["all_brands"][0]
            assert "name" in brand
            assert "products" in brand
            assert "total_score" in brand

    @patch("app.api.router.query_llms")
    @patch("app.api.router.search_google")
    def test_with_brand_name(self, mock_serp, mock_llms):
        mock_llms.return_value = {
            "GPT-5-mini": {
                "raw_text": '[{"rank": 1, "brand": "MyBrand", "product": "MyBrand Pro"}]',
                "parsed_count": 0,
                "error": None,
            }
        }
        mock_serp.return_value = []

        response = client.post(
            "/api/v1/diagnostic",
            json={"query": "best product", "your_brand": "MyBrand"},
        )
        data = response.json()
        assert data["your_brand"] is not None
        assert data["your_brand"]["name"] == "MyBrand"

    @patch("app.api.router.query_llms")
    @patch("app.api.router.search_google")
    def test_brand_not_found(self, mock_serp, mock_llms):
        mock_llms.return_value = {
            "GPT-5-mini": {
                "raw_text": '[{"rank": 1, "brand": "OtherBrand", "product": "OtherProduct"}]',
                "parsed_count": 0,
                "error": None,
            }
        }
        mock_serp.return_value = []

        response = client.post(
            "/api/v1/diagnostic",
            json={"query": "best product", "your_brand": "MyBrand"},
        )
        data = response.json()
        assert data["your_brand"] is None
        assert data["grade"]["grade"] == "F"

    @patch("app.api.router.query_llms")
    @patch("app.api.router.search_google")
    def test_all_llms_error(self, mock_serp, mock_llms):
        """All LLMs return errors, should still return a valid response."""
        mock_llms.return_value = {
            "GPT-5-mini": {"raw_text": "ERROR: timeout", "parsed_count": 0, "error": "timeout"},
            "Claude Sonnet": {"raw_text": "ERROR: timeout", "parsed_count": 0, "error": "timeout"},
        }
        mock_serp.return_value = []

        response = client.post(
            "/api/v1/diagnostic",
            json={"query": "best protein"},
        )
        data = response.json()
        assert response.status_code == 200
        assert data["all_brands"] == []
        assert data["grade"]["grade"] == "F"

    def test_invalid_json_body(self):
        response = client.post(
            "/api/v1/diagnostic",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422
