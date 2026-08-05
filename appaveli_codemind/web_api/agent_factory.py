"""
Agent factory for request-scoped CodeMindAgent instances.
Provides thread-safe agent creation with connection pooling.
"""
import logging
import os
from typing import Optional

from appaveli_codemind.core.agent import CodeMindAgent

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Factory for creating request-scoped CodeMindAgent instances.

    Ensures each request gets its own agent instance to prevent
    state leakage and race conditions.
    """

    def __init__(
        self,
        default_provider: str = "openai",
        default_api_key: Optional[str] = None,
    ):
        """
        Initialize the agent factory.

        Args:
            default_provider: Default LLM provider ('openai' or 'anthropic')
            default_api_key: Default API key (if not in env)
        """
        self.default_provider = default_provider
        self.default_api_key = default_api_key or self._get_default_api_key()

        logger.info(
            f"AgentFactory initialized with provider={default_provider}"
        )

    def _get_default_api_key(self) -> Optional[str]:
        """Get API key from environment based on provider."""
        # Check for provider-specific keys first
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        # Return based on default provider
        if self.default_provider == "openai" and openai_key:
            return openai_key
        elif self.default_provider == "anthropic" and anthropic_key:
            return anthropic_key

        # Fallback to any available key
        return openai_key or anthropic_key

    def create_agent(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> CodeMindAgent:
        """
        Create a new CodeMindAgent instance for this request.

        Args:
            provider: LLM provider override
            api_key: API key override

        Returns:
            A new CodeMindAgent instance
        """
        provider = provider or self.default_provider
        api_key = api_key or self.default_api_key

        logger.debug(f"Creating new agent instance with provider={provider}")

        return CodeMindAgent(
            api_key=api_key,
            llm_provider=provider,
        )


# Global factory instance (factory itself is thread-safe)
_agent_factory: Optional[AgentFactory] = None


def get_agent_factory() -> AgentFactory:
    """
    Get or create the global agent factory.

    The factory itself is thread-safe and can be shared.
    Each call to factory.create_agent() returns a NEW agent instance.
    """
    global _agent_factory
    if _agent_factory is None:
        # Determine provider from environment
        provider = os.getenv("LLM_PROVIDER", "openai")
        _agent_factory = AgentFactory(default_provider=provider)
    return _agent_factory


def get_agent() -> CodeMindAgent:
    """
    Dependency injection function for FastAPI.

    Creates a NEW agent instance for each request.
    Use with: `agent: CodeMindAgent = Depends(get_agent)`

    Returns:
        A new CodeMindAgent instance for this request
    """
    factory = get_agent_factory()
    return factory.create_agent()
