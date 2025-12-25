"""Google Gemini agent implementation."""

import time
from typing import Optional, Dict, Any
import google.generativeai as genai

from .base import BaseAgent, AgentResponse


class GeminiAgent(BaseAgent):
    """Google Gemini agent implementation."""

    def __init__(
        self,
        api_key: str,
        name: str = "Gemini",
        model: str = "gemini-pro"
    ):
        super().__init__(api_key, name)
        self.model = model
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)

    async def query(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Send a query to Gemini."""
        start_time = time.time()

        full_prompt = self._build_prompt(prompt, context)

        try:
            # Gemini doesn't have a native async API, so we run it in a thread pool
            import asyncio
            response = await asyncio.to_thread(
                self.client.generate_content,
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=4096,
                    temperature=0.7,
                )
            )

            latency_ms = int((time.time() - start_time) * 1000)
            content = response.text
            tokens_used = None  # Gemini doesn't provide token count

            code = self._extract_code(content)
            explanation = self._extract_explanation(content)

            return AgentResponse(
                agent_name=self.name,
                agent_type=self.agent_type,
                content=content,
                code=code,
                explanation=explanation,
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
        """Have Gemini evaluate another agent's solution."""
        evaluation_prompt = f"""Evaluate this solution (score 0-100):

Problem: {original_prompt}

Solution from {solution_to_evaluate.agent_name}:
{solution_to_evaluate.content}

{self._format_other_solutions(other_solutions)}

Score based on:
- Correctness (40 points)
- Code quality (20 points)
- Efficiency (20 points)
- Best practices (20 points)

Respond with ONLY a number from 0-100."""

        try:
            import asyncio
            response = await asyncio.to_thread(
                self.client.generate_content,
                evaluation_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=10,
                    temperature=0,
                )
            )

            score_text = response.text.strip()
            score = float(''.join(filter(lambda x: x.isdigit() or x == '.', score_text)))
            return max(0, min(100, score))

        except Exception:
            return 50.0

    async def enhance_prompt(
        self,
        initial_prompt: str,
        max_questions: int = 3
    ) -> tuple[list[str], str]:
        """Generate clarifying questions to improve the prompt."""
        enhancement_prompt = f"""Generate {max_questions} clarifying questions for:

{initial_prompt}

Ask about:
- Language/framework
- Requirements
- Constraints
- Expected behavior

Format each question starting with "Q:" on its own line."""

        try:
            import asyncio
            response = await asyncio.to_thread(
                self.client.generate_content,
                enhancement_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.7,
                )
            )

            content = response.text
            questions = [
                line.replace("Q:", "").strip()
                for line in content.split("\n")
                if line.strip().startswith("Q:")
            ]

            questions = questions[:max_questions]

            enhanced = f"""Enhanced Request:

Original: {initial_prompt}

Clarifications:
"""
            for i, q in enumerate(questions, 1):
                enhanced += f"{i}. {q}\n"

            return questions, enhanced

        except Exception:
            return [
                "What programming language?",
                "Any specific requirements?",
                "Expected behavior?"
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
        """Extract explanation from response."""
        if '```' in content:
            return content.split('```')[0].strip()
        return content

    def _format_other_solutions(self, solutions: list[AgentResponse]) -> str:
        """Format other solutions for comparison."""
        if not solutions:
            return ""

        formatted = "\n\nOther Solutions:\n"
        for sol in solutions:
            formatted += f"\n--- {sol.agent_name} ---\n{sol.content[:500]}...\n"

        return formatted
