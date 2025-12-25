"""Parallel dispatcher for CLI-based agents."""

import asyncio
from typing import List, Dict, Any, Optional

from agents.base_cli import BaseCLIAgent, AgentResponse
from config.cli_settings import cli_settings


class CLIDispatcher:
    """Dispatches prompts to multiple CLI-based agents in parallel."""

    def __init__(self, agents: Optional[List[BaseCLIAgent]] = None, auto_detect: bool = True):
        """
        Initialize the CLI dispatcher.

        Args:
            agents: Optional list of specific CLI agents
            auto_detect: If True, auto-detect available CLI tools
        """
        if agents:
            self.agents = agents
        elif auto_detect:
            self.agents = self._create_agents_from_detection()
        else:
            self.agents = self._create_default_agents()

    def _create_agents_from_detection(self) -> List[BaseCLIAgent]:
        """Create agents by checking available CLI tools synchronously."""
        agents = []
        configs = cli_settings.get_all_cli_configs()

        # Create agent instances and let them check availability themselves
        for agent_key, config in configs.items():
            try:
                agent = self._create_agent_for_tool(agent_key, config["command"])
                if agent and agent.available:
                    agents.append(agent)
            except Exception:
                # Skip agents that can't be created
                continue

        return agents

    def _create_default_agents(self) -> List[BaseCLIAgent]:
        """Create agents from configured CLI commands."""
        agents = []
        configs = cli_settings.get_all_cli_configs()

        for agent_key, config in configs.items():
            try:
                agent = self._create_agent_for_tool(agent_key, config["command"])
                if agent and agent.available:
                    agents.append(agent)
            except Exception:
                continue

        return agents

    def _create_agent_for_tool(self, tool_key: str, command: str) -> Optional[BaseCLIAgent]:
        """Create appropriate agent instance for a tool."""
        # Import agent classes
        from agents.claude_cli import ClaudeCLIAgent
        from agents.gemini_cli import GeminiCLIAgent
        from agents.openai_cli import OpenAICLIAgent, CodexCLIAgent, GPT4CLIAgent
        from agents.generic_cli import GenericCLIAgent

        # Map tool keys to agent classes
        agent_classes = {
            "claude": ClaudeCLIAgent,
            "gemini": GeminiCLIAgent,
            "openai": OpenAICLIAgent,
            "codex": CodexCLIAgent,
            "gpt4": GPT4CLIAgent,
        }

        agent_class = agent_classes.get(tool_key)

        if agent_class:
            # Use the specific agent class
            return agent_class(command=command)
        else:
            # Use generic agent for unknown/custom tools
            return GenericCLIAgent(
                name=tool_key.replace("-", " ").title(),
                command=command
            )

    async def dispatch_all(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[AgentResponse]:
        """
        Send prompt to all CLI agents in parallel.

        Args:
            prompt: The prompt to send
            context: Optional context information

        Returns:
            List of AgentResponse objects from all agents
        """
        if not self.agents:
            raise ValueError(
                "No CLI agents available. Please install at least one AI CLI tool "
                "(Claude, Gemini, OpenAI, etc.)"
            )

        # Create tasks for all agents
        tasks = [
            agent.query(prompt, context)
            for agent in self.agents
        ]

        # Execute all queries in parallel
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter exceptions and create error responses
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

    def add_agent(self, agent: BaseCLIAgent) -> None:
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

    def print_agent_status(self):
        """Print status of all agents."""
        print("\n" + "=" * 60)
        print("🤖 Agent Status")
        print("=" * 60)

        for agent in self.agents:
            status = "✓ Available" if agent.available else "✗ Not Available"
            print(f"  {status} {agent.name} ({agent.command})")

        print("=" * 60)
