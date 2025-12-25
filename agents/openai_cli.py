"""OpenAI/Codex CLI agent implementation."""

from typing import Optional, Dict, Any, List
from .base_cli import BaseCLIAgent, AgentResponse


class OpenAICLIAgent(BaseCLIAgent):
    """
    OpenAI CLI agent.

    Assumes 'openai' CLI tool is installed.
    Installation: npm install -g openai-cli
    Or via: pip install openai-cli
    """

    def __init__(self, name: str = "OpenAI CLI", command: str = "openai"):
        super().__init__(name, command)

    def build_query_command(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Build command for querying OpenAI CLI."""
        full_prompt = self._format_prompt(prompt, context)

        # OpenAI CLI patterns:
        # - openai api completions.create -m gpt-4 -p "prompt"
        # - openai chat "prompt"
        # - openai ask "prompt"

        return ["chat", full_prompt]

        # Alternative for API-style calls:
        # return ["api", "completions.create", "-m", "gpt-4", "-p", full_prompt]

    def build_evaluation_command(
        self,
        original_prompt: str,
        solution_to_evaluate: str,
        other_solutions: List[str]
    ) -> List[str]:
        """Build command for evaluation."""
        eval_prompt = f"""Rate this solution 0-100:

Problem: {original_prompt}
Solution: {solution_to_evaluate[:800]}

Consider correctness, quality, and efficiency.
Respond with just a number."""

        return ["chat", eval_prompt]

    def build_enhancement_command(self, initial_prompt: str, max_questions: int) -> List[str]:
        """Build command for generating questions."""
        prompt = f"""Generate {max_questions} clarifying questions for: {initial_prompt}

Cover:
- Language/framework
- Requirements
- Constraints

Output {max_questions} questions, one per line."""

        return ["chat", prompt]

    def parse_output(self, stdout: str, stderr: str) -> tuple[str, Optional[str], Optional[str]]:
        """Parse OpenAI CLI output."""
        content = stdout.strip()

        # Extract code blocks
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


class CodexCLIAgent(BaseCLIAgent):
    """
    Codex CLI agent (if separate from OpenAI CLI).

    For OpenAI Codex specifically.
    """

    def __init__(self, name: str = "Codex CLI", command: str = "codex"):
        super().__init__(name, command)

    def build_query_command(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Build command for Codex CLI."""
        full_prompt = self._format_prompt(prompt, context)
        return ["generate", full_prompt]

    def build_evaluation_command(
        self,
        original_prompt: str,
        solution_to_evaluate: str,
        other_solutions: List[str]
    ) -> List[str]:
        """Build evaluation command."""
        eval_prompt = f"Score 0-100: {solution_to_evaluate[:500]}"
        return ["evaluate", eval_prompt]

    def build_enhancement_command(self, initial_prompt: str, max_questions: int) -> List[str]:
        """Build enhancement command."""
        return [f"Generate {max_questions} questions for: {initial_prompt}"]

    def parse_output(self, stdout: str, stderr: str) -> tuple[str, Optional[str], Optional[str]]:
        """Parse Codex output."""
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


class GPT4CLIAgent(BaseCLIAgent):
    """
    GPT-4 specific CLI agent.

    If you have a specific CLI for GPT-4.
    """

    def __init__(self, name: str = "GPT-4 CLI", command: str = "gpt4"):
        super().__init__(name, command)

    def build_query_command(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Build command for GPT-4 CLI."""
        full_prompt = self._format_prompt(prompt, context)
        return ["ask", full_prompt]

    def build_evaluation_command(
        self,
        original_prompt: str,
        solution_to_evaluate: str,
        other_solutions: List[str]
    ) -> List[str]:
        """Build evaluation command."""
        return ["ask", f"Rate 0-100: {solution_to_evaluate[:800]}"]

    def build_enhancement_command(self, initial_prompt: str, max_questions: int) -> List[str]:
        """Build enhancement command."""
        return ["ask", f"Generate {max_questions} clarifying questions for: {initial_prompt}"]

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
        return f"Context: {context}\n\n{prompt}"
