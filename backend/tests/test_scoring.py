# test_scoring.py
"""Comprehensive tests for the deterministic AI Visibility Scoring Engine."""
import pytest
from app.services.scoring_engine import (
    aggregate_brands,
    get_position_score,
    calculate_gap_analysis,
    generate_typed_insights,
    get_visibility_label,
)
from app.services.llm_service import EngineExecutionResult
from app.services.parser_service import ParseResult, ParsedRecommendation
from app.services.serp_service import GoogleCorroborationSummary


class TestPositionScoreWeights:
    """Verify exact position scores for top-5 recommendations."""

    def test_rank_1(self):
        assert get_position_score(1) == 1.00

    def test_rank_2(self):
        assert get_position_score(2) == 0.80

    def test_rank_3(self):
        assert get_position_score(3) == 0.60

    def test_rank_4(self):
        assert get_position_score(4) == 0.40

    def test_rank_5(self):
        assert get_position_score(5) == 0.20

    def test_none_rank(self):
        assert get_position_score(None) == 0.00

    def test_invalid_ranks(self):
        assert get_position_score(0) == 0.00
        assert get_position_score(6) == 0.00
        assert get_position_score(-1) == 0.00


class TestBestRankAggregation:
    """Verify that multiple products for the same brand in one engine use only the BEST rank."""

    def test_multiple_products_same_brand_best_rank_only(self):
        """GPT returns Nike Pegasus (#1) and Nike Vaporfly (#4).

        Only rank #1 contributes (position_score = 1.00). Must NOT sum 1.00 + 0.40.
        """
        engine_recs = [
            ParsedRecommendation(rank=1, brand="Nike", product="Nike Air Zoom Pegasus"),
            ParsedRecommendation(rank=2, brand="Adidas", product="Adidas Ultraboost"),
            ParsedRecommendation(rank=3, brand="Brooks", product="Brooks Ghost"),
            ParsedRecommendation(rank=4, brand="Nike", product="Nike Vaporfly"),
            ParsedRecommendation(rank=5, brand="Hoka", product="Hoka Clifton"),
        ]
        results = {
            "GPT-5-mini": EngineExecutionResult(
                engine="GPT-5-mini",
                status="success",
                parse_result=ParseResult(status="valid", recommendations=engine_recs),
            )
        }

        all_brands, target, _ = aggregate_brands(results, target_brand_name="Nike")
        assert target is not None
        assert target.name == "Nike"
        # Since single successful engine with rank 1, score must be exactly 100.0, NOT 140.0
        assert target.ai_visibility_score == 100.0
        obs = target.observations["GPT-5-mini"]
        assert obs.best_rank == 1
        assert obs.position_score == 1.00
        # Both products remain available as evidence
        assert len(obs.products) == 2
        product_names = [p.product_name for p in obs.products]
        assert "Nike Air Zoom Pegasus" in product_names
        assert "Nike Vaporfly" in product_names


class TestMultiEngineAggregation:
    """Verify multi-engine mean calculation across successful engines."""

    def test_perfect_across_all_engines(self, mock_successful_engine_results):
        all_brands, _, _ = aggregate_brands(mock_successful_engine_results)
        # Nike was: GPT #1 (1.0), Claude #2 (0.8), Gemini #2 (0.8)
        # Mean = (1.0 + 0.8 + 0.8) / 3 = 2.6 / 3 = 0.8666... -> 86.7
        nike = next(b for b in all_brands if b.name == "Nike")
        assert nike.ai_visibility_score == 86.7
        assert nike.mentioned_engine_count == 3
        assert nike.successful_engine_count == 3
        assert nike.mention_coverage == 100.0
        assert nike.engine_availability == 100.0
        assert nike.best_rank == 1
        assert nike.worst_rank == 2
        assert nike.median_rank == 2.0

    def test_score_guaranteed_between_zero_and_hundred(self):
        """Scores must strictly stay in [0.0, 100.0]."""
        results = {
            "GPT": EngineExecutionResult(
                engine="GPT",
                status="success",
                parse_result=ParseResult(
                    status="valid",
                    recommendations=[ParsedRecommendation(rank=1, brand="BrandA", product="ProductA")]
                )
            )
        }
        all_brands, _, _ = aggregate_brands(results)
        for b in all_brands:
            assert 0.0 <= b.ai_visibility_score <= 100.0


