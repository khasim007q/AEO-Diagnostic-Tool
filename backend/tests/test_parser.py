# test_parser.py
"""Comprehensive tests for the parser service and strict validation.

Tests strict structured output, parser validation rules (rejecting rank 0, 6+,
duplicate ranks, empty brand/product), partial and low-confidence statuses,
and regex fallback recovery.
"""
import pytest
from app.services.parser_service import (
    parse_llm_response_detailed,
    parse_llm_response,
    ParsedRecommendation,
    ParseResult,
    _extract_brand_from_product,
    _clean_brand_name,
)


class TestStrictJsonValidation:
    """Tests for structured output with object wrapper or array."""

    def test_valid_five_recommendations_object_wrapper(self):
        text = '''{
            "recommendations": [
                {"rank": 1, "brand": "Nike", "product": "Nike Air Zoom Pegasus 40"},
                {"rank": 2, "brand": "Adidas", "product": "Adidas Ultraboost Light"},
                {"rank": 3, "brand": "Brooks", "product": "Brooks Ghost 15"},
                {"rank": 4, "brand": "Asics", "product": "Asics Gel-Nimbus 25"},
                {"rank": 5, "brand": "Hoka", "product": "Hoka Clifton 9"}
            ]
        }'''
        res = parse_llm_response_detailed(text)
        assert res.status == "valid"
        assert len(res.recommendations) == 5
        assert res.recommendations[0].brand == "Nike"
        assert res.recommendations[0].rank == 1
        assert res.recommendations[4].brand == "Hoka"
        assert res.recommendations[4].rank == 5

    def test_valid_five_recommendations_direct_array(self):
        text = '''[
            {"rank": 1, "brand": "Nike", "product": "Nike Air Zoom Pegasus 40"},
            {"rank": 2, "brand": "Adidas", "product": "Adidas Ultraboost Light"},
            {"rank": 3, "brand": "Brooks", "product": "Brooks Ghost 15"},
            {"rank": 4, "brand": "Asics", "product": "Asics Gel-Nimbus 25"},
            {"rank": 5, "brand": "Hoka", "product": "Hoka Clifton 9"}
        ]'''
        res = parse_llm_response_detailed(text)
        assert res.status == "valid"
        assert len(res.recommendations) == 5

    def test_markdown_code_fences_stripped(self):
        inner = '''{
            "recommendations": [
                {"rank": 1, "brand": "Nike", "product": "Nike Pegasus"},
                {"rank": 2, "brand": "Adidas", "product": "Adidas Ultraboost"},
                {"rank": 3, "brand": "Brooks", "product": "Brooks Ghost"},
                {"rank": 4, "brand": "Asics", "product": "Asics Nimbus"},
                {"rank": 5, "brand": "Hoka", "product": "Hoka Clifton"}
            ]
        }'''
        fenced = f"```json\n{inner}\n```"
        res = parse_llm_response_detailed(fenced)
        assert res.status == "valid"
        assert len(res.recommendations) == 5

    def test_json_with_preamble_and_postamble(self):
        text = (
            "Here is the list of top running shoes:\n\n"
            '{"recommendations": ['
            '{"rank": 1, "brand": "Nike", "product": "Nike Pegasus"},'
            '{"rank": 2, "brand": "Adidas", "product": "Adidas Ultraboost"},'
            '{"rank": 3, "brand": "Brooks", "product": "Brooks Ghost"},'
            '{"rank": 4, "brand": "Asics", "product": "Asics Nimbus"},'
            '{"rank": 5, "brand": "Hoka", "product": "Hoka Clifton"}'
            ']}\n\nHope this helps your search!'
        )
        res = parse_llm_response_detailed(text)
        assert res.status == "valid"
        assert len(res.recommendations) == 5


