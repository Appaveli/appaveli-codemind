"""
LLM client factory for Appaveli CodeMind
"""

import os
from typing import Optional, Union

from appaveli_codemind.ai.openai_client import OpenAIClient
from appaveli_codemind.ai.anthropic_client import AnthropicClient


LLMClient = Union[OpenAIClient, AnthropicClient]


def get_llm_client(provider: Optional[str] = None, api_key: Optional[str] = None) -> LLMClient:
    """
    Return the configured LLM client.

    Env:
      LLM_PROVIDER=openai|anthropic
      OPENAI_API_KEY=...
      ANTHROPIC_API_KEY=...
    """
    provider = (provider or os.getenv("LLM_PROVIDER", "openai")).lower().strip()

    if provider in ("anthropic", "claude"):
        return AnthropicClient(api_key=api_key)

    # default
    return OpenAIClient(api_key=api_key)