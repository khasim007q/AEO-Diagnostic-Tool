# test_scoring.py
"""Comprehensive tests for the scoring engine.

Covers exponential weighting, consensus multipliers, web bonuses,
brand grouping, deduplication, grade calculation, and insight generation.
"""
import pytest
from app.services.scoring_engine import (
    get_rank_weight,
    get_consensus_multiplier,
    get_web_bonus,
    merge_products,
    calculate_grade,
    generate_insights,
)
from app.api.schemas import GoogleResult
from app.models.brand import Brand, Product


class TestRankWeights:
    """Tests for exponential rank weighting."""

    def test_rank_1_highest(self):
        assert get_rank_weight(1) == 10.0

    def test_rank_2(self):
        assert get_rank_weight(2) == 6.0

    def test_rank_3(self):
        assert get_rank_weight(3) == 4.0

    def test_rank_4(self):
        assert get_rank_weight(4) == 2.0

    def test_rank_5_lowest(self):
        assert get_rank_weight(5) == 1.0

    def test_rank_0_invalid(self):
        assert get_rank_weight(0) == 0.0

    def test_rank_6_invalid(self):
        assert get_rank_weight(6) == 0.0

    def test_rank_negative_invalid(self):
        assert get_rank_weight(-1) == 0.0

    def test_exponential_curve(self):
        """Rank 1 should be worth significantly more than rank 5."""
        ratio = get_rank_weight(1) / get_rank_weight(5)
        assert ratio == 10.0  # 10x difference


class TestConsensusMultiplier:
    """Tests for consensus multiplier logic."""

    def test_single_llm(self):
        assert get_consensus_multiplier(1) == 1.0

    def test_two_llms(self):
        assert get_consensus_multiplier(2) == 1.15

    def test_three_llms(self):
        assert get_consensus_multiplier(3) == 1.30

    def test_more_than_three(self):
        """4+ LLMs should still get the max multiplier."""
        assert get_consensus_multiplier(4) == 1.30
        assert get_consensus_multiplier(10) == 1.30

    def test_zero_llms(self):
        assert get_consensus_multiplier(0) == 1.0


class TestWebBonus:
    """Tests for web authority bonus calculation."""

    def test_top_3_results(self):
        assert get_web_bonus(1) == 2.0
        assert get_web_bonus(2) == 2.0
        assert get_web_bonus(3) == 2.0

    def test_mid_page_results(self):
        assert get_web_bonus(4) == 1.0
        assert get_web_bonus(5) == 1.0
        assert get_web_bonus(7) == 1.0

    def test_bottom_page_results(self):
        assert get_web_bonus(8) == 0.5
        assert get_web_bonus(9) == 0.5
        assert get_web_bonus(10) == 0.5

    def test_beyond_page_1(self):
        assert get_web_bonus(11) == 0.0
        assert get_web_bonus(100) == 0.0

    def test_none_rank(self):
        assert get_web_bonus(None) == 0.0

    def test_zero_rank(self):
        assert get_web_bonus(0) == 0.0

    def test_negative_rank(self):
        assert get_web_bonus(-1) == 0.0


class TestMergeProducts:
    """Tests for the main scoring pipeline."""

    def test_single_llm_single_brand(self):
        parsed = {
            "GPT": [{"brand": "Apple", "product": "iPhone 15", "rank": 1}]
        }
        brands = merge_products(parsed, [])
        assert len(brands) == 1
        assert brands[0].name == "Apple"
        assert brands[0].total_score == 10.0  # rank 1 = 10pts, 1 LLM = 1.0x

    def test_same_brand_across_multiple_llms(self, sample_parsed_data):
        brands = merge_products(sample_parsed_data, [])
        # Optimum Nutrition appears in all 3 LLMs at rank 1
        on_brand = next(b for b in brands if b.name == "Optimum Nutrition")
        assert len(on_brand.llm_coverage) == 3
        # Score: 10 * 3 LLMs * 1.30 consensus = 39.0
        assert on_brand.total_score == pytest.approx(39.0, abs=0.1)

    def test_consensus_multiplier_applied(self):
        parsed = {
            "GPT": [{"brand": "A", "product": "A Pro", "rank": 1}],
            "Claude": [{"brand": "A", "product": "A Pro", "rank": 1}],
        }
        brands = merge_products(parsed, [])
        # 10 + 10 = 20 base, * 1.15 consensus = 23.0
        assert brands[0].total_score == pytest.approx(23.0, abs=0.1)

    def test_no_duplicate_competitors(self, sample_parsed_data):
        """Regression: the old code had a bug where competitors were duplicated."""
        brands = merge_products(sample_parsed_data, [])
        brand_names = [b.name for b in brands]
        # Each brand should appear exactly once
        assert len(brand_names) == len(set(b.lower() for b in brand_names))

    def test_web_validation_bonus(self, sample_parsed_data, sample_google_results):
        brands = merge_products(sample_parsed_data, sample_google_results)
        on_brand = next(b for b in brands if b.name == "Optimum Nutrition")
        # Should have web validation from google result rank 1
        has_web = any(p.web_validated for p in on_brand.products)
        assert has_web is True

    def test_web_rank_position_recorded(self, sample_parsed_data, sample_google_results):
        brands = merge_products(sample_parsed_data, sample_google_results)
        on_brand = next(b for b in brands if b.name == "Optimum Nutrition")
        web_ranks = [p.web_rank for p in on_brand.products if p.web_rank is not None]
        assert len(web_ranks) >= 1

    def test_products_grouped_under_brand(self, sample_parsed_data):
        brands = merge_products(sample_parsed_data, [])
        for brand in brands:
            for product in brand.products:
                assert product.brand_name == brand.name

    def test_no_overlap_between_llms_single_brand(self):
        """All LLMs return the same 5 brands in the same order."""
        base = [
            {"brand": "A", "product": "A Product", "rank": 1},
            {"brand": "B", "product": "B Product", "rank": 2},
            {"brand": "C", "product": "C Product", "rank": 3},
            {"brand": "D", "product": "D Product", "rank": 4},
            {"brand": "E", "product": "E Product", "rank": 5},
        ]
        parsed = {"GPT": base, "Claude": base, "Gemini": base}
        brands = merge_products(parsed, [])
        assert len(brands) == 5
        # Brand A should have 3/3 coverage
        brand_a = next(b for b in brands if b.name == "A")
        assert len(brand_a.llm_coverage) == 3

    def test_no_overlap_different_brands(self):
        """Each LLM returns completely different brands."""
        parsed = {
            "GPT": [{"brand": "A", "product": "A Pro", "rank": 1}],
            "Claude": [{"brand": "B", "product": "B Pro", "rank": 1}],
            "Gemini": [{"brand": "C", "product": "C Pro", "rank": 1}],
        }
        brands = merge_products(parsed, [])
        assert len(brands) == 3
        for b in brands:
            assert len(b.llm_coverage) == 1

    def test_empty_parsed_data(self):
        brands = merge_products({}, [])
        assert brands == []

    def test_brands_sorted_by_score_descending(self, sample_parsed_data):
        brands = merge_products(sample_parsed_data, [])
        scores = [b.total_score for b in brands]
        assert scores == sorted(scores, reverse=True)

    def test_consensus_percentage_calculated(self, sample_parsed_data):
        brands = merge_products(sample_parsed_data, [])
        on_brand = next(b for b in brands if b.name == "Optimum Nutrition")
        assert on_brand.consensus_pct == pytest.approx(100.0, abs=0.1)


