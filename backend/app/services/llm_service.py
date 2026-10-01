# llm_service.py
import json
import time
import httpx
import logging
import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

from app.config import settings
from app.services.parser_service import parse_llm_response_detailed, ParseResult, ParsedRecommendation

logger = logging.getLogger(__name__)

# Configured evaluation models
MODELS = [
    {"name": "GPT-5-mini", "id": "openai/gpt-5-mini", "supports_json_schema": True},
    {"name": "Claude Sonnet 4", "id": "anthropic/claude-sonnet-4", "supports_json_schema": False},
    {"name": "Gemini 2.5 Flash", "id": "google/gemini-2.5-flash", "supports_json_schema": False},
]

# Strict JSON Schema definition for models that support response_format: json_schema
STRICT_RECOMMENDATIONS_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "recommendations_response",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "recommendations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "rank": {
                                "type": "integer",
                                "enum": [1, 2, 3, 4, 5]
                            },
                            "brand": {
                                "type": "string",
                                "minLength": 1
                            },
                            "product": {
                                "type": "string",
                                "minLength": 1
                            }
                        },
                        "required": ["rank", "brand", "product"],
                        "additionalProperties": False
                    },
                    "minItems": 5,
                    "maxItems": 5
                }
            },
            "required": ["recommendations"],
            "additionalProperties": False
        }
    }
}

SYSTEM_PROMPT = """\
You are an expert product evaluation assistant. Your task is to recommend the top 5 products for the user query.
Return your answer strictly as a JSON object adhering to this schema:
{
  "recommendations": [
    {"rank": 1, "brand": "COMPANY OR MANUFACTURER ONLY", "product": "FULL PRODUCT NAME"},
    {"rank": 2, "brand": "COMPANY OR MANUFACTURER ONLY", "product": "FULL PRODUCT NAME"},
    {"rank": 3, "brand": "COMPANY OR MANUFACTURER ONLY", "product": "FULL PRODUCT NAME"},
    {"rank": 4, "brand": "COMPANY OR MANUFACTURER ONLY", "product": "FULL PRODUCT NAME"},
    {"rank": 5, "brand": "COMPANY OR MANUFACTURER ONLY", "product": "FULL PRODUCT NAME"}
  ]
}

STRICT CONSTRAINTS:
1. Provide exactly five recommendations with ranks 1, 2, 3, 4, 5. Each rank must appear exactly once.
2. "brand" must be the company/manufacturer name only (e.g. "Apple", "Nike", "Sony").
3. "product" must be the specific product name including the brand (e.g. "Apple iPhone 15 Pro", "Nike Air Zoom Pegasus 40").
4. Output ONLY the JSON object. Do not include markdown explanations, preambles, or thoughts.
"""

# Transient status codes that qualify for retry
RETRY_STATUS_CODES = {408, 429, 500, 502, 503, 504}
# Permanent client status codes that should not be retried
NON_RETRY_STATUS_CODES = {400, 401, 403, 404, 422}
MAX_RETRIES = 2
BASE_BACKOFF_SECONDS = 0.5


@dataclass
class EngineExecutionResult:
    """Detailed execution result for an AI engine."""
    engine: str
    status: str  # "success" | "failed" | "invalid"
    raw_text: str = ""
    parse_result: Optional[ParseResult] = None
    latency_ms: float = 0.0
    attempts: int = 1
    error_type: Optional[str] = None
    error_message: Optional[str] = None


