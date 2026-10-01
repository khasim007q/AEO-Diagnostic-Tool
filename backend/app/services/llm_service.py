# llm_service.py
import re
import json
import httpx
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple

from app.config import settings

logger = logging.getLogger(__name__)

# Models matching the original project, updated for brand+product separation
MODELS = [
    {"name": "GPT-5-mini", "id": "openai/gpt-5-mini", "json_mode": True},
    {"name": "Claude Sonnet", "id": "anthropic/claude-sonnet-4", "json_mode": False},
    {"name": "Gemini 2.5 Flash", "id": "google/gemini-2.5-flash", "json_mode": False},
]

# Models that support response_format via OpenRouter
_JSON_MODE_IDS = {"openai/gpt-5-mini", "openai/gpt-4.1", "openai/gpt-4o", "openai/gpt-4.1-mini"}

SYSTEM_PROMPT = """\
You are a product recommendation engine. Your ONLY job is to return structured data.

CRITICAL RULES:
1. Respond with ONLY a valid JSON array. No markdown, no explanation, no code fences.
2. The JSON array must contain exactly 5 objects.
3. Each object has exactly three keys:
   - "rank": integer from 1 (best) to 5
   - "brand": the COMPANY or MANUFACTURER name only (e.g., "Optimum Nutrition")
   - "product": the FULL product name including brand (e.g., "Optimum Nutrition Gold Standard 100% Whey")
4. PRESERVE all special characters in names: %, &, +, #, apostrophes, hyphens.
5. Use the COMPLETE product line name, not just the company name.
   - CORRECT brand: "Optimum Nutrition", product: "Optimum Nutrition Gold Standard 100% Whey"
   - WRONG brand: "Optimum Nutrition", product: "Optimum Nutrition" (too short, missing product line)
6. Do NOT wrap in ```json``` or any other formatting.
7. Do NOT add any text before or after the JSON array.

EXAMPLE of a PERFECT response:
[{"rank": 1, "brand": "Optimum Nutrition", "product": "Optimum Nutrition Gold Standard 100% Whey"}, {"rank": 2, "brand": "Dymatize", "product": "Dymatize ISO100 Hydrolyzed"}, {"rank": 3, "brand": "MyProtein", "product": "MyProtein Impact Whey Protein"}, {"rank": 4, "brand": "BSN", "product": "BSN SYNTHA-6 Edge"}, {"rank": 5, "brand": "MuscleTech", "product": "MuscleTech Nitro-Tech 100% Whey Gold"}]

Remember: Output ONLY the JSON array. Nothing else."""

MAX_RETRIES = 2


async def query_single_llm(
    client: httpx.AsyncClient,
    model: Dict[str, Any],
    user_query: str,
) -> Dict[str, Any]:
    """Query a single LLM via OpenRouter and return structured response.

    Args:
        client: Async HTTP client.
        model: Model configuration dict with name, id, json_mode fields.
        user_query: The user's search query.

    Returns:
        Dict with keys: raw_text, parsed_count, error.
    """
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://aeo-diagnostic.app",
        "X-Title": "AEO Diagnostic",
    }

    payload: Dict[str, Any] = {
        "model": model["id"],
        "max_tokens": 3000 if "gpt-5" in model["id"] else 1024,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_query},
        ],
    }

    # Only add response_format for models that reliably support it
    if model["id"] in _JSON_MODE_IDS:
        payload["response_format"] = {"type": "json_object"}

    raw_text = ""
    for attempt in range(MAX_RETRIES):
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0,
            )
            data = response.json()

            # Check for API-level errors
            if "error" in data:
                err_msg = data["error"].get("message", str(data["error"]))
                logger.error("API error from %s: %s", model["name"], err_msg)
                return {
                    "raw_text": f"API ERROR ({response.status_code}): {err_msg}",
                    "parsed_count": 0,
                    "error": err_msg,
                }

            message = data["choices"][0]["message"]
            raw_text = message.get("content") or ""

            # Some models put content in reasoning_details instead
            if not raw_text:
                reasoning_details = message.get("reasoning_details", [])
                for detail in reasoning_details:
                    if detail.get("type") == "reasoning.summary":
                        summary = detail.get("summary", "")
                        match = re.search(r'\[\s*\{.*?\}\s*\]', summary, re.DOTALL)
                        if match:
                            raw_text = match.group()
                            break

                if not raw_text:
                    raw_text = message.get("reasoning", "") or ""

            # Retry if response is too short (truncated or empty)
            if len(raw_text.strip()) < 20 and attempt < MAX_RETRIES - 1:
                logger.warning(
                    "Short response from %s (attempt %d), retrying",
                    model["name"],
                    attempt + 1,
                )
                continue

            return {
                "raw_text": raw_text,
                "parsed_count": 0,
                "error": None,
            }

        except httpx.TimeoutException:
            logger.error("Timeout querying %s", model["name"])
            return {
                "raw_text": "ERROR: Request timed out after 60 seconds",
                "parsed_count": 0,
                "error": "Request timed out",
            }
        except httpx.ConnectError:
            logger.error("Connection error querying %s", model["name"])
            return {
                "raw_text": "ERROR: Could not connect to OpenRouter API",
                "parsed_count": 0,
                "error": "Connection error",
            }
        except (KeyError, IndexError) as e:
            logger.error(
                "Unexpected response format from %s: %s",
                model["name"],
                str(e),
            )
            return {
                "raw_text": f"ERROR: Unexpected response format, missing key {e}",
                "parsed_count": 0,
                "error": str(e),
            }
        except Exception as e:
            logger.error("Unexpected error from %s: %s", model["name"], str(e))
            return {
                "raw_text": f"ERROR: {type(e).__name__}: {str(e)}",
                "parsed_count": 0,
                "error": str(e),
            }

    # Exhausted retries, return whatever we got last
    return {
        "raw_text": raw_text,
        "parsed_count": 0,
        "error": None,
    }


async def query_llms(user_query: str) -> Dict[str, Dict[str, Any]]:
    """Query all configured LLMs in parallel.

    Args:
        user_query: The user's search query.

    Returns:
        Dict mapping model name to response dict with raw_text, parsed_count, error.
    """
    results: Dict[str, Dict[str, Any]] = {}

    async with httpx.AsyncClient() as client:
        tasks = [
            query_single_llm(client, model, user_query) for model in MODELS
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for model, response in zip(MODELS, responses):
            if isinstance(response, Exception):
                logger.error(
                    "Unhandled exception from %s: %s",
                    model["name"],
                    str(response),
                )
                results[model["name"]] = {
                    "raw_text": f"ERROR: {str(response)}",
                    "parsed_count": 0,
                    "error": str(response),
                }
            else:
                results[model["name"]] = response

    return results
