"""Base agent interface and response models."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class AgentResponse(BaseModel):
    """Standardized response from any AI agent."""

    agent_name: str
    agent_type: str
    content: str
    code: Optional[str] = None
    explanation: Optional[str] = None
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = {}
    timestamp: datetime = datetime.now()
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "content": self.content,
            "code": self.code,
            "explanation": self.explanation,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms,
        }


class BaseAgent(ABC):
    """Abstract base class for all AI agents."""

    def __init__(self, api_key: str, name: str):
        self.api_key = api_key
        self.name = name
        self.agent_type = self.__class__.__name__

    @abstractmethod
    async def query(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Send a query to the agent and return the response.

        Args:
            prompt: The prompt to send to the agent
            context: Optional context information

        Returns:
            AgentResponse with the agent's answer
        """
        pass

    @abstractmethod
    async def evaluate(
        self,
        original_prompt: str,
        solution_to_evaluate: AgentResponse,
        other_solutions: list[AgentResponse]
    ) -> float:
        """
        Evaluate another agent's solution.

        Args:
            original_prompt: The original user prompt
            solution_to_evaluate: The solution to evaluate
            other_solutions: Other solutions for comparison

        Returns:
            Float score between 0 and 100
        """
        pass

    @abstractmethod
    async def enhance_prompt(self, initial_prompt: str, max_questions: int = 3) -> tuple[list[str], str]:
        """
        Generate clarifying questions to enhance the prompt.

        Args:
            initial_prompt: The user's initial prompt
            max_questions: Maximum number of questions to generate

        Returns:
            Tuple of (list of questions, enhanced prompt without answers)
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
