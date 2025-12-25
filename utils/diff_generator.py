"""Generate diffs for file changes."""

from typing import List, Dict, Any, Optional
from pathlib import Path
from difflib import unified_diff
from dataclasses import dataclass

from utils.code_parser import FileOperation, OperationType


@dataclass
class FileDiff:
    """Represents a diff for a single file."""
    operation: OperationType
    file_path: str
    old_content: Optional[str]
    new_content: Optional[str]
    unified_diff: str
    stats: Dict[str, int]


class DiffGenerator:
    """Generate diffs for proposed file changes."""

    def __init__(self, working_directory: str = "."):
        """
        Initialize diff generator.

        Args:
            working_directory: Base directory for file operations
        """
        self.working_dir = Path(working_directory).resolve()

    def generate_diffs(self, operations: List[FileOperation]) -> List[FileDiff]:
        """
        Generate diffs for a list of file operations.

        Args:
            operations: List of FileOperation objects

        Returns:
            List of FileDiff objects
        """
        diffs = []

        for op in operations:
            diff = self._generate_diff_for_operation(op)
            if diff:
                diffs.append(diff)

        return diffs

    def _generate_diff_for_operation(self, operation: FileOperation) -> Optional[FileDiff]:
        """Generate diff for a single operation."""
        file_path = self.working_dir / operation.file_path

        old_content = None
        if operation.op_type in [OperationType.MODIFY, OperationType.DELETE]:
            # Read existing file
            try:
                old_content = file_path.read_text(encoding='utf-8', errors='ignore')
            except FileNotFoundError:
                old_content = None
            except Exception:
                old_content = None

        new_content = operation.content

        # Generate unified diff
        diff_text = self._create_unified_diff(
            operation.file_path,
            old_content,
            new_content,
            operation.op_type
        )

        # Calculate stats
        stats = self._calculate_stats(old_content, new_content)

        return FileDiff(
            operation=operation.op_type,
            file_path=operation.file_path,
            old_content=old_content,
            new_content=new_content,
            unified_diff=diff_text,
            stats=stats
        )

    def _create_unified_diff(
        self,
        file_path: str,
        old_content: Optional[str],
        new_content: Optional[str],
        op_type: OperationType
    ) -> str:
        """Create a unified diff."""
        old_lines = old_content.splitlines(keepends=True) if old_content else []
        new_lines = new_content.splitlines(keepends=True) if new_content else []

        if op_type == OperationType.CREATE:
            # New file
            header = f"+++ {file_path} (new file)\n"
            if new_lines:
                diff_content = ''.join(f"+{line}" if not line.startswith('+') else line for line in new_lines)
                return header + diff_content
            return header + "// New file\n"

        elif op_type == OperationType.DELETE:
            # Deleted file
            header = f"--- {file_path} (deleted)\n"
            if old_lines:
                diff_content = ''.join(f"-{line}" if not line.startswith('-') else line for line in old_lines)
                return header + diff_content
            return header + "// Deleted file\n"

        else:  # MODIFY
            # Modified file - use actual diff
            diff_lines = list(unified_diff(
                old_lines,
                new_lines,
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
                lineterm=""
            ))

            if not diff_lines:
                # No changes detected
                return f"--- {file_path}\n+++ {file_path}\n// No changes\n"

            return ''.join(diff_lines)

    def _calculate_stats(
        self,
        old_content: Optional[str],
        new_content: Optional[str]
    ) -> Dict[str, int]:
        """Calculate diff statistics."""
        old_lines = old_content.splitlines() if old_content else []
        new_lines = new_content.splitlines() if new_content else []

        return {
            "old_lines": len(old_lines),
            "new_lines": len(new_lines),
            "lines_added": max(0, len(new_lines) - len(old_lines)),
            "lines_removed": max(0, len(old_lines) - len(new_lines)),
            "chars_added": len(new_content) if new_content else 0,
            "chars_removed": len(old_content) if old_content else 0,
        }

    def format_diff_summary(self, diffs: List[FileDiff]) -> str:
        """Format a summary of all diffs."""
        if not diffs:
            return "No changes detected"

        lines = ["\n📊 Changes Summary", "=" * 60]

        total_files = 0
        total_additions = 0
        total_deletions = 0

        for diff in diffs:
            total_files += 1
            total_additions += diff.stats['lines_added']
            total_deletions += diff.stats['lines_removed']

            icon = {
                OperationType.CREATE: "✨",
                OperationType.MODIFY: "✏️",
                OperationType.DELETE: "🗑️",
            }.get(diff.operation, "📄")

            lines.append(f"\n{icon} {diff.operation.value.upper()}: {diff.file_path}")
            lines.append(f"   Lines: +{diff.stats['lines_added']} -{diff.stats['lines_removed']}")

        lines.append(f"\n{'=' * 60}")
        lines.append(f"Total: {total_files} files, +{total_additions} -{total_deletions} lines")

        return "\n".join(lines)

    def format_detailed_diff(self, diff: FileDiff, context_lines: int = 3) -> str:
        """Format a detailed diff for a single file."""
        lines = [f"\n{'=' * 60}"]
        lines.append(f"File: {diff.file_path} ({diff.operation.value})")
        lines.append(f"Lines: +{diff.stats['lines_added']} -{diff.stats['lines_removed']}")
        lines.append(f"{'=' * 60}\n")

        if diff.unified_diff:
            # Show limited context
            diff_lines = diff.unified_diff.split('\n')

            # If diff is too long, truncate
            if len(diff_lines) > 100:
                lines.extend(diff_lines[:50])
                lines.append("\n... (truncated, showing first 50 lines)")
                lines.extend(diff_lines[-10:])
            else:
                lines.extend(diff_lines)

        elif diff.operation == OperationType.CREATE:
            lines.append("✨ New file will be created")
            lines.append("```" + (diff.operation.language or "") + "")
            lines.append(diff.new_content or "// Empty file")
            lines.append("```")

        return "\n".join(lines)

    def apply_changes(self, diffs: List[FileDiff], dry_run: bool = False) -> Dict[str, Any]:
        """
        Apply file changes.

        Args:
            diffs: List of FileDiff objects
            dry_run: If True, don't actually make changes

        Returns:
            Summary of applied changes
        """
        results = {
            "success": [],
            "failed": [],
            "skipped": []
        }

        for diff in diffs:
            try:
                file_path = self.working_dir / diff.file_path

                if dry_run:
                    results["success"].append(diff.file_path)
                    continue

                # Create parent directories if needed
                file_path.parent.mkdir(parents=True, exist_ok=True)

                if diff.operation == OperationType.DELETE:
                    if file_path.exists():
                        file_path.unlink()
                        results["success"].append(diff.file_path)
                    else:
                        results["skipped"].append(diff.file_path)

                else:
                    # CREATE or MODIFY
                    file_path.write_text(
                        diff.new_content or "",
                        encoding='utf-8'
                    )
                    results["success"].append(diff.file_path)

            except Exception as e:
                results["failed"].append({
                    "file": diff.file_path,
                    "error": str(e)
                })

        return results