class TestFailureExclusionFromDenominator:
    """Verify that failed engines do not falsely penalize brand AI score."""

    def test_failed_engine_not_penalizing_score(self):
        """3 configured engines, 2 successful, 1 failed.

        Brand is #1 in both successful engines.
        Score must be 100 * (1.0 + 1.0)/2 = 100.0, NOT 100 * (1.0 + 1.0)/3 = 66.7.
        Engine availability = 2/3 (66.7%).
        Mention coverage = 2/2 (100.0%).
        """
        recs = [ParsedRecommendation(rank=1, brand="Nike", product="Nike Pegasus")]
        results = {
            "GPT": EngineExecutionResult(
                engine="GPT",
                status="success",
                parse_result=ParseResult(status="valid", recommendations=recs),
            ),
            "Claude": EngineExecutionResult(
                engine="Claude",
                status="success",
                parse_result=ParseResult(status="valid", recommendations=recs),
            ),
            "Gemini": EngineExecutionResult(
                engine="Gemini",
                status="failed",
                error_type="timeout",
                error_message="Gateway timeout",
            ),
        }

        all_brands, target, _ = aggregate_brands(results, target_brand_name="Nike")
        assert target is not None
        assert target.ai_visibility_score == 100.0
        assert target.successful_engine_count == 2
        assert target.configured_engine_count == 3
        assert target.mentioned_engine_count == 2
        assert target.mention_coverage == 100.0  # 2/2
        assert target.engine_availability == 66.7  # 2/3

        # Failed engine remains visible in observations
        assert target.observations["Gemini"].status == "failed"
        assert target.observations["Gemini"].error_type == "timeout"


class TestGapAnalysisSigned:
    """Verify that gap analysis preserves sign (your_score - competitor_score)."""

    def test_gap_sign_and_status(self):
        """Target score 80.0, Competitor A 60.0 -> gap +20.0, status 'winning'.

        Competitor B 90.0 -> gap -10.0, status 'losing'.
        Competitor C 80.0 -> gap 0.0, status 'tied'.
        """
        recs_target = [
            ParsedRecommendation(rank=1, brand="MyBrand", product="MyProduct"),
            ParsedRecommendation(rank=2, brand="CompA", product="CompA Product"),
            ParsedRecommendation(rank=3, brand="CompB", product="CompB Product"),
        ]
        results = {
            "GPT": EngineExecutionResult(
                engine="GPT",
                status="success",
                parse_result=ParseResult(status="valid", recommendations=recs_target),
            )
        }

        all_brands, target, comps = aggregate_brands(results, target_brand_name="MyBrand")
        gaps = calculate_gap_analysis(target, comps, ["GPT"])

        # Check overall gap vs CompA (MyBrand #1 = 100.0, CompA #2 = 80.0 -> gap = +20.0)
        compa_overall = next(g for g in gaps if g["competitor"] == "CompA" and g["engine"] == "Overall")
        assert compa_overall["gap"] == 20.0
        assert compa_overall["status"] == "winning"

        # Check overall gap vs CompB (MyBrand #1 = 100.0, CompB #3 = 60.0 -> gap = +40.0)
        compb_overall = next(g for g in gaps if g["competitor"] == "CompB" and g["engine"] == "Overall")
        assert compb_overall["gap"] == 40.0
        assert compb_overall["status"] == "winning"

    def test_losing_gap_is_strictly_negative(self):
        """When competitor outranks target brand, gap must be negative."""
        recs = [
            ParsedRecommendation(rank=1, brand="Leader", product="Leader Prod"),
            ParsedRecommendation(rank=2, brand="MyBrand", product="My Prod"),
        ]
        results = {
            "GPT": EngineExecutionResult(
                engine="GPT",
                status="success",
                parse_result=ParseResult(status="valid", recommendations=recs),
            )
        }
        all_brands, target, comps = aggregate_brands(results, target_brand_name="MyBrand")
        gaps = calculate_gap_analysis(target, comps, ["GPT"])

        leader_gap = next(g for g in gaps if g["competitor"] == "Leader" and g["engine"] == "Overall")
        # Target #2 (80.0) - Leader #1 (100.0) = -20.0
        assert leader_gap["gap"] == -20.0
        assert leader_gap["status"] == "losing"

    def test_gap_analysis_omits_failed_or_partial_engines(self):
        """When an engine failed or produced partial output for either brand, omit that engine's gap."""
        recs_gpt = [
            ParsedRecommendation(rank=1, brand="Nike", product="Nike Pegasus"),
        ]
        results = {
            "GPT": EngineExecutionResult(
                engine="GPT",
                status="success",
                parse_result=ParseResult(status="valid", recommendations=recs_gpt),
            ),
            "Claude": EngineExecutionResult(
                engine="Claude",
                status="failed",
                error_type="timeout",
                error_message="Claude timed out",
            ),
            "Gemini": EngineExecutionResult(
                engine="Gemini",
                status="partial",
                parse_result=ParseResult(
                    status="partial",
                    recommendations=[ParsedRecommendation(rank=2, brand="Adidas", product="Adidas Sambas")],
                ),
            ),
        }
        all_brands, target, comps = aggregate_brands(results, target_brand_name="Nike")
        gaps = calculate_gap_analysis(target, comps, ["GPT", "Claude", "Gemini"])

        # Check all gap entries generated
        engine_gap_engines = [g["engine"] for g in gaps]
        # Overall gap should exist
        assert "Overall" in engine_gap_engines
        # Claude (failed) must not be compared
        assert "Claude" not in engine_gap_engines
        # Gemini (partial) must not be compared
        assert "Gemini" not in engine_gap_engines


