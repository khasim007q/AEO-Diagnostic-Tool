# test_segmentation.py
"""Tests for brand vs product segmentation and domain model separation.

Ensures that brands are ranking entities and products are supporting evidence.
Covers heuristic splitting, strict rejection of missing entities, and
proper grouping of multiple products under the same parent brand.
"""
import pytest
from app.services.parser_service import (
    parse_llm_response_detailed,
    _extract_brand_from_product,
)
from app.models.brand import Brand, ProductEvidence, EngineObservation


class TestBrandProductSegmentation:
    """Tests for separating brands from products."""

    def test_explicit_brand_and_product(self):
        text = '''{
            "recommendations": [
                {"rank": 1, "brand": "Optimum Nutrition", "product": "Gold Standard 100% Whey"},
                {"rank": 2, "brand": "Dymatize", "product": "ISO100 Hydrolyzed"},
                {"rank": 3, "brand": "BSN", "product": "Syntha-6 Edge"},
                {"rank": 4, "brand": "MuscleTech", "product": "Nitro-Tech"},
                {"rank": 5, "brand": "Cellucor", "product": "COR-Performance"}
            ]
        }'''
        res = parse_llm_response_detailed(text)
        assert res.status == "valid"
        assert res.recommendations[0].brand == "Optimum Nutrition"
        assert res.recommendations[0].product == "Gold Standard 100% Whey"

    def test_strict_reject_empty_brand_in_structured_json(self):
        """Strict parser rejects malformed recommendation with empty brand."""
        text = '''{
            "recommendations": [
                {"rank": 1, "brand": "", "product": "Nike Air Max 90"}
            ]
        }'''
        res = parse_llm_response_detailed(text)
        assert res.status == "invalid"
        assert any("empty or non-string brand" in e for e in res.errors)

    def test_strict_reject_empty_product_in_structured_json(self):
        """Strict parser rejects malformed recommendation with empty product."""
        text = '''{
            "recommendations": [
                {"rank": 1, "brand": "Apple", "product": ""}
            ]
        }'''
        res = parse_llm_response_detailed(text)
        assert res.status == "invalid"
        assert any("empty or non-string product" in e for e in res.errors)


class TestHeuristicSplittingForFallback:
    """Tests for the brand extraction heuristic used in regex fallback."""

    def test_two_word_brand(self):
        assert _extract_brand_from_product("Optimum Nutrition Gold Standard") == "Optimum Nutrition"

    def test_single_word_brand(self):
        assert _extract_brand_from_product("Apple") == "Apple"

    def test_brand_is_product_name(self):
        assert _extract_brand_from_product("Nike") == "Nike"

    def test_product_indicator_word(self):
        assert _extract_brand_from_product("BSN SYNTHA-6 Edge") == "BSN"

    def test_empty_string(self):
        assert _extract_brand_from_product("") == ""


class TestDomainModelHierarchy:
    """Tests that products are evidence while brands are scored entities."""

    def test_brand_aggregates_multiple_products(self):
        b = Brand(name="Nike", normalized_name="nike")
        obs = EngineObservation(
            engine="GPT-5-mini",
            status="success",
            mentioned=True,
            best_rank=1,
            position_score=1.00,
            products=[
                ProductEvidence(brand_name="Nike", product_name="Nike Pegasus 40", full_name="Nike Pegasus 40", rank=1, engine="GPT-5-mini"),
                ProductEvidence(brand_name="Nike", product_name="Nike Vaporfly 3", full_name="Nike Vaporfly 3", rank=4, engine="GPT-5-mini"),
            ],
            latency_ms=1200.0,
        )
        b.observations["GPT-5-mini"] = obs
        b.products.extend(obs.products)
        b.best_rank = 1

        # Brand has 2 products as evidence
        all_prods = b.products
        assert len(all_prods) == 2
        assert all_prods[0].product_name == "Nike Pegasus 40"
        assert all_prods[1].product_name == "Nike Vaporfly 3"

        # Best rank and best product
        assert b.best_rank == 1
        assert b.best_product.product_name == "Nike Pegasus 40"
