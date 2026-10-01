# test_fuzzy.py
"""Comprehensive tests for brand entity resolution and fuzzy matching.

Tests priority-based entity resolution:
1. Exact normalized match
2. Explicit alias match
3. Domain match
4. Strong deterministic containment
5. High-confidence fuzzy match
6. Ambiguity rejection
Also covers product comparison and independent snippet search.
"""
import pytest
from app.utils.fuzzy import is_same_brand, is_same_product, fuzzy_find_in_text
from app.utils.entity_resolution import (
    normalize_brand_name,
    extract_domain,
    resolve_brand_entity,
)


class TestNormalizeBrandName:
    """Tests for brand name cleaning and normalization."""

    def test_strips_legal_suffixes(self):
        assert normalize_brand_name("Apple Inc.") == "apple"
        assert normalize_brand_name("Microsoft Corporation") == "microsoft"
        assert normalize_brand_name("Nike LLC") == "nike"
        assert normalize_brand_name("Adidas AG") == "adidas ag"

    def test_strips_punctuation_and_trademarks(self):
        assert normalize_brand_name("Nature's Best(TM)") == "natures best"
        assert normalize_brand_name("Optimum Nutrition(R)") == "optimum nutrition"

    def test_replaces_hyphens_and_slashes(self):
        assert normalize_brand_name("Coca-Cola") == "coca cola"
        assert normalize_brand_name("Pro/Trainer") == "pro trainer"

    def test_collapses_whitespace(self):
        assert normalize_brand_name("  Sony   Electronics  ") == "sony"

    def test_resolves_known_alias(self):
        assert normalize_brand_name("ON") == "optimum nutrition"
        assert normalize_brand_name("AWS") == "amazon"
        assert normalize_brand_name("MSFT") == "microsoft"


class TestExtractDomain:
    """Tests for URL and domain extraction."""

    def test_full_url(self):
        assert extract_domain("https://www.nike.com/running") == "nike.com"

    def test_http_url(self):
        assert extract_domain("http://adidas.de/products") == "adidas.de"

    def test_raw_domain_with_www(self):
        assert extract_domain("www.apple.com") == "apple.com"

    def test_raw_domain_clean(self):
        assert extract_domain("brooksrunning.com") == "brooksrunning.com"

    def test_empty_or_none(self):
        assert extract_domain("") is None
        assert extract_domain(None) is None


class TestEntityResolutionPriority:
    """Tests matching priority and ambiguity handling in entity resolution."""

    def test_priority_1_exact_normalized(self):
        known = [
            ("Nike", "nike", "nike.com"),
            ("Adidas", "adidas", "adidas.com"),
        ]
        assert resolve_brand_entity("NIKE", known) == "Nike"
        assert resolve_brand_entity("Nike Inc.", known) == "Nike"

    def test_priority_2_explicit_alias(self):
        known = [
            ("Optimum Nutrition", "optimum nutrition", "optimumnutrition.com"),
            ("MuscleTech", "muscletech", "muscletech.com"),
        ]
        assert resolve_brand_entity("ON", known) == "Optimum Nutrition"

    def test_priority_3_domain_match(self):
        known = [
            ("Brooks Running", "brooks running", "brooksrunning.com"),
            ("Asics", "asics", "asics.com"),
        ]
        # Match using candidate domain
        assert resolve_brand_entity("Brooks", known, candidate_domain="brooksrunning.com") == "Brooks Running"

    def test_priority_4_strong_containment(self):
        known = [
            ("Nike Athletic", "nike athletic", None),
            ("Puma", "puma", None),
        ]
        assert resolve_brand_entity("Nike Athletic Shoes", known) == "Nike Athletic"

    def test_priority_5_fuzzy_match(self):
        known = [
            ("Under Armour", "under armour", "underarmour.com"),
            ("New Balance", "new balance", "newbalance.com"),
        ]
        # Slight variation
        assert resolve_brand_entity("Under Armor", known) == "Under Armour"

    def test_priority_6_ambiguous_reject(self):
        """When two candidate brands are similarly close in score, reject."""
        known = [
            ("SoundMax Pro", "soundmax pro", None),
            ("SoundMax Plus", "soundmax plus", None),
        ]
        # "SoundMax" is equidistant from both, difference is < 5 points
        assert resolve_brand_entity("SoundMax", known) is None

    def test_unknown_brand_returns_none(self):
        known = [("Nike", "nike", "nike.com")]
        assert resolve_brand_entity("Totally Unknown Brand", known) is None


class TestIsSameBrand:
    """Tests for is_same_brand helper."""

    def test_exact_match(self):
        assert is_same_brand("Apple", "Apple") is True

    def test_case_insensitive(self):
        assert is_same_brand("apple", "APPLE") is True

    def test_legal_entity_variation(self):
        assert is_same_brand("Nike", "Nike Inc.") is True

    def test_alias_match(self):
        assert is_same_brand("ON", "Optimum Nutrition") is True

    def test_completely_different(self):
        assert is_same_brand("Apple", "Microsoft") is False

    def test_empty_or_none(self):
        assert is_same_brand("", "Apple") is False
        assert is_same_brand("Apple", "") is False
        assert is_same_brand(None, "Apple") is False
        assert is_same_brand("Apple", None) is False


class TestIsSameProduct:
    """Tests for is_same_product helper."""

    def test_exact_match(self):
        assert is_same_product("iPhone 15 Pro", "iPhone 15 Pro") is True

    def test_case_insensitive(self):
        assert is_same_product("iphone 15 pro", "iPhone 15 Pro") is True

    def test_different_version_numbers_do_not_merge(self):
        assert is_same_product("iPhone 14 Pro", "iPhone 15 Pro") is False
        assert is_same_product("Galaxy S23", "Galaxy S24") is False

    def test_same_version_numbers_merge(self):
        assert is_same_product("iPhone 15 Pro Max 256GB", "iPhone 15 Pro Max") is True

    def test_word_order_independent(self):
        assert is_same_product("Gold Standard Whey Protein", "Whey Protein Gold Standard") is True

    def test_empty_or_none(self):
        assert is_same_product("", "Test") is False
        assert is_same_product(None, "Test") is False


class TestFuzzyFindInText:
    """Tests for independent snippet brand matching."""

    def test_exact_substring(self):
        assert fuzzy_find_in_text("Nike", "The new Nike running shoes are top rated.") is True

    def test_case_insensitive(self):
        assert fuzzy_find_in_text("nike", "The new NIKE running shoes are top rated.") is True

    def test_word_boundary_match(self):
        # 'Son' should NOT match 'Sony'
        assert fuzzy_find_in_text("Son", "Sony releases new noise canceling headphones.") is False

    def test_not_in_text(self):
        assert fuzzy_find_in_text("Adidas", "Nike and Puma are featured here.") is False

    def test_empty_or_none(self):
        assert fuzzy_find_in_text("", "text") is False
        assert fuzzy_find_in_text("Nike", "") is False
        assert fuzzy_find_in_text(None, "text") is False
