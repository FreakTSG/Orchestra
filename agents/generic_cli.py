"""Generic CLI agent template - works with any CLI-based AI tool."""

from typing import Optional, Dict, Any, List
from .base_cli import BaseCLIAgent, AgentResponse


class GenericCLIAgent(BaseCLIAgent):
    """
    Generic CLI agent that can work with any command-line AI tool.

    This is useful for:
    - Custom AI CLI tools
    - Tools not specifically implemented
    - Testing new CLI tools

    Example usage:
        agent = GenericCLIAgent(
            name="MyAI",
            command="my-ai-cli",
            query_args=["ask", "{prompt}"],
            eval_args=["evaluate", "{prompt}"],
            enhance_args=["clarify", "{prompt}"]
        )
    """

    def __init__(
        self,
        name: str,
        command: str,
        query_args: Optional[List[str]] = None,
        eval_args: Optional[List[str]] = None,
        enhance_args: Optional[List[str]] = None
    ):
        """
        Initialize generic CLI agent.

        Args:
            name: Display name
            command: CLI command to run
            query_args: Argument template for queries (use "{prompt}" as placeholder)
            eval_args: Argument template for evaluation
            enhance_args: Argument template for prompt enhancement
        """
        super().__init__(name, command)

        # Default argument templates
        self.query_args = query_args or ["ask", "{prompt}"]
        self.eval_args = eval_args or ["evaluate", "{prompt}"]
        self.enhance_args = enhance_args or ["clarify", "{prompt}"]

    def build_query_command(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Build query command using argument template."""
        full_prompt = self._format_prompt(prompt, context)
        return self._build_args_from_template(self.query_args, full_prompt)

    def build_evaluation_command(
        self,
        original_prompt: str,
        solution_to_evaluate: str,
        other_solutions: List[str]
    ) -> List[str]:
        """Build evaluation command."""
        eval_prompt = f"Rate this solution 0-100:\n{solution_to_evaluate[:800]}"
        return self._build_args_from_template(self.eval_args, eval_prompt)

    def build_enhancement_command(self, initial_prompt: str, max_questions: int) -> List[str]:
        """Build enhancement command."""
        prompt = f"Generate {max_questions} clarifying questions for: {initial_prompt}"
        return self._build_args_from_template(self.enhance_args, prompt)

    def parse_output(self, stdout: str, stderr: str) -> tuple[str, Optional[str], Optional[str]]:
        """Parse output - generic implementation."""
        content = stdout.strip()

        # Try to extract code blocks
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
        return f"Context:\n{context_str}\n\n{prompt}"

    def _build_args_from_template(self, template: List[str], prompt: str) -> List[str]:
        """Replace {prompt} placeholder in argument template."""
        args = []
        for arg in template:
            if "{prompt}" in arg:
                args.append(arg.replace("{prompt}", prompt))
            else:
                args.append(arg)
        return args


class AutoCLIAgent(BaseCLIAgent):
    """
    Auto-detecting CLI agent that tries common patterns.

    Useful when you don't know the exact CLI syntax.
    It will try different command patterns until one works.
    """

    def __init__(self, name: str, command: str):
        super().__init__(name, command)
        self.working_pattern = None

        # Common CLI patterns to try
        self.query_patterns = [
            ["ask", "{prompt}"],
            ["chat", "{prompt}"],
            ["query", "{prompt}"],
            ["generate", "{prompt}"],
            ["--prompt", "{prompt}"],
            ["-p", "{prompt}"],
            ["{prompt}"],  # Direct argument
        ]

    def build_query_command(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Build query command, trying different patterns."""
        full_prompt = self._format_prompt(prompt, context)

        if self.working_pattern:
            return self._build_args(self.working_pattern, full_prompt)

        # Use first pattern by default
        return self._build_args(self.query_patterns[0], full_prompt)

    def build_evaluation_command(
        self,
        original_prompt: str,
        solution_to_evaluate: str,
        other_solutions: List[str]
    ) -> List[str]:
        """Build evaluation command."""
        eval_prompt = f"Rate 0-100: {solution_to_evaluate[:500]}"
        return ["ask", eval_prompt]  # Common pattern

    def build_enhancement_command(self, initial_prompt: str, max_questions: int) -> List[str]:
        """Build enhancement command."""
        prompt = f"Generate {max_questions} questions for: {initial_prompt}"
        return ["ask", prompt]

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

    def _build_args(self, pattern: List[str], prompt: str) -> List[str]:
        """Build args from pattern."""
        args = []
        for arg in pattern:
            if "{prompt}" in arg:
                args.append(arg.replace("{prompt}", prompt))
            else:
                args.append(arg)
        return args


class FileBasedCLIAgent(BaseCLIAgent):
    """
    CLI agent that writes prompts to files (for CLIs that expect file input).

    Some AI CLIs expect input from a file rather than command-line args.
    """

    def __init__(self, name: str, command: str, temp_dir: str = "/tmp"):
        super().__init__(name, command)
        self.temp_dir = temp_dir
        import tempfile
        self.temp_dir = tempfile.gettempdir()

    def build_query_command(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Build command that reads from file."""
        import tempfile
        import os

        full_prompt = self._format_prompt(prompt, context)

        # Write prompt to temp file
        fd, temp_path = tempfile.mkstemp(suffix='.txt', dir=self.temp_dir)
        with os.fdopen(fd, 'w') as f:
            f.write(full_prompt)

        # Return command that reads from file
        return ["--file", temp_path]

    def build_evaluation_command(
        self,
        original_prompt: str,
        solution_to_evaluate: str,
        other_solutions: List[str]
    ) -> List[str]:
        """Build evaluation command."""
        import tempfile
        import os

        eval_prompt = f"Rate 0-100:\n{solution_to_evaluate[:800]}"

        fd, temp_path = tempfile.mkstemp(suffix='.txt', dir=self.temp_dir)
        with os.fdopen(fd, 'w') as f:
            f.write(eval_prompt)

        return ["--file", temp_path]

    def build_enhancement_command(self, initial_prompt: str, max_questions: int) -> List[str]:
        """Build enhancement command."""
        import tempfile
        import os

        prompt = f"Generate {max_questions} questions for: {initial_prompt}"

        fd, temp_path = tempfile.mkstemp(suffix='.txt', dir=self.temp_dir)
        with os.fdopen(fd, 'w') as f:
            f.write(prompt)

        return ["--file", temp_path]

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