class TestTypedInsights:
    """Verify evidence-based typed insights generation."""

    def test_typed_insights_structure(self, mock_successful_engine_results, mock_google_summary_success):
        all_brands, target, _ = aggregate_brands(mock_successful_engine_results, target_brand_name="Nike")
        insights = generate_typed_insights(
            target_brand=target,
            all_brands=all_brands,
            engine_results=mock_successful_engine_results,
            google_summary=mock_google_summary_success,
        )

        assert len(insights) > 0
        for insight in insights:
            assert insight["type"] in ("positive", "warning", "info")
            assert "title" in insight
            assert "message" in insight
            assert "evidence" in insight
            # Must NOT contain forbidden causal text
            assert "Improving SEO will boost AI visibility" not in insight["message"]
            assert "Google validates the AI recommendation" not in insight["message"]


class TestEngineStatusScoringExclusionAndCompleteness:
    """Tests proving strict status isolation and complete observation matrices."""

    def test_valid_response_participates_and_partial_failed_excluded(self):
        """1 valid engine (success), 1 partial engine, 1 invalid engine, 1 failed engine.

        Only the 1 valid engine participates in the AI Visibility Score denominator.
        Score must be 100 * (1.0) / 1 = 100.0, NOT 100 * (1.0) / 4 = 25.0.
        Engine availability = 1/4 (25.0%).
        Mention coverage = 1/1 (100.0%).
        """
        nike_rec = [ParsedRecommendation(rank=1, brand="Nike", product="Nike Pegasus")]
        partial_recs = [ParsedRecommendation(rank=3, brand="Nike", product="Nike Streak")]

        results = {
            "EngineValid": EngineExecutionResult(
                engine="EngineValid",
                status="success",
                parse_result=ParseResult(status="valid", recommendations=nike_rec),
            ),
            "EnginePartial": EngineExecutionResult(
                engine="EnginePartial",
                status="partial",
                parse_result=ParseResult(status="partial", recommendations=partial_recs),
            ),
            "EngineInvalid": EngineExecutionResult(
                engine="EngineInvalid",
                status="invalid",
                error_type="validation_error",
                error_message="Duplicate ranks",
            ),
            "EngineFailed": EngineExecutionResult(
                engine="EngineFailed",
                status="failed",
                error_type="timeout",
                error_message="Request timed out",
            ),
        }

        all_brands, target, _ = aggregate_brands(results, target_brand_name="Nike")
        assert target is not None
        assert target.name == "Nike"
        assert target.configured_engine_count == 4
        assert target.successful_engine_count == 1
        assert target.mentioned_engine_count == 1
        assert target.engine_availability == 25.0
        assert target.mention_coverage == 100.0
        # Valid engine had rank 1 -> 1.00 position score -> 100.0 / 1 = 100.0
        assert target.ai_visibility_score == 100.0

        # Partial engine still exposes its product evidence
        obs_partial = target.observations["EnginePartial"]
        assert obs_partial.status == "partial"
        assert obs_partial.position_score == 0.0
        assert len(obs_partial.products) == 1
        assert obs_partial.products[0].product_name == "Nike Streak"

        # Failed engine is present
        obs_failed = target.observations["EngineFailed"]
        assert obs_failed.status == "failed"
        assert obs_failed.error_type == "timeout"

    def test_every_brand_has_every_engine_observation_matrix(self):
        """Discovered brands in different engines must all receive an observation for every engine."""
        recs_e1 = [ParsedRecommendation(rank=1, brand="BrandOne", product="Prod One")]
        recs_e2 = [ParsedRecommendation(rank=2, brand="BrandTwo", product="Prod Two")]
        recs_e3 = [ParsedRecommendation(rank=3, brand="BrandThree", product="Prod Three")]

        results = {
            "E1": EngineExecutionResult(
                engine="E1",
                status="success",
                parse_result=ParseResult(status="valid", recommendations=recs_e1),
            ),
            "E2": EngineExecutionResult(
                engine="E2",
                status="success",
                parse_result=ParseResult(status="valid", recommendations=recs_e2),
            ),
            "E3": EngineExecutionResult(
                engine="E3",
                status="success",
                parse_result=ParseResult(status="valid", recommendations=recs_e3),
            ),
        }

        all_brands, _, _ = aggregate_brands(results)
        assert len(all_brands) == 3

        for brand in all_brands:
            assert len(brand.observations) == 3
            assert set(brand.observations.keys()) == {"E1", "E2", "E3"}
            for eng, obs in brand.observations.items():
                assert obs.engine == eng
                assert obs.status == "success"

        # Check BrandOne specifically
        b1 = next(b for b in all_brands if b.name == "BrandOne")
        assert b1.observations["E1"].mentioned is True
        assert b1.observations["E1"].best_rank == 1
        assert b1.observations["E2"].mentioned is False
        assert b1.observations["E2"].best_rank is None
        assert b1.observations["E3"].mentioned is False
        assert b1.observations["E3"].best_rank is None

        # Check BrandTwo specifically
        b2 = next(b for b in all_brands if b.name == "BrandTwo")
        assert b2.observations["E1"].mentioned is False
        assert b2.observations["E2"].mentioned is True
        assert b2.observations["E2"].best_rank == 2
        assert b2.observations["E3"].mentioned is False
