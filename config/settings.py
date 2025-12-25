"""Configuration management for Multi-Agent Coder."""

import os
from typing import Dict, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # API Keys
        self.anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

        # Agent configuration
        self.agent_weights: Dict[str, float] = self._parse_agent_weights()
        self.max_questions: int = int(os.getenv("MAX_QUESTIONS", "3"))
        self.request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "120"))

        # Logging
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level: str = "DEBUG" if self.debug else "INFO"

        # Available agents
        self.available_agents: List[str] = self._get_available_agents()

    def _parse_agent_weights(self) -> Dict[str, float]:
        """Parse agent weights from environment variable."""
        weights_str = os.getenv("AGENT_WEIGHTS", "claude:1.0,openai:1.0,gemini:1.0")
        weights = {}
        for item in weights_str.split(","):
            if ":" in item:
                agent, weight = item.split(":")
                weights[agent.strip()] = float(weight.strip())
        return weights

    def _get_available_agents(self) -> List[str]:
        """Determine which agents are available based on API keys."""
        agents = []
        if self.anthropic_api_key:
            agents.append("claude")
        if self.openai_api_key:
            agents.append("openai")
        if self.gemini_api_key:
            agents.append("gemini")
        return agents

    def validate(self) -> bool:
        """Validate that at least one agent is configured."""
        if not self.available_agents:
            raise ValueError(
                "No AI agents configured. Please set at least one API key in .env file:\n"
                "- ANTHROPIC_API_KEY for Claude\n"
                "- OPENAI_API_KEY for OpenAI\n"
                "- GEMINI_API_KEY for Gemini"
            )
        return True


# Global settings instance
settings = Settings()
