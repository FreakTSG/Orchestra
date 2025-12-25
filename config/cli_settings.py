"""Configuration management for CLI-based Multi-Agent Coder."""

import os
from typing import Dict, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class CLISettings:
    """Configuration for CLI-based agent system (no API keys needed!)."""

    def __init__(self):
        # CLI Tool Commands (paths or command names)
        self.claude_cli: str = os.getenv("CLAUDE_CLI", "claude")
        self.gemini_cli: str = os.getenv("GEMINI_CLI", "gemini")
        self.codex_cli: str = os.getenv("CODEX_CLI", "codex")
        self.openai_cli: str = os.getenv("OPENAI_CLI", "openai")  # Legacy/alternative
        self.gpt4_cli: str = os.getenv("GPT4_CLI", "gpt4")

        # Optional: Custom CLI tools
        self.custom_clis: Dict[str, str] = self._parse_custom_clis()

        # System settings
        self.max_questions: int = int(os.getenv("MAX_QUESTIONS", "3"))
        self.request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "120"))
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"

        # Agent selection
        self.enabled_agents: List[str] = self._parse_enabled_agents()

        # Auto-detection
        self.auto_detect: bool = os.getenv("AUTO_DETECT_CLIS", "true").lower() == "true"

    def _parse_custom_clis(self) -> Dict[str, str]:
        """Parse custom CLI tools from environment."""
        custom = {}
        # Look for CUSTOM_CLI_<NAME> variables
        for key, value in os.environ.items():
            if key.startswith("CUSTOM_CLI_"):
                name = key.replace("CUSTOM_CLI_", "").lower()
                custom[name] = value
        return custom

    def _parse_enabled_agents(self) -> List[str]:
        """Parse list of enabled agents."""
        agents_str = os.getenv("ENABLED_AGENTS", "auto")
        if agents_str.lower() == "auto":
            return ["auto"]  # Auto-detect available CLIs

        return [a.strip() for a in agents_str.split(",") if a.strip()]

    def get_cli_config(self, agent_name: str) -> Dict[str, str]:
        """Get CLI configuration for a specific agent."""
        configs = {
            "claude": {"command": self.claude_cli},
            "gemini": {"command": self.gemini_cli},
            "codex": {"command": self.codex_cli},
            "openai": {"command": self.openai_cli},
            "gpt4": {"command": self.gpt4_cli},
        }

        # Add custom CLIs
        for name, command in self.custom_clis.items():
            configs[name] = {"command": command}

        return configs.get(agent_name.lower(), {})

    def get_all_cli_configs(self) -> Dict[str, Dict[str, str]]:
        """Get all CLI configurations."""
        configs = {
            "claude": {"command": self.claude_cli, "name": "Claude CLI"},
            "gemini": {"command": self.gemini_cli, "name": "Gemini CLI"},
            "codex": {"command": self.codex_cli, "name": "Codex CLI"},
            "openai": {"command": self.openai_cli, "name": "OpenAI CLI"},
            "gpt4": {"command": self.gpt4_cli, "name": "GPT-4 CLI"},
        }

        # Add custom CLIs
        for name, command in self.custom_clis.items():
            configs[name] = {"command": command, "name": name.title()}

        return configs


# Global settings instance
cli_settings = CLISettings()
