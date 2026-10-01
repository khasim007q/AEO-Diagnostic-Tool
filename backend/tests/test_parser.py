# test_parser.py
"""Comprehensive tests for the parser service.

Covers JSON parsing, truncated recovery, regex fallback,
special characters, edge cases, and brand/product segmentation.
"""
import pytest
from app.services.parser_service import (
    parse_llm_response,
    _parse_json,
    _extract_brands_regex,
    _extract_brand_from_product,
    _clean_brand_name,
    _is_valid_brand,
)


class TestValidJsonParsing:
    """Tests for well-formed JSON input."""

    def test_standard_json_with_brand_and_product(self, valid_json_response):
        result = parse_llm_response(valid_json_response)
        assert len(result) == 5
        assert result[0]["brand"] == "Optimum Nutrition"
        assert result[0]["product"] == "Optimum Nutrition Gold Standard 100% Whey"
        assert result[0]["rank"] == 1

    def test_old_format_json_brand_only(self, old_format_json_response):
        result = parse_llm_response(old_format_json_response)
        assert len(result) == 3
        # When only "brand" key exists, product should equal brand
        assert result[0]["product"] == "Optimum Nutrition Gold Standard 100% Whey"

    def test_json_preserves_special_characters(self, special_chars_json):
        result = parse_llm_response(special_chars_json)
        assert len(result) == 3
        assert "& Relax" in result[0]["product"]
        assert "100%" in result[1]["product"]
        assert "+ Creatine" in result[2]["product"]

    def test_json_with_code_fences(self, fenced_json_response):
        result = parse_llm_response(fenced_json_response)
        assert len(result) == 5
        assert result[0]["rank"] == 1

    def test_json_with_only_json_fence(self):
        text = "```json\n" + '[{"rank": 1, "brand": "Test", "product": "Test Pro"}]' + "\n```"
        result = parse_llm_response(text)
        assert len(result) == 1

    def test_json_with_generic_fence(self):
        text = "```\n" + '[{"rank": 1, "brand": "Test", "product": "Test Pro"}]' + "\n```"
        result = parse_llm_response(text)
        assert len(result) == 1


class TestTruncatedJsonRecovery:
    """Tests for recovering from truncated/malformed JSON."""

    def test_truncated_after_first_object(self, truncated_json_response):
        result = parse_llm_response(truncated_json_response)
        assert result is not None
        assert len(result) >= 1
        assert result[0]["brand"] == "OnePlus"

    def test_truncated_mid_object(self, truncated_mid_object_response):
        result = parse_llm_response(truncated_mid_object_response)
        assert result is not None
        assert len(result) >= 2
        assert result[0]["brand"] == "Xiaomi"
        assert result[1]["brand"] == "Samsung"

    def test_truncated_no_closing_bracket(self):
        text = '[{"rank": 1, "brand": "Apple", "product": "iPhone 15 Pro"}'
        result = parse_llm_response(text)
        assert len(result) >= 1
        assert result[0]["brand"] == "Apple"

    def test_truncated_with_trailing_comma(self):
        text = '[{"rank": 1, "brand": "Test", "product": "Test Pro"},'
        result = parse_llm_response(text)
        assert len(result) >= 1


class TestProseWithJson:
    """Tests for JSON embedded in prose text."""

    def test_json_with_preamble(self, prose_with_json):
        result = parse_llm_response(prose_with_json)
        assert len(result) == 2
        assert result[0]["brand"] == "Apple"

    def test_json_with_long_preamble(self):
        text = (
            "Sure, I'd be happy to help! Based on my research, here are the "
            "best products in this category. I've carefully selected them "
            "based on quality, value, and user reviews.\n\n"
            '[{"rank": 1, "brand": "TestBrand", "product": "TestProduct"}]'
        )
        result = parse_llm_response(text)
        assert len(result) == 1
        assert result[0]["brand"] == "TestBrand"


