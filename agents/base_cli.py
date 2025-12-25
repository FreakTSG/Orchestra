"""Base CLI agent interface - uses subprocess to call CLI tools."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel
import subprocess
import json
import asyncio
from pathlib import Path


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
    command_used: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time_ms: Optional[int] = None

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
            "command_used": self.command_used,
            "exit_code": self.exit_code,
            "execution_time_ms": self.execution_time_ms,
        }


class BaseCLIAgent(ABC):
    """Abstract base class for CLI-based AI agents."""

    def __init__(self, name: str, command: str):
        """
        Initialize CLI agent.

        Args:
            name: Display name for the agent
            command: CLI command to invoke (e.g., "claude", "gemini-cli")
        """
        self.name = name
        self.command = command
        self.agent_type = self.__class__.__name__
        self.available = self._check_available()

    def _check_available(self) -> bool:
        """Check if the CLI tool is available."""
        import shutil
        import sys

        # First, check if command exists using shutil.which (works on all platforms)
        cmd_path = shutil.which(self.command)

        if not cmd_path:
            # Try adding common extensions on Windows
            if sys.platform == 'win32':
                for ext in ['.cmd', '.bat', '.exe']:
                    if shutil.which(self.command + ext):
                        cmd_path = shutil.which(self.command + ext)
                        break

            # If still not found, return False
            if not cmd_path:
                return False

        # Command found! It's available.
        # The version check below is just for verification, but we already know it exists.
        # Try to verify it works, but don't fail if verification fails
        try:
            # Quick verification - try to run with minimal timeout
            use_shell = sys.platform == 'win32' and cmd_path.lower().endswith(('.cmd', '.bat'))

            subprocess.run(
                [self.command, "--version"],
                capture_output=True,
                timeout=2,  # Very short timeout just to check if it responds
                text=True,
                shell=use_shell
            )
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            # Verification failed, but command exists so it's available
            pass

        return True

    @abstractmethod
    def build_query_command(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Build the command list for querying the agent.

        Args:
            prompt: The prompt to send
            context: Optional context

        Returns:
            List of command arguments (e.g., ["claude", "ask", prompt])
        """
        pass

    @abstractmethod
    def build_evaluation_command(
        self,
        original_prompt: str,
        solution_to_evaluate: str,
        other_solutions: List[str]
    ) -> List[str]:
        """
        Build command for evaluating another solution.

        Args:
            original_prompt: Original problem statement
            solution_to_evaluate: Solution to evaluate
            other_solutions: Other solutions for comparison

        Returns:
            List of command arguments
        """
        pass

    @abstractmethod
    def build_enhancement_command(self, initial_prompt: str, max_questions: int) -> List[str]:
        """
        Build command for generating clarifying questions.

        Args:
            initial_prompt: User's initial prompt
            max_questions: Maximum questions to generate

        Returns:
            List of command arguments
        """
        pass

    @abstractmethod
    def parse_output(self, stdout: str, stderr: str) -> tuple[str, Optional[str], Optional[str]]:
        """
        Parse the CLI output into content, code, and explanation.

        Args:
            stdout: Standard output from CLI
            stderr: Standard error from CLI

        Returns:
            Tuple of (content, code, explanation)
        """
        pass

    async def query(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Send a query to the CLI agent."""
        import time
        start_time = time.time()

        command = self.build_query_command(prompt, context)
        full_command = [self.command] + command
        use_shell = self._should_use_shell()

        # Format prompt for stdin (if needed)
        stdin_prompt = self._format_prompt_for_stdin(prompt, context) if self._use_stdin() else None

        try:
            if use_shell:
                # On Windows with .cmd files, use shell=True
                # Convert list to string for shell execution
                cmd_str = " ".join(full_command)
                process = await asyncio.create_subprocess_shell(
                    cmd_str,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.PIPE if stdin_prompt else None
                )
            else:
                # Normal subprocess execution
                process = await asyncio.create_subprocess_exec(
                    *full_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.PIPE if stdin_prompt else None
                )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=stdin_prompt.encode() if stdin_prompt else None),
                timeout=120  # 2 minute timeout
            )

            execution_time_ms = int((time.time() - start_time) * 1000)
            stdout_text = stdout.decode('utf-8', errors='ignore')
            stderr_text = stderr.decode('utf-8', errors='ignore')

            # Parse output
            content, code, explanation = self.parse_output(stdout_text, stderr_text)

            return AgentResponse(
                agent_name=self.name,
                agent_type=self.agent_type,
                content=content,
                code=code,
                explanation=explanation,
                command_used=" ".join(full_command),
                exit_code=process.returncode,
                execution_time_ms=execution_time_ms,
                metadata={
                    "has_stderr": bool(stderr_text),
                    "stderr_preview": stderr_text[:200] if stderr_text else None,
                    "used_shell": use_shell
                }
            )

        except asyncio.TimeoutError:
            return AgentResponse(
                agent_name=self.name,
                agent_type=self.agent_type,
                content=f"Error: Command timed out after 120 seconds",
                metadata={"error": "timeout"}
            )
        except Exception as e:
            return AgentResponse(
                agent_name=self.name,
                agent_type=self.agent_type,
                content=f"Error: {str(e)}",
                metadata={"error": str(e)}
            )

    async def evaluate(
        self,
        original_prompt: str,
        solution_to_evaluate: AgentResponse,
        other_solutions: List[AgentResponse]
    ) -> float:
        """Evaluate another agent's solution."""
        command_parts = self.build_evaluation_command(
            original_prompt,
            solution_to_evaluate.content,
            [s.content for s in other_solutions]
        )

        full_command = [self.command] + command_parts
        use_shell = self._should_use_shell()

        # Build evaluation prompt for stdin
        eval_prompt = self._build_evaluation_prompt(original_prompt, solution_to_evaluate, other_solutions)
        stdin_input = eval_prompt.encode() if self._use_stdin() else None

        try:
            if use_shell:
                cmd_str = " ".join(full_command)
                process = await asyncio.create_subprocess_shell(
                    cmd_str,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.PIPE if stdin_input else None
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    *full_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.PIPE if stdin_input else None
                )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=stdin_input),
                timeout=60
            )

            output = stdout.decode('utf-8', errors='ignore')
            score = self._extract_score(output)

            return max(0, min(100, score))

        except Exception:
            return 50.0  # Return neutral score on error

    async def enhance_prompt(
        self,
        initial_prompt: str,
        max_questions: int = 3
    ) -> tuple[List[str], str]:
        """Generate clarifying questions to improve the prompt."""
        command_parts = self.build_enhancement_command(initial_prompt, max_questions)
        full_command = [self.command] + command_parts
        use_shell = self._should_use_shell()

        # Build enhancement prompt for stdin
        enhance_prompt = self._build_enhancement_prompt(initial_prompt, max_questions)
        stdin_input = enhance_prompt.encode() if self._use_stdin() else None

        try:
            if use_shell:
                cmd_str = " ".join(full_command)
                process = await asyncio.create_subprocess_shell(
                    cmd_str,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.PIPE if stdin_input else None
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    *full_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.PIPE if stdin_input else None
                )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=stdin_input),
                timeout=60
            )

            output = stdout.decode('utf-8', errors='ignore')
            questions = self._parse_questions(output)

            enhanced = f"""Enhanced Request:

Original: {initial_prompt}

Clarifications:
"""
            for i, q in enumerate(questions, 1):
                enhanced += f"{i}. {q}\n"

            return questions, enhanced

        except Exception:
            # Fallback questions
            return [
                "What programming language are you using?",
                "Are there any specific constraints or requirements?",
                "What is the expected output or behavior?"
            ], initial_prompt

    def _use_stdin(self) -> bool:
        """Whether this agent expects input via stdin."""
        return False

    def _format_prompt_for_stdin(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Format prompt for stdin input. Override in subclasses if needed."""
        if not context:
            return prompt

        context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
        return f"""Context:
{context_str}

{prompt}"""

    def _build_evaluation_prompt(
        self,
        original_prompt: str,
        solution_to_evaluate: AgentResponse,
        other_solutions: List[AgentResponse]
    ) -> str:
        """Build evaluation prompt for stdin. Override in subclasses if needed."""
        return f"""Rate this solution from 0-100:

Problem: {original_prompt}

Solution:
{solution_to_evaluate.content[:1000]}

Other solutions for reference:
{chr(10).join(f'- {s.content[:200]}...' for s in other_solutions[:2])}

Respond with only a number from 0-100."""

    def _build_enhancement_prompt(self, initial_prompt: str, max_questions: int) -> str:
        """Build enhancement prompt for stdin. Override in subclasses if needed."""
        return f"""Generate {max_questions} clarifying questions for this coding request:

{initial_prompt}

Questions should clarify:
- Programming language/framework
- Specific requirements
- Constraints
- Expected behavior

Output {max_questions} questions, each on a new line."""

    def _should_use_shell(self) -> bool:
        """Check if we should use shell=True for subprocess calls."""
        import shutil
        import sys
        cmd_path = shutil.which(self.command)
        return sys.platform == 'win32' and cmd_path and cmd_path.lower().endswith(('.cmd', '.bat'))

    def _extract_score(self, output: str) -> float:
        """Extract a numeric score from agent output."""
        import re
        # Look for numbers like "85", "85.5", "85/100"
        matches = re.findall(r'(\d+(?:\.\d+)?)', output)
        if matches:
            try:
                score = float(matches[0])
                return max(0, min(100, score))
            except ValueError:
                pass
        return 50.0

    def _parse_questions(self, output: str) -> List[str]:
        """Parse questions from agent output."""
        questions = []
        for line in output.split('\n'):
            line = line.strip()
            if line and (line.endswith('?') or line.startswith(('Q:', 'Question', '-'))):
                # Clean up the question
                q = line.lstrip('Q:').lstrip('Question').lstrip('-').strip()
                if q:
                    questions.append(q)
        return questions[:3]  # Max 3 questions

    def __repr__(self) -> str:
        status = "✓" if self.available else "✗"
        return f"{self.__class__.__name__}(name='{self.name}', status='{status}')"