class TestParserStrictRejections:
    """Tests that malformed ranking data is strictly rejected rather than silently repaired."""

    def test_reject_rank_zero(self):
        text = '''{
            "recommendations": [
                {"rank": 0, "brand": "Nike", "product": "Nike Pegasus"},
                {"rank": 2, "brand": "Adidas", "product": "Adidas Ultraboost"},
                {"rank": 3, "brand": "Brooks", "product": "Brooks Ghost"},
                {"rank": 4, "brand": "Asics", "product": "Asics Nimbus"},
                {"rank": 5, "brand": "Hoka", "product": "Hoka Clifton"}
            ]
        }'''
        res = parse_llm_response_detailed(text)
        assert res.status == "invalid"
        assert any("out-of-bounds rank 0" in e for e in res.errors)

    def test_reject_rank_six_or_higher(self):
        text = '''{
            "recommendations": [
                {"rank": 1, "brand": "Nike", "product": "Nike Pegasus"},
                {"rank": 2, "brand": "Adidas", "product": "Adidas Ultraboost"},
                {"rank": 3, "brand": "Brooks", "product": "Brooks Ghost"},
                {"rank": 4, "brand": "Asics", "product": "Asics Nimbus"},
                {"rank": 6, "brand": "Hoka", "product": "Hoka Clifton"}
            ]
        }'''
        res = parse_llm_response_detailed(text)
        assert res.status == "invalid"
        assert any("out-of-bounds rank 6" in e for e in res.errors)

    def test_reject_duplicate_ranks(self):
        text = '''{
            "recommendations": [
                {"rank": 1, "brand": "Nike", "product": "Nike Pegasus"},
                {"rank": 1, "brand": "Adidas", "product": "Adidas Ultraboost"},
                {"rank": 3, "brand": "Brooks", "product": "Brooks Ghost"},
                {"rank": 4, "brand": "Asics", "product": "Asics Nimbus"},
                {"rank": 5, "brand": "Hoka", "product": "Hoka Clifton"}
            ]
        }'''
        res = parse_llm_response_detailed(text)
        assert res.status == "invalid"
        assert any("Duplicate rank 1" in e for e in res.errors)

    def test_reject_empty_brand(self):
        text = '''{
            "recommendations": [
                {"rank": 1, "brand": "", "product": "Nike Pegasus"},
                {"rank": 2, "brand": "Adidas", "product": "Adidas Ultraboost"},
                {"rank": 3, "brand": "Brooks", "product": "Brooks Ghost"},
                {"rank": 4, "brand": "Asics", "product": "Asics Nimbus"},
                {"rank": 5, "brand": "Hoka", "product": "Hoka Clifton"}
            ]
        }'''
        res = parse_llm_response_detailed(text)
        assert res.status == "invalid"
        assert any("empty or non-string brand" in e for e in res.errors)

    def test_reject_empty_product(self):
        text = '''{
            "recommendations": [
                {"rank": 1, "brand": "Nike", "product": ""},
                {"rank": 2, "brand": "Adidas", "product": "Adidas Ultraboost"},
                {"rank": 3, "brand": "Brooks", "product": "Brooks Ghost"},
                {"rank": 4, "brand": "Asics", "product": "Asics Nimbus"},
                {"rank": 5, "brand": "Hoka", "product": "Hoka Clifton"}
            ]
        }'''
        res = parse_llm_response_detailed(text)
        assert res.status == "invalid"
        assert any("empty or non-string product" in e for e in res.errors)

    def test_reject_non_integer_rank(self):
        text = '''{
            "recommendations": [
                {"rank": "1", "brand": "Nike", "product": "Nike Pegasus"},
                {"rank": 2, "brand": "Adidas", "product": "Adidas Ultraboost"},
                {"rank": 3, "brand": "Brooks", "product": "Brooks Ghost"},
                {"rank": 4, "brand": "Asics", "product": "Asics Nimbus"},
                {"rank": 5, "brand": "Hoka", "product": "Hoka Clifton"}
            ]
        }'''
        res = parse_llm_response_detailed(text)
        assert res.status == "invalid"
        assert any("non-integer rank" in e for e in res.errors)

    def test_partial_status_when_valid_subset_is_present(self):
        # Missing rank 4 and 5, but 1, 2, 3 are valid and non-duplicate
        text = '''{
            "recommendations": [
                {"rank": 1, "brand": "Nike", "product": "Nike Pegasus"},
                {"rank": 2, "brand": "Adidas", "product": "Adidas Ultraboost"},
                {"rank": 3, "brand": "Brooks", "product": "Brooks Ghost"}
            ]
        }'''
        res = parse_llm_response_detailed(text)
        assert res.status == "partial"
        assert len(res.recommendations) == 3
        assert any("Missing ranks" in e for e in res.errors)