async def query_single_llm(
    client: httpx.AsyncClient,
    model: Dict[str, Any],
    user_query: str,
) -> EngineExecutionResult:
    """Query a single LLM via OpenRouter with bounded retry and strict structured output."""
    engine_name = model["name"]
    model_id = model["id"]
    supports_schema = model.get("supports_json_schema", False)

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://aeo-diagnostic.app",
        "X-Title": "AEO Diagnostic Tool",
        "Content-Type": "application/json",
    }

    payload: Dict[str, Any] = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Recommend the top 5 products for: {user_query}"},
        ],
        "temperature": 0.2,
    }

    if supports_schema:
        payload["response_format"] = STRICT_RECOMMENDATIONS_SCHEMA

    start_time = time.monotonic()
    attempts = 0
    last_error_type: Optional[str] = None
    last_error_msg: Optional[str] = None

    for attempt in range(1, MAX_RETRIES + 2):
        attempts = attempt
        try:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=25.0,
            )

            # Check for non-retryable client errors (401, 403, etc.)
            if resp.status_code in NON_RETRY_STATUS_CODES:
                elapsed = (time.monotonic() - start_time) * 1000
                err_msg = f"HTTP {resp.status_code}: {resp.text[:200]}"
                err_type = "auth_error" if resp.status_code in (401, 403) else "client_error"
                logger.error("Non-retryable error for %s: %s", engine_name, err_msg)
                return EngineExecutionResult(
                    engine=engine_name,
                    status="failed",
                    latency_ms=round(elapsed, 1),
                    attempts=attempts,
                    error_type=err_type,
                    error_message=err_msg,
                )

            # Check for retryable server/rate limit errors
            if resp.status_code in RETRY_STATUS_CODES:
                last_error_type = "rate_limit" if resp.status_code == 429 else "server_error"
                last_error_msg = f"HTTP {resp.status_code}: {resp.text[:200]}"
                logger.warning("Retryable HTTP %d from %s (attempt %d/%d)", resp.status_code, engine_name, attempt, MAX_RETRIES + 1)
                if attempt <= MAX_RETRIES:
                    await asyncio.sleep(BASE_BACKOFF_SECONDS * (2 ** (attempt - 1)))
                    continue
                break

            # Handle 200 OK response
            resp.raise_for_status()
            data = resp.json()

            choices = data.get("choices", [])
            if not choices:
                elapsed = (time.monotonic() - start_time) * 1000
                return EngineExecutionResult(
                    engine=engine_name,
                    status="failed",
                    latency_ms=round(elapsed, 1),
                    attempts=attempts,
                    error_type="empty_response",
                    error_message="No completion choices returned by model",
                )

            message = choices[0].get("message", {})
            # CRITICAL: Only parse actual message content; NEVER use reasoning/reasoning_details
            raw_content = message.get("content") or ""

            # Parse and validate recommendations
            parse_result = parse_llm_response_detailed(raw_content)
            elapsed = (time.monotonic() - start_time) * 1000

            # If parser marked it as invalid, engine status is 'invalid'
            engine_status = "success" if parse_result.status in ("valid", "partial", "low_confidence") else "invalid"
            err_type = None if engine_status == "success" else "validation_error"
            err_msg = None if engine_status == "success" else "; ".join(parse_result.errors)

            return EngineExecutionResult(
                engine=engine_name,
                status=engine_status,
                raw_text=raw_content,
                parse_result=parse_result,
                latency_ms=round(elapsed, 1),
                attempts=attempts,
                error_type=err_type,
                error_message=err_msg,
            )

        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            last_error_type = "timeout" if isinstance(exc, httpx.TimeoutException) else "connection_error"
            last_error_msg = str(exc)
            logger.warning("Network issue for %s on attempt %d: %s", engine_name, attempt, exc)
            if attempt <= MAX_RETRIES:
                await asyncio.sleep(BASE_BACKOFF_SECONDS * (2 ** (attempt - 1)))
                continue
            break
        except Exception as exc:
            last_error_type = "unexpected_error"
            last_error_msg = str(exc)
            logger.error("Unexpected failure querying %s: %s", engine_name, exc, exc_info=True)
            break

    elapsed = (time.monotonic() - start_time) * 1000
    return EngineExecutionResult(
        engine=engine_name,
        status="failed",
        latency_ms=round(elapsed, 1),
        attempts=attempts,
        error_type=last_error_type or "unknown_failure",
        error_message=last_error_msg or "Retries exhausted without successful response",
    )


async def query_llms_parallel(user_query: str) -> Dict[str, EngineExecutionResult]:
    """Execute LLM queries for all configured models concurrently."""
    async with httpx.AsyncClient() as client:
        tasks = [
            query_single_llm(client, model, user_query)
            for model in MODELS
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)

    return {res.engine: res for res in results}
