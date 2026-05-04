# llm_engine.py
import json
import requests
import os
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODELS = {
    "GPT-5-mini": "openai/gpt-5-mini",
    "Claude Sonnet": "anthropic/claude-sonnet-4",
    "Gemini 2.5 Flash": "google/gemini-2.5-flash"
}

# ─── Robust System Prompt ─────────────────────────────────────────────────────
# Designed to force structured JSON output from all models.
# Key features:
#   - Explicit JSON-only instruction with zero-tolerance for markdown/prose
#   - Multiple examples showing special characters (%, &, +, ™) are preserved
#   - Strict schema definition with rank + full brand name
#   - Fallback-friendly: even if a model ignores JSON, the numbered-list
#     instruction makes regex extraction more reliable
SYSTEM_PROMPT = """\
You are a product recommendation engine. Your ONLY job is to return structured data.

CRITICAL RULES — FOLLOW EXACTLY:
1. Respond with ONLY a valid JSON array. No markdown, no explanation, no intro text, no code fences.
2. The JSON array must contain exactly 5 objects.
3. Each object has exactly two keys:
   - "rank": integer from 1 (best) to 5
   - "brand": the FULL, EXACT brand/product name as commonly known to consumers
4. PRESERVE all special characters in brand names: %, &, +, #, ™, ®, apostrophes, hyphens.
5. Use the COMPLETE product line name, not just the company name.
   - CORRECT: "Optimum Nutrition Gold Standard 100% Whey"
   - WRONG:   "Optimum Nutrition" (too short, missing product line)
   - CORRECT: "Nature Made Wellblends Calm & Relax"
   - WRONG:   "Nature Made" (too short)
6. Do NOT wrap in ```json``` or any other formatting.
7. Do NOT add any text before or after the JSON array.

EXAMPLE of a PERFECT response (your output should look exactly like this):
[{"rank": 1, "brand": "Optimum Nutrition Gold Standard 100% Whey"}, {"rank": 2, "brand": "Dymatize ISO100 Hydrolyzed"}, {"rank": 3, "brand": "MyProtein Impact Whey Protein"}, {"rank": 4, "brand": "BSN SYNTHA-6 Edge"}, {"rank": 5, "brand": "MuscleTech Nitro-Tech 100% Whey Gold"}]

Remember: Output ONLY the JSON array. Nothing else."""


