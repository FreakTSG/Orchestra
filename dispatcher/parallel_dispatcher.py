"""Parallel dispatcher for sending queries to multiple agents simultaneously."""

import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from agents.base import BaseAgent, AgentResponse
from config.settings import settings


class ParallelDispatcher:
    """Dispatches prompts to multiple agents in parallel."""

    def __init__(self, agents: Optional[List[BaseAgent]] = None):
        """
        Initialize the dispatcher.

        Args:
            agents: List of agent instances. If None, creates from available API keys.
        """
        self.agents = agents or self._create_default_agents()

    def _create_default_agents(self) -> List[BaseAgent]:
        """Create agent instances based on available API keys."""
        agents = []

        if settings.anthropic_api_key:
            from agents.claude_agent import ClaudeAgent
            agents.append(ClaudeAgent(api_key=settings.anthropic_api_key))

        if settings.openai_api_key:
            from agents.openai_agent import OpenAIAgent
            agents.append(OpenAIAgent(api_key=settings.openai_api_key))

        if settings.gemini_api_key:
            from agents.gemini_agent import GeminiAgent
            agents.append(GeminiAgent(api_key=settings.gemini_api_key))

        return agents

    async def dispatch_all(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[AgentResponse]:
        """
        Send prompt to all agents in parallel.

        Args:
            prompt: The prompt to send
            context: Optional context information

        Returns:
            List of AgentResponse objects from all agents
        """
        if not self.agents:
            raise ValueError("No agents available. Please configure at least one API key.")

        # Create tasks for all agents
        tasks = [
            agent.query(prompt, context)
            for agent in self.agents
        ]

        # Execute all queries in parallel
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and wrap them in error responses
        valid_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                valid_responses.append(AgentResponse(
                    agent_name=self.agents[i].name,
                    agent_type=self.agents[i].agent_type,
                    content=f"Error: {str(response)}",
                    metadata={"error": True}
                ))
            else:
                valid_responses.append(response)

        return valid_responses

    async def dispatch_to_agents(
        self,
        prompt: str,
        agent_names: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> List[AgentResponse]:
        """
        Send prompt to specific agents by name.

        Args:
            prompt: The prompt to send
            agent_names: List of agent names to dispatch to
            context: Optional context information

        Returns:
            List of AgentResponse objects
        """
        # Filter agents by name
        selected_agents = [
            agent for agent in self.agents
            if agent.name.lower() in [name.lower() for name in agent_names]
        ]

        if not selected_agents:
            available = ", ".join([agent.name for agent in self.agents])
            raise ValueError(
                f"No agents found matching {agent_names}. "
                f"Available agents: {available}"
            )

        # Create tasks for selected agents
        tasks = [
            agent.query(prompt, context)
            for agent in selected_agents
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        valid_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                valid_responses.append(AgentResponse(
                    agent_name=selected_agents[i].name,
                    agent_type=selected_agents[i].agent_type,
                    content=f"Error: {str(response)}",
                    metadata={"error": True}
                ))
            else:
                valid_responses.append(response)

        return valid_responses

    def get_available_agents(self) -> List[str]:
        """Get list of available agent names."""
        return [agent.name for agent in self.agents]

    def add_agent(self, agent: BaseAgent) -> None:
        """Add a new agent to the dispatcher."""
        self.agents.append(agent)

    def remove_agent(self, agent_name: str) -> bool:
        """
        Remove an agent by name.

        Returns:
            True if agent was removed, False if not found
        """
        for i, agent in enumerate(self.agents):
            if agent.name.lower() == agent_name.lower():
                self.agents.pop(i)
                return True
        return False
