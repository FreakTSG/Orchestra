"""Parse agent responses to detect file operations."""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class OperationType(Enum):
    """Types of file operations."""
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    UNKNOWN = "unknown"


@dataclass
class FileOperation:
    """Represents a file operation."""
    op_type: OperationType
    file_path: str
    content: Optional[str]
    line_start: Optional[int]
    line_end: Optional[int]
    language: Optional[str]


class CodeParser:
    """Parse agent responses to extract file operations."""

    # Patterns to detect file paths in various formats
    FILE_PATTERNS = [
        r'(?:File:|📄|→)\s*([^\s:]+\.[a-z]+)',
        r'(?:create|modify|delete|update)\s+(?:file\s+)?[`"\'"]?([^\s`"\']+\.[a-z]+)[`"\'"]?',
        r'(?:in\s+)?([a-zA-Z]:[/\\\\][^\s]+\.[a-z]+)',  # Windows paths
        r'([~/][^\s]+\.[a-z]+)',  # Unix paths
        r'(?:^|\n)\s*#?\s*([a-zA-Z_][a-zA-Z0-9_]*\.[a-z]+)',  # Bare filenames
    ]

    # Code block patterns
    CODE_BLOCK_PATTERNS = [
        r'```(\w*)\n(.*?)```',
        r'`([^`]+)`',  # Inline code
    ]

    def __init__(self):
        """Initialize the parser."""
        pass

    def parse_response(self, response_text: str) -> List[FileOperation]:
        """
        Parse agent response and extract file operations.

        Args:
            response_text: The agent's response text

        Returns:
            List of FileOperation objects
        """
        operations = []

        # Extract all code blocks
        code_blocks = self._extract_code_blocks(response_text)

        # Try to associate each code block with a file path
        for i, (language, code) in enumerate(code_blocks):
            op = self._detect_operation_for_block(response_text, code, i, language)
            if op:
                operations.append(op)

        return operations

    def _extract_code_blocks(self, text: str) -> List[tuple]:
        """Extract code blocks from response."""
        blocks = []

        # Multi-line code blocks
        for match in re.finditer(r'```(\w*)\n(.*?)```', text, re.DOTALL):
            language = match.group(1) if match.group(1) else 'text'
            code = match.group(2).strip()
            blocks.append((language, code))

        # If no code blocks found, look for any code-like content
        if not blocks:
            # Look for indented code blocks
            lines = text.split('\n')
            current_block = []
            in_code_block = False

            for line in lines:
                if line.startswith('    ') or line.startswith('\t'):
                    current_block.append(line)
                    in_code_block = True
                elif in_code_block:
                    current_block.append(line)
                    if not line.strip():
                        blocks.append(('text', '\n'.join(current_block)))
                        current_block = []
                        in_code_block = False

            if current_block:
                blocks.append(('text', '\n'.join(current_block)))

        return blocks

    def _detect_operation_for_block(
        self,
        full_response: str,
        code_block: str,
        block_index: int,
        language: str
    ) -> Optional[FileOperation]:
        """Detect what file operation this code block represents."""

        # Look for file path mentions before the code block
        text_before = full_response.split(code_block)[0] if code_block in full_response else ""

        # Extract file path from text before the block
        file_path = self._extract_file_path(text_before)

        if not file_path:
            # Try to infer from the code itself
            file_path = self._infer_file_path_from_code(code_block, language)

        if not file_path:
            # Generate a default filename
            file_path = self._generate_default_filename(code_block, language, block_index)

        # Detect operation type from context
        op_type = self._detect_operation_type(text_before, file_path, code_block)

        return FileOperation(
            op_type=op_type,
            file_path=file_path,
            content=code_block,
            line_start=None,
            line_end=None,
            language=language if language != 'text' else None
        )

    def _extract_file_path(self, text: str) -> Optional[str]:
        """Extract file path from text."""
        # Try each pattern
        for pattern in self.FILE_PATTERNS:
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
            if matches:
                # Return the last mentioned file (most likely to be the current one)
                return matches[-1].strip()

        return None

    def _infer_file_path_from_code(self, code: str, language: str) -> Optional[str]:
        """Infer file path from code content."""
        # Look for class/function definitions to guess filename
        if language == 'python':
            # Look for class definitions
            class_match = re.search(r'^class\s+(\w+)', code, re.MULTILINE)
            if class_match:
                class_name = class_match.group(1)
                return f"{class_name.lower()}.py"

        elif language in ['javascript', 'typescript']:
            # Look for class or function exports
            class_match = re.search(r'class\s+(\w+)', code)
            if class_match:
                return f"{class_match.group(1).lower()}.js"

        return None

    def _generate_default_filename(self, code: str, language: str, index: int) -> str:
        """Generate a default filename for the code."""
        extensions = {
            'python': '.py',
            'javascript': '.js',
            'typescript': '.ts',
            'java': '.java',
            'go': '.go',
            'rust': '.rs',
            'c': '.c',
            'cpp': '.cpp',
            'html': '.html',
            'css': '.css',
            'json': '.json',
            'yaml': '.yaml',
            'yml': '.yml',
        }

        ext = extensions.get(language, '.txt')

        # Try to guess a meaningful name from the code
        if 'binary_search' in code.lower() or 'binary search' in code.lower():
            return f"binary_search{ext}"
        elif 'main' in code.lower():
            return f"main{ext}"
        elif 'utils' in code.lower():
            return f"utils{ext}"
        elif 'test' in code.lower():
            return f"test{ext}"
        else:
            return f"code_{index + 1}{ext}"

    def _detect_operation_type(self, text_before: str, file_path: str, code: str) -> OperationType:
        """Detect what type of operation this is."""
        text_lower = text_before.lower()

        # Check for explicit operation keywords
        if any(word in text_lower for word in ['create', 'new file', 'add file', 'write to']):
            return OperationType.CREATE
        elif any(word in text_lower for word in ['modify', 'update', 'change', 'edit', 'refactor']):
            return OperationType.MODIFY
        elif any(word in text_lower for word in ['delete', 'remove']):
            return OperationType.DELETE

        # If file is mentioned with "implement" or just appears, assume create
        if any(word in text_lower for word in ['implement', 'create', 'add', 'write']):
            return OperationType.CREATE

        # Default to create
        return OperationType.CREATE

    def get_summary(self, operations: List[FileOperation]) -> str:
        """Get a text summary of operations."""
        if not operations:
            return "No file operations detected"

        lines = ["\n📁 File Operations:"]
        lines.append("=" * 60)

        for op in operations:
            icon = {
                OperationType.CREATE: "✨",
                OperationType.MODIFY: "✏️",
                OperationType.DELETE: "🗑️",
            }.get(op.op_type, "📄")

            lines.append(f"\n{icon} {op.op_type.value.upper()}: {op.file_path}")

            if op.language:
                lines.append(f"   Language: {op.language}")

            if op.content:
                lines_count = len(op.content.split('\n'))
                preview = op.content.split('\n')[0][:60]
                lines.append(f"   Lines: {lines_count}")
                lines.append(f"   Preview: {preview}...")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


def parse_agent_response(response_text: str) -> List[FileOperation]:
    """
    Convenience function to parse an agent response.

    Args:
        response_text: The agent's response text

    Returns:
        List of FileOperation objects
    """
    parser = CodeParser()
    return parser.parse_response(response_text)