class TestRegexFallback:
    """Tests for regex-based extraction from unstructured text."""

    def test_numbered_list(self, numbered_list_response):
        result = parse_llm_response(numbered_list_response)
        assert len(result) == 5
        assert result[0]["rank"] == 1
        # Brand should be extracted from the full name
        assert result[0]["product"] is not None

    def test_bold_markdown(self, bold_markdown_response):
        result = parse_llm_response(bold_markdown_response)
        assert len(result) >= 3

    def test_numbered_list_with_parenthesis(self):
        text = (
            "1) Samsung Galaxy S24 Ultra - Best overall\n"
            "2) iPhone 15 Pro Max - Best for iOS\n"
            "3) Google Pixel 8 Pro - Best camera"
        )
        result = parse_llm_response(text)
        assert len(result) == 3

    def test_bullet_list(self):
        text = (
            "- Samsung Galaxy S24 Ultra\n"
            "- iPhone 15 Pro Max\n"
            "- Google Pixel 8 Pro"
        )
        result = parse_llm_response(text)
        assert len(result) == 3

    def test_heading_format(self):
        text = (
            "### Samsung Galaxy S24 Ultra\nGreat phone.\n"
            "### iPhone 15 Pro Max\nAnother great phone.\n"
            "### Google Pixel 8 Pro\nBest camera."
        )
        result = parse_llm_response(text)
        assert len(result) == 3


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_string(self):
        assert parse_llm_response("") == []

    def test_none_input(self):
        assert parse_llm_response(None) == []

    def test_error_string(self):
        assert parse_llm_response("ERROR: Request timed out") == []

    def test_api_error_string(self):
        assert parse_llm_response("API ERROR (429): Rate limited") == []

    def test_random_text_no_brands(self):
        result = parse_llm_response("the quick brown fox jumped over the lazy dog")
        assert result == []

    def test_empty_json_array(self):
        result = parse_llm_response("[]")
        assert result == []

    def test_json_with_missing_brand_key(self):
        text = '[{"rank": 1, "product": "Test Product"}]'
        result = parse_llm_response(text)
        assert len(result) == 1
        # Brand should be extracted from product name
        assert result[0]["brand"] != ""

    def test_json_with_non_string_brand(self):
        text = '[{"rank": 1, "brand": 123, "product": "Test"}]'
        result = parse_llm_response(text)
        assert len(result) == 1
        assert result[0]["brand"] == "123"

    def test_json_with_non_integer_rank(self):
        text = '[{"rank": "first", "brand": "Test", "product": "Test Pro"}]'
        result = parse_llm_response(text)
        assert len(result) == 1
        assert result[0]["rank"] == 1  # Falls back to position

    def test_limits_to_5_results(self):
        items = [
            f'{{"rank": {i}, "brand": "Brand{i}", "product": "Product{i}"}}'
            for i in range(1, 9)
        ]
        text = "[" + ", ".join(items) + "]"
        result = parse_llm_response(text)
        assert len(result) == 5

    def test_json_with_extra_fields(self):
        text = '[{"rank": 1, "brand": "Test", "product": "Test Pro", "extra": "data", "score": 95}]'
        result = parse_llm_response(text)
        assert len(result) == 1
        assert result[0]["brand"] == "Test"

    def test_unicode_brand_names(self):
        text = '[{"rank": 1, "brand": "Samsung", "product": "Samsung Galaxy S24"}]'
        result = parse_llm_response(text)
        assert len(result) == 1


class TestBrandExtraction:
    """Tests for the brand-from-product extraction heuristic."""

    def test_two_word_brand_multi_word_product(self):
        result = _extract_brand_from_product("Optimum Nutrition Gold Standard 100% Whey")
        assert result == "Optimum Nutrition"

    def test_single_word_name(self):
        result = _extract_brand_from_product("Apple")
        assert result == "Apple"

    def test_two_word_name(self):
        result = _extract_brand_from_product("Samsung Galaxy")
        assert result == "Samsung Galaxy"

    def test_product_indicator_at_position_two(self):
        result = _extract_brand_from_product("BSN SYNTHA-6 Edge")
        assert result == "BSN"

    def test_empty_string(self):
        assert _extract_brand_from_product("") == ""

    def test_long_product_name(self):
        result = _extract_brand_from_product(
            "MuscleTech Nitro-Tech 100% Whey Gold Performance"
        )
        assert result in ["MuscleTech", "MuscleTech Nitro-Tech"]


class TestCleanBrandName:
    """Tests for brand name cleaning."""

    def test_trailing_asterisks(self):
        assert _clean_brand_name("BrandName**") == "BrandName"

    def test_trailing_description_with_dash(self):
        assert _clean_brand_name("BrandName - great product") == "BrandName"

    def test_trailing_description_with_colon(self):
        assert _clean_brand_name("BrandName: excellent choice") == "BrandName"

    def test_description_words(self):
        result = _clean_brand_name("BrandName is the best on the market")
        assert result == "BrandName"

    def test_preserves_hyphens_in_name(self):
        result = _clean_brand_name("SYNTHA-6 Edge")
        assert "SYNTHA-6" in result


class TestValidBrand:
    """Tests for brand name validation."""

    def test_valid_name(self):
        assert _is_valid_brand("Apple") is True

    def test_too_short(self):
        assert _is_valid_brand("AB") is False

    def test_too_long(self):
        assert _is_valid_brand("A" * 81) is False

    def test_minimum_length(self):
        assert _is_valid_brand("ABC") is True
