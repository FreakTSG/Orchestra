"""Google Gemini CLI agent implementation."""

from typing import Optional, Dict, Any, List
from .base_cli import BaseCLIAgent, AgentResponse


class GeminiCLIAgent(BaseCLIAgent):
    """
    Gemini CLI agent.

    Assumes 'gemini' CLI tool is installed.
    Installation: https://github.com/google/generative-ai-python
    Or via: gemini-cli (if available)
    """

    def __init__(self, name: str = "Gemini CLI", command: str = "gemini"):
        super().__init__(name, command)

    def build_query_command(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Build command for querying Gemini CLI."""
        # Gemini CLI: just "gemini" (then prompt via stdin)
        return []  # No subcommand needed, prompt via stdin

    def build_evaluation_command(
        self,
        original_prompt: str,
        solution_to_evaluate: str,
        other_solutions: List[str]
    ) -> List[str]:
        """Build command for evaluation."""
        # Just return empty list, prompt will be sent via stdin
        return []

    def build_enhancement_command(self, initial_prompt: str, max_questions: int) -> List[str]:
        """Build command for generating questions."""
        # Just return empty list, prompt will be sent via stdin
        return []

    def parse_output(self, stdout: str, stderr: str) -> tuple[str, Optional[str], Optional[str]]:
        """Parse Gemini CLI output."""
        content = stdout.strip()

        # Gemini often outputs Markdown with code blocks
        code = None
        if "```" in content:
            import re
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', content, re.DOTALL)
            if code_blocks:
                code = code_blocks[0].strip()

        explanation = content.split("```")[0].strip() if "```" in content else content

        return content, code, explanation

    def _format_prompt(self, prompt: str, context: Optional[Dict[str, Any]]) -> str:
        """Format prompt with context."""
        if not context:
            return prompt

        context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
        return f"""Context:
{context_str}

{prompt}"""

    def _use_stdin(self) -> bool:
        """Gemini CLI expects input via stdin."""
        return True


class GeminiAskCLIAgent(BaseCLIAgent):
    """
    Alternative Gemini CLI using 'gemini-ask' or similar variant.
    """

    def __init__(self, name: str = "Gemini Ask", command: str = "gemini-ask"):
        super().__init__(name, command)

    def build_query_command(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Build query command."""
        full_prompt = self._format_prompt(prompt, context)
        return [full_prompt]

    def build_evaluation_command(
        self,
        original_prompt: str,
        solution_to_evaluate: str,
        other_solutions: List[str]
    ) -> List[str]:
        """Build evaluation command."""
        eval_prompt = f"Rate 0-100: {solution_to_evaluate[:500]}"
        return [eval_prompt]

    def build_enhancement_command(self, initial_prompt: str, max_questions: int) -> List[str]:
        """Build enhancement command."""
        return [f"Ask {max_questions} clarifying questions about: {initial_prompt}"]

    def parse_output(self, stdout: str, stderr: str) -> tuple[str, Optional[str], Optional[str]]:
        """Parse output."""
        content = stdout.strip()

        code = None
        if "```" in content:
            import re
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', content, re.DOTALL)
            if code_blocks:
                code = code_blocks[0].strip()

        explanation = content.split("```")[0].strip() if "```" in content else content

        return content, code, explanation

    def _format_prompt(self, prompt: str, context: Optional[Dict[str, Any]]) -> str:
        """Format prompt."""
        if not context:
            return prompt
        context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
        return f"Context: {context_str}\n\n{prompt}"
