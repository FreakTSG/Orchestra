"""Claude (Anthropic) agent implementation."""

import time
import asyncio
from typing import Optional, Dict, Any
import anthropic

from .base import BaseAgent, AgentResponse


class ClaudeAgent(BaseAgent):
    """Anthropic Claude agent implementation."""

    def __init__(self, api_key: str, name: str = "Claude", model: str = "claude-3-sonnet-20240229"):
        super().__init__(api_key, name)
        self.model = model
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def query(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Send a query to Claude."""
        start_time = time.time()

        # Build the full prompt with context
        full_prompt = self._build_prompt(prompt, context)

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": full_prompt}]
            )

            latency_ms = int((time.time() - start_time) * 1000)
            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            # Extract code blocks if present
            code = self._extract_code(content)
            explanation = self._extract_explanation(content)

            return AgentResponse(
                agent_name=self.name,
                agent_type=self.agent_type,
                content=content,
                code=code,
                explanation=explanation,
                confidence=None,  # Claude doesn't provide confidence scores
                metadata={"model": self.model},
                tokens_used=tokens_used,
                latency_ms=latency_ms
            )

        except Exception as e:
            return AgentResponse(
                agent_name=self.name,
                agent_type=self.agent_type,
                content=f"Error: {str(e)}",
                metadata={"error": True}
            )

    async def evaluate(
        self,
        original_prompt: str,
        solution_to_evaluate: AgentResponse,
        other_solutions: list[AgentResponse]
    ) -> float:
        """
        Have Claude evaluate another agent's solution.
        Returns a score from 0-100.
        """
        evaluation_prompt = f"""Evaluate the following solution to this programming problem:

Original Problem:
{original_prompt}

Solution to Evaluate (from {solution_to_evaluate.agent_name}):
{solution_to_evaluate.content}

{self._format_other_solutions(other_solutions)}

Provide a score from 0-100 based on:
1. Correctness (40 points)
2. Code quality (20 points)
3. Efficiency (20 points)
4. Best practices (20 points)

Respond with ONLY a number between 0 and 100."""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[{"role": "user", "content": evaluation_prompt}]
            )

            # Extract score from response
            score_text = response.content[0].text.strip()
            score = float(''.join(filter(lambda x: x.isdigit() or x == '.', score_text)))
            return max(0, min(100, score))  # Ensure score is between 0-100

        except Exception:
            return 50.0  # Return neutral score on error

    async def enhance_prompt(
        self,
        initial_prompt: str,
        max_questions: int = 3
    ) -> tuple[list[str], str]:
        """
        Generate clarifying questions to improve the prompt.
        """
        enhancement_prompt = f"""Analyze this programming request and generate {max_questions} clarifying questions that would help provide a better solution.

Request: {initial_prompt}

Generate questions that would clarify:
- Technical requirements (language, frameworks, versions)
- Context and constraints
- Expected outcomes
- Edge cases or specific scenarios

Respond with exactly {max_questions} questions, each on a new line, starting with "Q:".

Example format:
Q: What programming language are you using?
Q: What is the expected input format?
Q: Are there any performance constraints?"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": enhancement_prompt}]
            )

            content = response.content[0].text
            questions = [
                line.replace("Q:", "").strip()
                for line in content.split("\n")
                if line.strip().startswith("Q:")
            ]

            # Limit to max_questions
            questions = questions[:max_questions]

            # Generate enhanced prompt template
            enhanced = f"""Enhanced Request (based on clarifying questions):

Original: {initial_prompt}

Clarifications:
"""
            for i, q in enumerate(questions, 1):
                enhanced += f"{i}. {q}\n"

            enhanced += "\nPlease provide a solution that addresses these aspects."

            return questions, enhanced

        except Exception:
            # Fallback to generic questions
            return [
                "What programming language and version are you using?",
                "Are there any specific constraints or requirements?",
                "What is the expected output or behavior?"
            ], initial_prompt

    def _build_prompt(self, prompt: str, context: Optional[Dict[str, Any]]) -> str:
        """Build the full prompt with context."""
        if not context:
            return prompt

        context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
        return f"""Context:
{context_str}

Request:
{prompt}"""

    def _extract_code(self, content: str) -> Optional[str]:
        """Extract code blocks from response."""
        import re
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', content, re.DOTALL)
        return code_blocks[0] if code_blocks else None

    def _extract_explanation(self, content: str) -> Optional[str]:
        """Extract explanation (text before code)."""
        # Return everything before the first code block
        if '```' in content:
            return content.split('```')[0].strip()
        return content

    def _format_other_solutions(self, solutions: list[AgentResponse]) -> str:
        """Format other solutions for comparison in evaluation."""
        if not solutions:
            return ""

        formatted = "\n\nOther Solutions for Comparison:\n"
        for sol in solutions:
            formatted += f"\n--- {sol.agent_name} ---\n{sol.content[:500]}...\n"

        return formatted
