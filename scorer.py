# scorer.py
from thefuzz import fuzz
from parser import fuzzy_match_brand, fuzzy_find_in_text

# Threshold for considering two brand names as the "same" brand
DEDUP_THRESHOLD = 85


def score_brands(llm_results_parsed):
    """
    Scoring: Rank 1 = 5pts, Rank 2 = 4pts, Rank 3 = 3pts,
             Rank 4 = 2pts, Rank 5 = 1pt
    Aggregates across all LLMs with fuzzy deduplication so that
    similar brand names (e.g. short vs full product names) are merged into a single entry.
    """
    RANK_SCORES = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}

    brand_scores = {}  # canonical_key -> {display_name, scores, total}

    for llm_name, brands in llm_results_parsed.items():
        for rank, brand in brands:
            key = brand.lower().strip()
            score = RANK_SCORES.get(rank, 0)

            # Try to find an existing entry that fuzzy-matches this brand
            # AND HAS NOT ALREADY BEEN SCORED BY THIS LLM (prevent self-merging)
            matched_key = _find_matching_key(key, brand_scores, llm_name)

            if matched_key:
                # Merge into existing entry
                brand_scores[matched_key]["scores"][llm_name] = score
                brand_scores[matched_key]["total"] += score
                # Keep the longer/more complete display name
                if len(brand) > len(brand_scores[matched_key]["display_name"]):
                    brand_scores[matched_key]["display_name"] = brand
            else:
                # New brand entry
                brand_scores[key] = {
                    "display_name": brand,
                    "scores": {llm_name: score},
                    "total": score
                }

    # Sort by total score descending
    sorted_brands = sorted(
        brand_scores.values(),
        key=lambda x: x["total"], reverse=True
    )
    return sorted_brands


def _find_matching_key(new_key, brand_scores, current_llm_name):
    """
    Find an existing key in brand_scores that fuzzy-matches new_key.
    Will NOT match an entry that has already been scored by current_llm_name 
    (since an LLM's own list items must be distinct products).
    """
    for existing_key, data in brand_scores.items():
        if current_llm_name in data["scores"]:
            continue
        if fuzzy_match_brand(new_key, existing_key, threshold=DEDUP_THRESHOLD):
            return existing_key
    return None


def calculate_consistency(brand_data, llm_names):
    """How many LLMs agree on this brand? 0-100%"""
    mentions = sum(1 for llm in llm_names if llm in brand_data["scores"])
    return round((mentions / len(llm_names)) * 100)


def cross_validate_with_google(scored_brands, google_results):
    """
    Check if AI-recommended brands appear in Google results.
    Uses fuzzy matching to catch partial matches in titles and snippets.
    Adds a 'web_validated' flag to each brand.
    """
    google_text = " ".join([
        r["title"] + " " + r["snippet"]
        for r in google_results
    ])

    for brand in scored_brands:
        name = brand["display_name"]
        brand["web_validated"] = fuzzy_find_in_text(name, google_text, threshold=75)

    return scored_brands


def get_brand_report(scored_brands, your_brand, llm_names):
    """
    Finds your brand in scored results using fuzzy matching and builds a full report.
    Returns your stats + competitor comparison.
    """
    your_data = None
    competitors = []

    for brand in scored_brands:
        name = brand["display_name"]
        if your_brand and fuzzy_match_brand(your_brand, name, threshold=70):
            # scored_brands is sorted descending, so the first match is the highest scoring.
            # Keep the first match as the primary 'your_data' for the top cards.
            if your_data is None:
                your_data = brand
        else:
            competitors.append(brand)
            competitors.append(brand)

    report = {
        "your_brand": your_data,
        "competitors": competitors[:5],
        "all_brands": scored_brands,
        "llm_names": llm_names
    }
    return report


def calculate_grade(your_data, llm_names):
    """
    Assigns A/B/C/D/F grade based on:
    - How many LLMs mention you
    - Average rank position
    - Web validation
    """
    if not your_data:
        return "F", "Not mentioned by any AI engine"

    mentions = sum(1 for llm in llm_names if llm in your_data["scores"])
    avg_rank_score = your_data["total"] / mentions if mentions else 0
    web_bonus = 1 if your_data.get("web_validated") else 0

    # Max possible: 5pts (rank 1) * 3 LLMs = 15pts
    # Grade thresholds
    total = your_data["total"] + web_bonus

    if mentions == 3 and avg_rank_score >= 4:
        return "A", "Excellent — All 3 AIs rank you highly"
    elif mentions == 3 and avg_rank_score >= 2:
        return "B", "Good — All 3 AIs mention you but not at top"
    elif mentions == 2:
        return "C", "Average — Only 2 out of 3 AIs mention you"
    elif mentions == 1:
        return "D", "Weak — Only 1 AI mentions you"
    else:
        return "F", "Critical — No AI engine mentions your brand"


def generate_insights(your_data, competitors, llm_names, your_brand):
    """
    Generates specific, actionable text insights.
    """
    insights = []

    if not your_data:
        top_competitor = competitors[0]["display_name"] if competitors else "Unknown"
        insights.append(
            f"\U0001f6a8 **{your_brand.title()} is not mentioned by any AI engine.** "
            f"The dominant brand is **{top_competitor}**."
        )
        return insights

    # Which LLMs mention you vs don't
    mentioned_in = [llm for llm in llm_names if llm in your_data["scores"]]
    not_mentioned_in = [llm for llm in llm_names if llm not in your_data["scores"]]

    if not_mentioned_in:
        # Find who dominates in those LLMs
        for missing_llm in not_mentioned_in:
            dominant = next(
                (b["display_name"] for b in competitors
                 if missing_llm in b["scores"]),
                "competitors"
            )
            insights.append(
                f"\u26a0\ufe0f **{missing_llm} doesn't mention you.** "
                f"**{dominant}** dominates there instead."
            )

    # Rank gap vs top competitor
    if competitors:
        top = competitors[0]
        gap = top["total"] - your_data["total"]
        if gap > 0:
            insights.append(
                f"\U0001f4c9 **{top['display_name']} outscores you by {gap} points** "
                f"across AI engines. They appear more consistently at higher ranks."
            )
        else:
            insights.append(
                f"\u2705 **You outscore your nearest competitor "
                f"({top['display_name']}) by {abs(gap)} points.**"
            )

    # Web validation insight
    if not your_data.get("web_validated"):
        insights.append(
            "\U0001f310 **Your brand doesn't appear in top Google results** for this query. "
            "AI engines often reflect web authority — improving SEO may boost AEO."
        )
    else:
        insights.append(
            "\u2705 **Your brand is validated in Google Search results** — "
            "this likely helps your AI visibility."
        )

    # Consistency insight
    consistency = calculate_consistency(your_data, llm_names)
    if consistency == 100:
        insights.append(
            "\U0001f3c6 **All 3 AI engines agree on your brand** — strong consensus signal."
        )
    elif consistency >= 66:
        insights.append(
            "\U0001f4ca **2 out of 3 AI engines mention you** — room to grow on the third."
        )

    return insights
