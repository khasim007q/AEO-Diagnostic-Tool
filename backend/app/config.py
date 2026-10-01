# config.py
import json
import logging
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Required:
        OPENROUTER_API_KEY: API key for OpenRouter LLM access.
        SERPAPI_KEY: API key for SerpApi Google search.

    Optional:
        CORS_ORIGINS: List of allowed CORS origins (JSON array string).
        DEBUG: Enable debug logging.
    """

    OPENROUTER_API_KEY: str = ""
    SERPAPI_KEY: str = ""
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def parse_cors_origins(cls, value: str) -> List[str]:
        """Parse CORS origins if passed as a JSON string.

        Args:
            value: Either a JSON array string or a single origin URL.

        Returns:
            List of origin URLs.
        """
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return [value]
        return value


settings = Settings()
