"""
OpenAI client wrapper for Appaveli CodeMind
"""

import os
import logging
from typing import Dict, List, Optional, Any

from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Wrapper for OpenAI API client with CodeMind-specific functionality"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client

        Args:
            api_key: OpenAI API key (if not provided, uses environment variable)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required (set OPENAI_API_KEY)")

        self.client = OpenAI(api_key=self.api_key)
        self.default_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "4000"))

        logger.info(f"Initialized OpenAI client with model: {self.default_model}")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion

        Args:
            messages: List of message dictionaries (OpenAI format)
            model: Model to use (defaults to configured model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for OpenAI SDK

        Returns:
            Dict with normalized response fields for CodeMind
        """
        try:
            response = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or self.max_tokens,
                **kwargs
            )

            usage = {}
            if getattr(response, "usage", None):
                # openai SDK usage is a Pydantic-ish object in many versions
                usage = response.usage.model_dump() if hasattr(response.usage, "model_dump") else dict(response.usage)

            return {
                "content": response.choices[0].message.content,
                "usage": usage,
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason,
            }

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    def estimate_cost(self, tokens: int, model: Optional[str] = None) -> float:
        """
        Estimate cost for token usage (rough)

        Args:
            tokens: Total tokens
            model: Model used

        Returns:
            Estimated cost in USD
        """
        model = model or self.default_model

        # Rough pricing estimates (USD per 1M tokens)
        pricing = {
            "gpt-4o": 5.0,
            "gpt-4o-mini": 1.5,
            "gpt-4": 30.0,
        }

        per_million = pricing.get(model, 5.0)
        return (tokens / 1_000_000) * per_million