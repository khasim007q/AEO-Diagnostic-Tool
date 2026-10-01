# test_segmentation.py
"""Tests for brand vs product segmentation.

Covers heuristic splitting, known brand patterns, single-word brands,
edge cases, and international naming conventions.
"""
import pytest
from app.services.parser_service import (
    parse_llm_response,
    _extract_brand_from_product,
)


class TestJsonBasedSegmentation:
    """Tests for segmentation when LLM provides both brand and product."""

    def test_explicit_brand_and_product(self):
        text = '[{"rank": 1, "brand": "Optimum Nutrition", "product": "Gold Standard 100% Whey"}]'
        result = parse_llm_response(text)
        assert result[0]["brand"] == "Optimum Nutrition"
        assert result[0]["product"] == "Gold Standard 100% Whey"

    def test_brand_missing_product_present(self):
        """When brand is empty, it should be extracted from product."""
        text = '[{"rank": 1, "brand": "", "product": "Nike Air Max 90"}]'
        result = parse_llm_response(text)
        assert result[0]["brand"] != ""
        assert result[0]["product"] == "Nike Air Max 90"

    def test_product_missing_brand_present(self):
        """When product is missing, brand is used as product too."""
        text = '[{"rank": 1, "brand": "Apple", "product": ""}]'
        result = parse_llm_response(text)
        assert result[0]["brand"] == "Apple"
        assert result[0]["product"] == "Apple"

    def test_both_missing_skipped(self):
        text = '[{"rank": 1, "brand": "", "product": ""}, {"rank": 2, "brand": "Test", "product": "Test Pro"}]'
        result = parse_llm_response(text)
        assert len(result) == 1
        assert result[0]["brand"] == "Test"


class TestHeuristicSplitting:
    """Tests for the brand extraction heuristic."""

    def test_two_word_brand(self):
        assert _extract_brand_from_product("Optimum Nutrition Gold Standard") == "Optimum Nutrition"

    def test_single_word_brand(self):
        assert _extract_brand_from_product("Apple") == "Apple"

    def test_brand_is_product_name(self):
        """When brand and product are the same single entity."""
        assert _extract_brand_from_product("Nike") == "Nike"

    def test_three_word_product(self):
        result = _extract_brand_from_product("Samsung Galaxy S24")
        assert result in ["Samsung", "Samsung Galaxy"]

    def test_product_indicator_word(self):
        """Word 2 is a product indicator, so brand is word 1 only."""
        result = _extract_brand_from_product("BSN SYNTHA-6 Edge")
        assert result == "BSN"

    def test_long_compound_name(self):
        result = _extract_brand_from_product(
            "Nature Made Wellblends Calm & Relax Magnesium Supplement"
        )
        assert result in ["Nature Made", "Nature"]

    def test_empty_string(self):
        assert _extract_brand_from_product("") == ""

    def test_single_character(self):
        assert _extract_brand_from_product("A") == "A"

    def test_two_words_total(self):
        assert _extract_brand_from_product("Samsung Galaxy") == "Samsung Galaxy"

    def test_product_name_with_numbers(self):
        result = _extract_brand_from_product("iPhone 15 Pro Max")
        assert result in ["iPhone 15", "iPhone"]

    def test_product_name_with_special_chars(self):
        result = _extract_brand_from_product("GNC Pro Performance 100% Whey")
        assert result in ["GNC", "GNC Pro"]


class TestRegexFallbackSegmentation:
    """Tests for brand extraction from regex-parsed results."""

    def test_numbered_list_extracts_brand(self):
        text = (
            "1. Samsung Galaxy S24 Ultra - Best Android\n"
            "2. Apple iPhone 15 Pro - Best iOS\n"
            "3. Google Pixel 8 Pro - Best Camera"
        )
        result = parse_llm_response(text)
        assert len(result) == 3
        # Each result should have a brand extracted
        for item in result:
            assert item["brand"] != ""
            assert item["product"] != ""

    def test_bold_markdown_extracts_brand(self):
        text = (
            "**Samsung Galaxy S24** is the best phone.\n"
            "**Apple iPhone 15** is great too.\n"
            "**Google Pixel 8** has the best camera."
        )
        result = parse_llm_response(text)
        assert len(result) >= 3
        for item in result:
            assert item["brand"] != ""