class TestCalculateGrade:
    """Tests for grade calculation."""

    def test_grade_a_threshold(self):
        grade = calculate_grade(40.0, 50.0)
        assert grade.grade == "A"

    def test_grade_b_threshold(self):
        grade = calculate_grade(30.0, 50.0)
        assert grade.grade == "B"

    def test_grade_c_threshold(self):
        grade = calculate_grade(20.0, 50.0)
        assert grade.grade == "C"

    def test_grade_d_threshold(self):
        grade = calculate_grade(10.0, 50.0)
        assert grade.grade == "D"

    def test_grade_f_threshold(self):
        grade = calculate_grade(5.0, 50.0)
        assert grade.grade == "F"

    def test_zero_score(self):
        grade = calculate_grade(0.0, 50.0)
        assert grade.grade == "F"

    def test_perfect_score(self):
        grade = calculate_grade(50.0, 50.0)
        assert grade.grade == "A"

    def test_zero_max_possible(self):
        grade = calculate_grade(10.0, 0.0)
        assert grade.grade == "F"

    def test_score_exceeds_max(self):
        grade = calculate_grade(60.0, 50.0)
        assert grade.grade == "A"

    def test_grade_includes_label(self):
        grade = calculate_grade(45.0, 50.0)
        assert grade.label != ""
        assert len(grade.label) > 5

    def test_score_and_max_in_result(self):
        grade = calculate_grade(25.0, 50.0)
        assert grade.score == 25.0
        assert grade.max_score == 50.0


class TestGenerateInsights:
    """Tests for insight generation."""

    def test_no_brands(self):
        insights = generate_insights([], None)
        assert len(insights) >= 1
        assert "No brands" in insights[0]

    def test_top_brand_mentioned(self, sample_parsed_data):
        brands = merge_products(sample_parsed_data, [])
        insights = generate_insights(brands, None)
        assert any("top performing" in i.lower() for i in insights)

    def test_user_brand_found(self, sample_parsed_data):
        brands = merge_products(sample_parsed_data, [])
        insights = generate_insights(brands, "Optimum Nutrition")
        assert len(insights) >= 2

    def test_user_brand_not_found(self, sample_parsed_data):
        brands = merge_products(sample_parsed_data, [])
        insights = generate_insights(brands, "Nonexistent Brand")
        assert any("not mentioned" in i.lower() for i in insights)

    def test_user_brand_is_top(self, sample_parsed_data):
        brands = merge_products(sample_parsed_data, [])
        insights = generate_insights(brands, "Optimum Nutrition")
        # Optimum Nutrition should be top, so we should see a positive insight
        assert any(
            "leading" in i.lower() or "outscore" in i.lower()
            for i in insights
        )

    def test_web_validation_insight(self, sample_parsed_data, sample_google_results):
        brands = merge_products(sample_parsed_data, sample_google_results)
        insights = generate_insights(brands, "Optimum Nutrition")
        assert any("google" in i.lower() for i in insights)

    def test_no_user_brand_still_has_insights(self, sample_parsed_data):
        brands = merge_products(sample_parsed_data, [])
        insights = generate_insights(brands, None)
        assert len(insights) >= 1