def _try_parse_json(text):
    """
    Attempt to extract a JSON array of brand objects from raw LLM text.
    Handles: code fences, preamble text, and truncated/malformed JSON.
    Returns list of (rank, brand) tuples or None on failure.
    """
    if not text or text.startswith("ERROR:") or text.startswith("API ERROR"):
        return None

    # Strip common markdown code-fence wrappers
    cleaned = text.strip()
    if cleaned.startswith("```"):
        first_newline = cleaned.index("\n") if "\n" in cleaned else 3
        cleaned = cleaned[first_newline + 1:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    # Try to find a JSON array in the text
    start = cleaned.find("[")
    end = cleaned.rfind("]")

    brands = None

    # Attempt 1: Standard json.loads on the array
    if start != -1 and end != -1 and end > start:
        json_str = cleaned[start:end + 1]
        try:
            data = json.loads(json_str)
            if isinstance(data, list):
                brands = _extract_from_json_list(data)
        except json.JSONDecodeError:
            pass

    # Attempt 2: JSON is truncated (no closing ']') — happens with Gemini
    # Try adding the missing bracket
    if not brands and start != -1:
        # Take everything from '[' and try to fix it
        partial = cleaned[start:]
        # Remove trailing comma if present
        partial = partial.rstrip().rstrip(',')
        if not partial.endswith(']'):
            partial += ']'
        # Also close any unclosed object
        if partial.count('{') > partial.count('}'):
            partial = partial.rstrip().rstrip(',')
            partial += '}]' if not partial.endswith('}') else ']'
        try:
            data = json.loads(partial)
            if isinstance(data, list):
                brands = _extract_from_json_list(data)
        except json.JSONDecodeError:
            pass

    # Attempt 3: JSON is completely malformed — extract "brand": "..." with regex
    # This catches cases like Gemini returning partial JSON objects
    if not brands:
        brands = _recover_brands_from_json_text(cleaned)

    return brands


def _extract_from_json_list(data):
    """Extract (rank, brand) tuples from a parsed JSON list of objects."""
    brands = []
    for item in data:
        if not isinstance(item, dict):
            continue
        rank = item.get("rank")
        # Ensure brand is a string before calling strip()
        brand_raw = item.get("brand")
        if not isinstance(brand_raw, str):
            continue
            
        brand = brand_raw.strip()
        if rank and brand and isinstance(rank, int) and 1 <= rank <= 10:
            brands.append((rank, brand))
    return brands if brands else None


def _recover_brands_from_json_text(text):
    """
    Last-resort recovery: extract brand names from malformed JSON text
    using regex to find "brand": "..." and "rank": N patterns.
    Works even when json.loads() fails completely.
    """
    import re
    # Find all "brand": "value" pairs
    brand_matches = re.findall(r'"brand"\s*:\s*"([^"]+)"', text)
    # Find all "rank": N pairs
    rank_matches = re.findall(r'"rank"\s*:\s*(\d+)', text)

    if not brand_matches:
        return None

    brands = []
    for i, brand in enumerate(brand_matches):
        # Use the corresponding rank if available, otherwise use position
        rank = int(rank_matches[i]) if i < len(rank_matches) else i + 1
        if brand.strip() and 1 <= rank <= 10:
            brands.append((rank, brand.strip()))

    return brands if brands else None

# Models that reliably support response_format via OpenRouter
_JSON_MODE_MODELS = {"openai/gpt-4.1", "openai/gpt-4o", "openai/gpt-4.1-mini"}

MAX_RETRIES = 2  # Retry once if response is empty/truncated


def query_single_llm(model_name, model_id, user_query):
    """Query a single LLM via OpenRouter and return (model_name, raw_text, parsed_brands_or_none)."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://aeo-diagnostic.app",
        "X-Title": "AEO Diagnostic"
    }
    payload = {
        "model": model_id,
        "max_tokens": 3000 if "gpt-5" in model_id else 1024,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_query}
        ],
    }

    # Only add response_format for models that reliably support it
    # Gemini and Claude via OpenRouter can return empty/truncated responses with this
    if model_id in _JSON_MODE_MODELS:
        payload["response_format"] = {"type": "json_object"}

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            data = response.json()

    

            # Check for API-level errors (402 credits, 429 rate limit, etc.)
            if "error" in data:
                err_msg = data["error"].get("message", str(data["error"]))
                return model_name, f"API ERROR ({response.status_code}): {err_msg}", None

            message = data["choices"][0]["message"]
            raw_text = message.get("content") or ""
            if not raw_text:
                reasoning_details = message.get("reasoning_details", [])
                for detail in reasoning_details:
                    if detail.get("type") == "reasoning.summary":
                        summary = detail.get("summary", "")
                        # Extract just the JSON array from the reasoning summary
                        import re
                        match = re.search(r'\[\s*\{.*?\}\s*\]', summary, re.DOTALL)
                        if match:
                            raw_text = match.group()
                            break

                # Also try top-level reasoning field
                if not raw_text:
                    raw_text = message.get("reasoning", "") or ""

            # Retry if response is suspiciously short (e.g., just "[" or empty)
            if len(raw_text.strip()) < 20 and attempt < MAX_RETRIES - 1:
                continue

            parsed = _try_parse_json(raw_text)
            return model_name, raw_text, parsed

        except requests.exceptions.Timeout:
            return model_name, "ERROR: Request timed out after 60 seconds", None
        except requests.exceptions.ConnectionError:
            return model_name, "ERROR: Could not connect to OpenRouter API", None
        except KeyError as e:
            return model_name, f"ERROR: Unexpected response format - missing key {e}. Raw: {str(data)[:300]}", None
        except Exception as e:
            return model_name, f"ERROR: {type(e).__name__}: {str(e)}", None

    # If we exhausted retries, return whatever we got last
    return model_name, raw_text, _try_parse_json(raw_text)


def query_all_llms(user_query):
    """
    Query all 3 LLMs in parallel.
    Returns dict: {model_name: {"raw": response_text, "parsed": [(rank, brand), ...] or None}}
    """
    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(query_single_llm, name, model_id, user_query)
            for name, model_id in MODELS.items()
        ]
        for future in futures:
            name, raw_text, parsed = future.result()
            results[name] = {"raw": raw_text, "parsed": parsed}
    return results
