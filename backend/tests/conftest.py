# conftest.py
import pytest
from typing import Dict, Any, List


@pytest.fixture
def valid_json_response() -> str:
    """Standard valid JSON response with brand and product fields."""
    return (
        '[{"rank": 1, "brand": "Optimum Nutrition", "product": "Optimum Nutrition Gold Standard 100% Whey"}, '
        '{"rank": 2, "brand": "Dymatize", "product": "Dymatize ISO100 Hydrolyzed"}, '
        '{"rank": 3, "brand": "MyProtein", "product": "MyProtein Impact Whey Protein"}, '
        '{"rank": 4, "brand": "BSN", "product": "BSN SYNTHA-6 Edge"}, '
        '{"rank": 5, "brand": "MuscleTech", "product": "MuscleTech Nitro-Tech 100% Whey Gold"}]'
    )


@pytest.fixture
def old_format_json_response() -> str:
    """JSON response in old format (brand only, no product field)."""
    return (
        '[{"rank": 1, "brand": "Optimum Nutrition Gold Standard 100% Whey"}, '
        '{"rank": 2, "brand": "Dymatize ISO100 Hydrolyzed"}, '
        '{"rank": 3, "brand": "MyProtein Impact Whey Protein"}]'
    )


@pytest.fixture
def fenced_json_response(valid_json_response: str) -> str:
    """JSON response wrapped in markdown code fences."""
    return f"```json\n{valid_json_response}\n```"


@pytest.fixture
def truncated_json_response() -> str:
    """JSON response truncated mid-object (common with Gemini)."""
    return '[{"rank": 1, "brand": "OnePlus", "product": "OnePlus 12R"},'


@pytest.fixture
def truncated_mid_object_response() -> str:
    """JSON truncated inside an object."""
    return (
        '[{"rank": 1, "brand": "Xiaomi", "product": "Xiaomi 14"}, '
        '{"rank": 2, "brand": "Samsung", "product": "Samsung Galaxy S24"}, '
        '{"rank": 3, "brand":'
    )


@pytest.fixture
def prose_with_json() -> str:
    """JSON array buried inside prose text."""
    return (
        'Here are my top picks for you:\n\n'
        '[{"rank": 1, "brand": "Apple", "product": "iPhone 15 Pro"}, '
        '{"rank": 2, "brand": "Samsung", "product": "Samsung Galaxy S24 Ultra"}]\n\n'
        'Hope this helps!'
    )


@pytest.fixture
def numbered_list_response() -> str:
    """Plain text numbered list (no JSON)."""
    return (
        "Here are the top 5 whey proteins:\n"
        "1. Optimum Nutrition Gold Standard 100% Whey - Best overall\n"
        "2. BSN SYNTHA-6 Edge - Best for taste\n"
        "3. MyProtein Impact Whey Protein - Best value\n"
        "4. Dymatize ISO100 Hydrolyzed - Best for digestion\n"
        "5. MuscleTech Nitro-Tech 100% Whey Gold - Best for muscle"
    )


@pytest.fixture
def bold_markdown_response() -> str:
    """Response with bold markdown brand names."""
    return (
        "I recommend these supplements:\n\n"
        "**Optimum Nutrition Gold Standard** is great for beginners.\n"
        "**BSN SYNTHA-6 Edge** offers amazing taste.\n"
        "**MyProtein Impact Whey** provides the best value."
    )


@pytest.fixture
def special_chars_json() -> str:
    """JSON with special characters in brand names."""
    return (
        '[{"rank": 1, "brand": "Nature Made", "product": "Nature Made Wellblends Calm & Relax"}, '
        '{"rank": 2, "brand": "Optimum Nutrition", "product": "Optimum Nutrition Gold Standard 100% Whey"}, '
        '{"rank": 3, "brand": "GNC", "product": "GNC Pro Performance 100% Whey + Creatine"}]'
    )


@pytest.fixture
def sample_parsed_data() -> Dict[str, List[Dict[str, Any]]]:
    """Parsed LLM data from 3 models, with overlapping brands."""
    return {
        "GPT-5-mini": [
            {"brand": "Optimum Nutrition", "product": "Gold Standard 100% Whey", "rank": 1},
            {"brand": "Dymatize", "product": "ISO100 Hydrolyzed", "rank": 2},
            {"brand": "MyProtein", "product": "Impact Whey Protein", "rank": 3},
            {"brand": "BSN", "product": "SYNTHA-6 Edge", "rank": 4},
            {"brand": "MuscleTech", "product": "Nitro-Tech", "rank": 5},
        ],
        "Claude Sonnet": [
            {"brand": "Optimum Nutrition", "product": "Gold Standard 100% Whey", "rank": 1},
            {"brand": "MyProtein", "product": "Impact Whey Protein", "rank": 2},
            {"brand": "Dymatize", "product": "ISO100 Hydrolyzed", "rank": 3},
            {"brand": "MuscleTech", "product": "Nitro-Tech", "rank": 4},
            {"brand": "Garden of Life", "product": "Sport Organic Protein", "rank": 5},
        ],
        "Gemini 2.5 Flash": [
            {"brand": "Optimum Nutrition", "product": "Gold Standard 100% Whey", "rank": 1},
            {"brand": "Dymatize", "product": "ISO100 Hydrolyzed", "rank": 2},
            {"brand": "BSN", "product": "SYNTHA-6 Edge", "rank": 3},
            {"brand": "Nature Made", "product": "Wellblends Calm & Relax", "rank": 4},
            {"brand": "MuscleTech", "product": "Nitro-Tech", "rank": 5},
        ],
    }


@pytest.fixture
def sample_google_results():
    """Sample Google search results for cross-validation."""
    from app.api.schemas import GoogleResult
    return [
        GoogleResult(
            rank=1,
            title="Best Whey Protein Powders 2024 - Optimum Nutrition Review",
            snippet="Optimum Nutrition Gold Standard is our top pick for whey protein.",
            url="https://example.com/best-whey-protein",
        ),
        GoogleResult(
            rank=2,
            title="Dymatize ISO100 vs Optimum Nutrition",
            snippet="Compare the top two whey protein powders available.",
            url="https://example.com/dymatize-vs-on",
        ),
        GoogleResult(
            rank=5,
            title="MyProtein Impact Whey - Full Review",
            snippet="MyProtein offers great value for money.",
            url="https://example.com/myprotein-review",
        ),
        GoogleResult(
            rank=8,
            title="Best Supplements for Muscle Building",
            snippet="BSN SYNTHA-6 Edge and MuscleTech Nitro-Tech are popular choices.",
            url="https://example.com/muscle-supplements",
        ),
    ]
