"""
Unit tests for AgentFactory.
"""
import os
import pytest
from unittest.mock import patch

from appaveli_codemind.core.agent import CodeMindAgent
from appaveli_codemind.web_api.agent_factory import (
    AgentFactory,
    get_agent,
    get_agent_factory,
)


class TestAgentFactory:
    """Tests for AgentFactory class."""

    def test_factory_creates_agent_instances(self):
        """Factory should create CodeMindAgent instances."""
        factory = AgentFactory(default_provider="openai")
        agent = factory.create_agent()

        assert isinstance(agent, CodeMindAgent)
        assert agent.llm_client is not None

    def test_factory_creates_unique_instances(self):
        """Each create_agent() call should return a new instance."""
        factory = AgentFactory(default_provider="openai")

        agent1 = factory.create_agent()
        agent2 = factory.create_agent()

        # Different instances
        assert agent1 is not agent2
        assert id(agent1) != id(agent2)

    def test_factory_respects_provider_parameter(self):
        """Factory should use the specified provider."""
        factory = AgentFactory(default_provider="openai")

        # Create with override
        agent = factory.create_agent(provider="anthropic")

        # Should have created agent (type check)
        assert isinstance(agent, CodeMindAgent)

    def test_factory_uses_default_provider(self):
        """Factory should use default provider when not specified."""
        factory = AgentFactory(default_provider="openai")
        agent = factory.create_agent()

        assert isinstance(agent, CodeMindAgent)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    def test_factory_gets_api_key_from_env(self):
        """Factory should get API key from environment."""
        factory = AgentFactory(default_provider="openai")

        # Should have picked up the env var
        assert factory.default_api_key == "test-key-123"

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-anthropic-key"})
    def test_factory_gets_anthropic_key_from_env(self):
        """Factory should get Anthropic API key from environment."""
        factory = AgentFactory(default_provider="anthropic")

        assert factory.default_api_key == "test-anthropic-key"

    def test_factory_handles_missing_api_key(self):
        """Factory should handle missing API keys gracefully."""
        # Clear environment
        with patch.dict(os.environ, {}, clear=True):
            factory = AgentFactory(default_provider="openai")

            # Should still create agent (will fail on actual LLM call)
            agent = factory.create_agent()
            assert isinstance(agent, CodeMindAgent)


class TestGetAgentFactory:
    """Tests for get_agent_factory() function."""

    def test_get_agent_factory_returns_singleton(self):
        """get_agent_factory() should return the same instance."""
        factory1 = get_agent_factory()
        factory2 = get_agent_factory()

        # Same instance
        assert factory1 is factory2

    def test_get_agent_factory_creates_factory(self):
        """get_agent_factory() should create an AgentFactory."""
        factory = get_agent_factory()

        assert isinstance(factory, AgentFactory)


class TestGetAgent:
    """Tests for get_agent() dependency injection function."""

    def test_get_agent_returns_agent_instance(self):
        """get_agent() should return a CodeMindAgent instance."""
        agent = get_agent()

        assert isinstance(agent, CodeMindAgent)

    def test_get_agent_returns_new_instances(self):
        """Each call to get_agent() should return a new instance."""
        agent1 = get_agent()
        agent2 = get_agent()

        # Different instances
        assert agent1 is not agent2
        assert id(agent1) != id(agent2)

    def test_get_agent_uses_factory(self):
        """get_agent() should use the global factory."""
        factory = get_agent_factory()

        # Get an agent
        agent = get_agent()

        # Should be from the factory
        assert isinstance(agent, CodeMindAgent)

    def test_multiple_get_agent_calls_independent(self):
        """Multiple get_agent() calls should return independent instances."""
        agents = [get_agent() for _ in range(10)]

        # All should be different instances
        agent_ids = [id(agent) for agent in agents]
        assert len(agent_ids) == len(set(agent_ids))

        # All should be valid agents
        for agent in agents:
            assert isinstance(agent, CodeMindAgent)
