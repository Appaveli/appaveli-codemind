import logging
import os
from typing import Any, Dict, List, Optional

from anthropic import Anthropic

logger = logging.getLogger(__name__)


class AnthropicClient:
    """Wrapper for Anthropic Claude API client with CodeMind-specific functionality"""

    def __init__(self, api_key: Optional[str] = None):
        # For testing/CI, use a dummy key. Real API calls will fail but client can be created.
        DEFAULT_TEST_KEY = "sk-ant-test-dummy-key-for-ci-testing-not-real"
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or DEFAULT_TEST_KEY

        if self.api_key == DEFAULT_TEST_KEY:
            logger.warning("Using default test Anthropic key - set ANTHROPIC_API_KEY for real usage")

        self.client = Anthropic(api_key=self.api_key)
        self.default_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
        self.max_tokens = int(os.getenv("ANTHROPIC_MAX_TOKENS", "4000"))

        logger.info(f"Initialized Anthropic client with model: {self.default_model}")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a Claude message. Keeps the same output shape as OpenAIClient.chat_completion().
        NOTE: Claude uses `system=` separately; OpenAI-style system messages must be converted.
        """
        try:
            system_text = ""
            filtered_messages: List[Dict[str, str]] = []

            for m in messages:
                role = m.get("role")
                content = m.get("content", "")

                if role == "system":
                    if content:
                        system_text += content if not system_text else "\n" + content
                    continue

                if role in ("user", "assistant"):
                    filtered_messages.append({"role": role, "content": content})

            resp = self.client.messages.create(
                model=model or self.default_model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature,
                system=system_text or None,
                messages=filtered_messages,
                **kwargs,
            )

            # Claude returns content blocks; gather text blocks into one string
            text_out = ""
            for block in getattr(resp, "content", []) or []:
                if getattr(block, "type", None) == "text":
                    text_out += getattr(block, "text", "")

            usage = {}
            if getattr(resp, "usage", None):
                usage = {
                    "input_tokens": getattr(resp.usage, "input_tokens", 0),
                    "output_tokens": getattr(resp.usage, "output_tokens", 0),
                }

            return {
                "content": text_out,
                "usage": usage,
                "model": model or self.default_model,
                "finish_reason": getattr(resp, "stop_reason", None),
            }

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    def estimate_cost(self, tokens: int, model: Optional[str] = None) -> float:
        """
        Estimate cost using a blended per-1M-token rate (rough).
        Keeps interface consistent with OpenAIClient.
        """
        model = model or self.default_model

        blended_pricing_per_million = {
            "claude-haiku-4-5": 2.0,
            "claude-sonnet-4-5-20250929": 9.0,
        }

        per_million = blended_pricing_per_million.get(model, 5.0)
        return (tokens / 1_000_000) * per_million
