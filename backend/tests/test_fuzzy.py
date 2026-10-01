# test_fuzzy.py
"""Comprehensive tests for fuzzy matching utilities.

Covers exact matches, case sensitivity, special characters,
anti-merge digit logic, edge cases, and sliding window text search.
"""
import pytest
from app.utils.fuzzy import is_same_brand, is_same_product, fuzzy_find_in_text


class TestIsSameBrand:
    """Tests for brand name comparison."""

    def test_exact_match(self):
        assert is_same_brand("Apple", "Apple") is True

    def test_case_insensitive(self):
        assert is_same_brand("apple", "APPLE") is True

    def test_with_whitespace(self):
        assert is_same_brand("Apple ", " apple") is True

    def test_similar_names(self):
        assert is_same_brand("Coca Cola", "Coca-Cola") is True

    def test_completely_different(self):
        assert is_same_brand("Apple", "Microsoft") is False

    def test_partial_match_short_vs_long(self):
        """Short brand name in a longer brand should match at lower threshold."""
        assert is_same_brand("Nike", "Nike Inc", threshold=70) is True

    def test_different_version_numbers(self):
        """Brands with different numbers should NOT match."""
        assert is_same_brand("iPhone 14", "iPhone 15") is False

    def test_same_version_numbers(self):
        """Brands with same numbers should match."""
        assert is_same_brand("iPhone 15", "iphone 15 pro") is True

    def test_empty_first(self):
        assert is_same_brand("", "Apple") is False

    def test_empty_second(self):
        assert is_same_brand("Apple", "") is False

    def test_both_empty(self):
        assert is_same_brand("", "") is False

    def test_none_first(self):
        assert is_same_brand(None, "Apple") is False

    def test_none_second(self):
        assert is_same_brand("Apple", None) is False

    def test_very_short_names(self):
        assert is_same_brand("GNC", "GNC") is True

    def test_very_long_names(self):
        name = "Optimum Nutrition Gold Standard 100% Whey Protein Powder"
        assert is_same_brand(name, name) is True

    def test_special_characters_preserved(self):
        assert is_same_brand("Nature's Best", "Nature's Best") is True

    def test_ampersand_in_name(self):
        assert is_same_brand("Tom & Jerry", "Tom and Jerry") is True

    def test_custom_threshold_strict(self):
        assert is_same_brand("Samsung", "Samsonite", threshold=95) is False

    def test_custom_threshold_lenient(self):
        assert is_same_brand("optimum", "Optimum Nutrition", threshold=60) is True


class TestIsSameProduct:
    """Tests for product name comparison."""

    def test_exact_match(self):
        assert is_same_product("iPhone 15 Pro", "iPhone 15 Pro") is True

    def test_case_insensitive(self):
        assert is_same_product("iphone 15", "iPhone 15") is True

    def test_different_products_same_brand(self):
        """Different products from the same brand should NOT merge."""
        assert is_same_product("iPhone 15", "iPhone 15 Pro Max") is False

    def test_different_version_numbers(self):
        """Products with different version numbers should NOT merge."""
        assert is_same_product("iPhone 14 Pro", "iPhone 15 Pro") is False

    def test_word_order_independent(self):
        """token_sort_ratio handles word order differences."""
        assert is_same_product(
            "Gold Standard Whey Protein",
            "Whey Protein Gold Standard",
        ) is True

    def test_empty_first(self):
        assert is_same_product("", "Test") is False

    def test_empty_second(self):
        assert is_same_product("Test", "") is False

    def test_none_handling(self):
        assert is_same_product(None, "Test") is False
        assert is_same_product("Test", None) is False

    def test_completely_different_products(self):
        assert is_same_product("iPhone 15", "Galaxy S24") is False

    def test_slight_variation(self):
        assert is_same_product(
            "Optimum Nutrition Gold Standard 100% Whey",
            "Optimum Nutrition Gold Standard Whey 100%",
        ) is True


class TestFuzzyFindInText:
    """Tests for fuzzy text search in Google snippets."""

    def test_exact_substring(self):
        text = "The best protein is Optimum Nutrition Gold Standard"
        assert fuzzy_find_in_text("Optimum Nutrition", text) is True

    def test_case_insensitive_search(self):
        text = "OPTIMUM NUTRITION is the best"
        assert fuzzy_find_in_text("optimum nutrition", text) is True

    def test_partial_word_match(self):
        text = "The Optimum Nutrition Gold Standard and BSN Syntha-6 are great"
        assert fuzzy_find_in_text("Optimum Nutrition Gold Standard", text) is True
        assert fuzzy_find_in_text("BSN SYNTHA-6", text) is True

    def test_brand_not_in_text(self):
        text = "This article is about hiking gear and outdoor equipment."
        assert fuzzy_find_in_text("Optimum Nutrition", text) is False

    def test_empty_brand(self):
        assert fuzzy_find_in_text("", "some text") is False

    def test_empty_text(self):
        assert fuzzy_find_in_text("Brand", "") is False

    def test_none_brand(self):
        assert fuzzy_find_in_text(None, "some text") is False

    def test_none_text(self):
        assert fuzzy_find_in_text("Brand", None) is False

    def test_single_word_brand(self):
        text = "Samsung Galaxy S24 Ultra review and comparison"
        assert fuzzy_find_in_text("Samsung", text) is True

    def test_brand_with_special_chars(self):
        text = "The Gold Standard 100% Whey protein by Optimum Nutrition"
        assert fuzzy_find_in_text("100% Whey", text) is True

    def test_sliding_window_near_match(self):
        """Test fuzzy match via sliding window for imperfect matches."""
        text = "Top picks include Optmum Nutriton and Dymatize"
        # Misspelled in text but should still fuzzy match
        assert fuzzy_find_in_text("Optimum Nutrition", text, threshold=70) is True

    def test_long_text(self):
        text = (
            "After extensive testing of over 50 different protein supplements, "
            "our team found that Optimum Nutrition Gold Standard 100% Whey "
            "consistently outperformed competitors in taste, mixability, and "
            "overall nutritional profile."
        )
        assert fuzzy_find_in_text("Optimum Nutrition Gold Standard", text) is True
        assert fuzzy_find_in_text("Dymatize ISO100", text) is False