class TestRegexFallbackRecovery:
    """Tests for unstructured text parsed via low-confidence regex fallback."""

    def test_numbered_list_falls_back_to_low_confidence(self):
        text = (
            "1. Nike Air Zoom Pegasus 40 - Best overall daily runner\n"
            "2. Adidas Ultraboost Light - Great cushion\n"
            "3. Brooks Ghost 15 - Balanced feel\n"
            "4. Asics Gel-Nimbus 25 - Max plush\n"
            "5. Hoka Clifton 9 - Lightweight comfort\n"
        )
        res = parse_llm_response_detailed(text)
        assert res.status == "low_confidence"
        assert len(res.recommendations) == 5
        assert res.recommendations[0].rank == 1
        assert res.recommendations[0].brand == "Nike"
        assert "Pegasus" in res.recommendations[0].product

    def test_parenthesis_numbered_list(self):
        text = (
            "1) Apple iPhone 15 Pro\n"
            "2) Samsung Galaxy S24 Ultra\n"
            "3) Google Pixel 8 Pro\n"
        )
        res = parse_llm_response_detailed(text)
        assert res.status == "low_confidence"
        assert len(res.recommendations) == 3
        assert res.recommendations[0].rank == 1
        assert res.recommendations[0].brand == "Apple"


class TestEdgeCasesAndCleaners:
    """Tests for edge cases, empty input, errors, and string cleaning."""

    def test_empty_input(self):
        res = parse_llm_response_detailed("")
        assert res.status == "invalid"
        assert len(res.recommendations) == 0

    def test_none_input(self):
        res = parse_llm_response_detailed(None)
        assert res.status == "invalid"

    def test_error_string_input(self):
        res = parse_llm_response_detailed("ERROR: Request timed out after 30s")
        assert res.status == "invalid"

    def test_api_error_string_input(self):
        res = parse_llm_response_detailed("API ERROR: Rate limit 429")
        assert res.status == "invalid"

    def test_arbitrary_unstructured_prose(self):
        res = parse_llm_response_detailed("No recommendations available for this query.")
        assert res.status == "invalid"

    def test_special_characters_preserved(self):
        text = '''{
            "recommendations": [
                {"rank": 1, "brand": "Optimum Nutrition", "product": "Gold Standard 100% Whey & BCAA"},
                {"rank": 2, "brand": "MuscleTech", "product": "Nitro-Tech + Creatine"},
                {"rank": 3, "brand": "BSN", "product": "SYNTHA-6 Edge"},
                {"rank": 4, "brand": "Dymatize", "product": "ISO100 Hydrolyzed"},
                {"rank": 5, "brand": "Cellucor", "product": "COR-Performance"}
            ]
        }'''
        res = parse_llm_response_detailed(text)
        assert res.status == "valid"
        assert "100%" in res.recommendations[0].product
        assert "+" in res.recommendations[1].product
        assert "-" in res.recommendations[2].product

    def test_clean_brand_name_removes_markdown_and_trailing_descriptions(self):
        assert _clean_brand_name("**Nike**") == "Nike"
        assert _clean_brand_name("Nike - Best running shoe") == "Nike"
        assert _clean_brand_name("Adidas: Top performance") == "Adidas"

    def test_extract_brand_from_product(self):
        assert _extract_brand_from_product("Nike Air Zoom Pegasus") == "Nike"
        assert _extract_brand_from_product("Apple iPhone 15 Pro") == "Apple"
        assert _extract_brand_from_product("") == ""

    def test_legacy_helper_parse_llm_response(self):
        text = '''{
            "recommendations": [
                {"rank": 1, "brand": "Nike", "product": "Pegasus"},
                {"rank": 2, "brand": "Adidas", "product": "Ultraboost"}
            ]
        }'''
        dicts = parse_llm_response(text)
        assert isinstance(dicts, list)
        assert len(dicts) == 2
        assert dicts[0]["rank"] == 1
        assert dicts[0]["brand"] == "Nike"
