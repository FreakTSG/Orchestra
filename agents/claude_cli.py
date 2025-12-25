"""Claude Code CLI agent implementation."""

from typing import Optional, Dict, Any, List
from .base_cli import BaseCLIAgent, AgentResponse


class ClaudeCLIAgent(BaseCLIAgent):
    """
    Claude Code CLI agent.

    Assumes the 'claude' CLI tool is installed and in PATH.
    Typical installation: npm install -g @anthropic-ai/claude-code
    """

    def __init__(self, name: str = "Claude CLI", command: str = "claude"):
        super().__init__(name, command)

    def build_query_command(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Build command for querying Claude CLI."""
        # Claude CLI needs: claude ask (then prompt via stdin)
        return ["ask"]  # Prompt will be sent via stdin

    def build_evaluation_command(
        self,
        original_prompt: str,
        solution_to_evaluate: str,
        other_solutions: List[str]
    ) -> List[str]:
        """Build command for evaluating a solution."""
        # Just return the subcommand, prompt will be sent via stdin
        return ["ask"]

    def build_enhancement_command(self, initial_prompt: str, max_questions: int) -> List[str]:
        """Build command for generating clarifying questions."""
        # Just return the subcommand, prompt will be sent via stdin
        return ["ask"]

    def parse_output(self, stdout: str, stderr: str) -> tuple[str, Optional[str], Optional[str]]:
        """Parse Claude CLI output."""
        # Claude CLI typically outputs Markdown
        content = stdout.strip()

        # Extract code blocks
        code = None
        if "```" in content:
            import re
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', content, re.DOTALL)
            if code_blocks:
                code = code_blocks[0].strip()

        # Explanation is everything before the first code block
        explanation = None
        if "```" in content:
            explanation = content.split("```")[0].strip()
        elif content:
            explanation = content

        return content, code, explanation

    def _format_prompt(self, prompt: str, context: Optional[Dict[str, Any]]) -> str:
        """Format prompt with context."""
        if not context:
            return prompt

        context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
        return f"""Context:
{context_str}

Request:
{prompt}"""

    def _use_stdin(self) -> bool:
        """Claude CLI expects input via stdin."""
        return True


class ClaudeCodeCLIAgent(BaseCLIAgent):
    """
    Alternative Claude Code CLI agent.

    For the newer 'claude-code' CLI tool if different from 'claude'.
    """

    def __init__(self, name: str = "Claude Code", command: str = "claude-code"):
        super().__init__(name, command)

    def build_query_command(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Build command for Claude Code CLI."""
        full_prompt = self._format_prompt(prompt, context)
        return ["prompt", full_prompt]

    def build_evaluation_command(
        self,
        original_prompt: str,
        solution_to_evaluate: str,
        other_solutions: List[str]
    ) -> List[str]:
        """Build evaluation command."""
        eval_prompt = f"""Rate this solution (0-100):

{original_prompt}

Solution: {solution_to_evaluate[:1000]}

Respond with just a number."""

        return ["prompt", eval_prompt]

    def build_enhancement_command(self, initial_prompt: str, max_questions: int) -> List[str]:
        """Build enhancement command."""
        prompt = f"Generate {max_questions} clarifying questions for: {initial_prompt}"
        return ["prompt", prompt]

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
        return f"Context:\n{context_str}\n\n{prompt}"
