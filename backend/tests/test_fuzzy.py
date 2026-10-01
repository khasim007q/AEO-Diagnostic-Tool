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
    normalize_text_for_search,
    extract_domain,
    is_domain_match,
    resolve_brand_entity,
    get_brand_search_variants,
    is_variant_in_text,
)


class TestNormalizeBrandName:
    """Tests for brand name cleaning and normalization."""

    def test_strips_legal_suffixes(self):
        assert normalize_brand_name("Apple Inc.") == "apple"
        assert normalize_brand_name("Microsoft Corporation") == "microsoft"
        assert normalize_brand_name("Nike LLC") == "nike"

    def test_strips_punctuation_and_trademarks(self):
        assert normalize_brand_name("Nature's Best(TM)") == "natures best"
        assert normalize_brand_name("Optimum Nutrition(R)") == "optimum nutrition"
        assert normalize_brand_name("Nike®") == "nike"
        assert normalize_brand_name("Apple™") == "apple"

    def test_replaces_hyphens_and_slashes(self):
        assert normalize_brand_name("Coca-Cola") == "coca cola"
        assert normalize_brand_name("Pro/Trainer") == "pro trainer"

    def test_collapses_whitespace(self):
        assert normalize_brand_name("  New   Balance  ") == "new balance"

    def test_resolves_known_alias(self):
        assert normalize_brand_name("ON") == "optimum nutrition"
        assert normalize_brand_name("Optimum") == "optimum nutrition"
        assert normalize_brand_name("MSFT") == "microsoft"

    def test_conservative_aliases_not_merging_divisions(self):
        # Divisions, subsidiaries, and legal entities must not merge to base brands
        assert normalize_brand_name("Sony Electronics") == "sony electronics"
        assert normalize_brand_name("Apple Computer") == "apple computer"
        assert normalize_brand_name("Nike Athletic") == "nike athletic"

    def test_does_not_merge_corporate_parents_and_subsidiaries(self):
        # AWS != Amazon, Facebook != Meta, Alphabet != Google
        assert normalize_brand_name("AWS") == "aws"
        assert normalize_brand_name("Amazon") == "amazon"
        assert normalize_brand_name("Facebook") == "facebook"
        assert normalize_brand_name("Meta") == "meta"
        assert normalize_brand_name("Alphabet") == "alphabet"
        assert normalize_brand_name("Google") == "google"

    def test_context_aware_legal_and_co_preservation(self):
        assert normalize_brand_name("Apple Inc.") == "apple"
        assert normalize_brand_name("Nike LLC") == "nike"
        assert normalize_brand_name("Coca-Cola") == "coca cola"
        assert normalize_brand_name("Co-op") == "co op"
        assert normalize_brand_name("Company A") == "company a"

    def test_apostrophe_and_unicode_variants(self):
        assert normalize_brand_name("L'Oréal") == "l oreal"
        assert normalize_brand_name("L’Oreal") == "l oreal"
        assert normalize_brand_name("L Oreal") == "l oreal"
        assert normalize_brand_name("Nature’s Best") == "natures best"
        assert normalize_brand_name("Nature's Best") == "natures best"


class TestDomainMatching:
    """Tests for strict hostname and subdomain matching."""

    def test_exact_domain(self):
        assert is_domain_match("nike.com", "nike.com") is True

    def test_valid_subdomain(self):
        assert is_domain_match("nike.com", "store.nike.com") is True
        assert is_domain_match("apple.com", "developer.apple.com") is True

    def test_rejects_subdomain_spoofing(self):
        # nike.com.example.com must NOT match nike.com
        assert is_domain_match("nike.com", "nike.com.example.com") is False
        assert is_domain_match("nike.com", "faknike.com") is False
        assert is_domain_match("apple.com", "apple.com.attacker.com") is False

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


class TestBrandSearchVariantsAndCorroborationMatching:
    """Tests for alias-aware search variants and preposition-safe text matching."""

    def test_search_variants_for_alias(self):
        # Target "ON" should include "optimum nutrition" and "on"
        variants = get_brand_search_variants("ON")
        assert "optimum nutrition" in variants
        assert "on" in variants
        # Sorted by length descending
        assert variants[0] == "optimum nutrition"

    def test_search_variants_for_canonical(self):
        # Target "Optimum Nutrition" should include "optimum nutrition", "on", "optimum"
        variants = get_brand_search_variants("Optimum Nutrition")
        assert "optimum nutrition" in variants
        assert "on" in variants
        assert "optimum" in variants

    def test_is_variant_in_text_acronym_matches_in_full_title(self):
        # Title mentioning Optimum Nutrition Gold Standard matches search variants for "ON"
        variants = get_brand_search_variants("ON")
        raw_title = "Optimum Nutrition Gold Standard 100% Whey"
        norm_title = normalize_text_for_search(raw_title)

        matched = any(is_variant_in_text(v, raw_title, norm_title) for v in variants)
        assert matched is True

    def test_is_variant_in_text_ignores_english_preposition_on(self):
        # Text with lowercase preposition "on" should NOT match target acronym "ON"
        raw_text = "Running shoes for best performance on roads and trails."
        norm_text = normalize_text_for_search(raw_text)

        # "on" is length <= 2, raw_text has lowercase "on", NOT uppercase "ON"
        assert is_variant_in_text("on", raw_text, norm_text) is False

    def test_is_variant_in_text_matches_uppercase_acronym_on(self):
        # Raw text with uppercase ON should match
        raw_text = "Top picks from ON Running and Nike."
        norm_text = normalize_text_for_search(raw_text)

        assert is_variant_in_text("on", raw_text, norm_text) is True
