"""AI agent implementations for multi-agent coding system."""

from .base import BaseAgent, AgentResponse

# Optional agent implementations (may require additional dependencies)
try:
    from .claude_agent import ClaudeAgent
    _claude_available = True
except ImportError:
    _claude_available = False

try:
    from .openai_agent import OpenAIAgent
    _openai_available = True
except ImportError:
    _openai_available = False

try:
    from .gemini_agent import GeminiAgent
    _gemini_available = True
except ImportError:
    _gemini_available = False

__all__ = [
    "BaseAgent",
    "AgentResponse",
]

# Add available agents to __all__
if _claude_available:
    __all__.append("ClaudeAgent")
if _openai_available:
    __all__.append("OpenAIAgent")
if _gemini_available:
    __all__.append("GeminiAgent")
