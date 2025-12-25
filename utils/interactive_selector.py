"""Interactive UI for selecting and applying solutions."""

import asyncio
from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
import questionary

from agents.base_cli import AgentResponse
from evaluator.cross_evaluator import EvaluationResult
from utils.code_parser import CodeParser, FileOperation
from utils.diff_generator import DiffGenerator, FileDiff


class InteractiveSelector:
    """Interactive UI for selecting and applying solutions."""

    def __init__(self, working_directory: str = "."):
        """
        Initialize the interactive selector.

        Args:
            working_directory: Directory where changes will be applied
        """
        self.console = Console()
        self.working_directory = working_directory
        self.parser = CodeParser()
        self.diff_generator = DiffGenerator(working_directory)

    async def select_solution(
        self,
        evaluation_results: List[EvaluationResult],
        all_responses: List[AgentResponse]
    ) -> Optional[Dict[str, Any]]:
        """
        Guide user through solution selection.

        Args:
            evaluation_results: Ranked evaluation results
            all_responses: All agent responses

        Returns:
            Selected solution info with operations and diffs, or None if cancelled
        """
        # Show ranked solutions
        self._display_solutions(evaluation_results)

        # Prompt for selection
        choices = [
            questionary.Choice(f"{i}. {eval_result.response.agent_name} (Score: {eval_result.average_score:.1f}/100)", value=i)
            for i, eval_result in enumerate(evaluation_results, 1)
        ]
        choices.append(questionary.Choice("0. Cancel and exit", value=0))

        selection = await questionary.select(
            "Select a solution to preview:",
            choices=choices,
            qmark="🔍"
        ).ask_async()

        if selection == 0:
            self.console.print("[yellow]Cancelled.[/yellow]")
            return None

        # Get the selected result
        selected = evaluation_results[selection - 1]

        # Parse file operations from the response
        operations = self.parser.parse_response(selected.response.content)

        if not operations:
            self.console.print("[yellow]⚠️  No file operations detected in this response.[/yellow]")
            self.console.print("The agent provided an explanation but no code changes.")
            return {
                "response": selected.response,
                "operations": [],
                "diffs": [],
                "rank": selection
            }

        # Show what would be changed
        self._display_operations_summary(operations)

        # Generate diffs
        diffs = self.diff_generator.generate_diffs(operations)

        # Show preview
        self._display_diff_preview(diffs)

        # Ask for confirmation
        confirm = await questionary.confirm(
            "Apply these changes?",
            default=False,
            qmark="✨"
        ).ask_async()

        if not confirm:
            self.console.print("[yellow]Changes not applied.[/yellow]")
            return None

        return {
            "response": selected.response,
            "operations": operations,
            "diffs": diffs,
            "rank": selection,
            "agent_name": selected.response.agent_name,
            "score": selected.average_score
        }

    def _display_solutions(self, evaluation_results: List[EvaluationResult]):
        """Display ranked solutions."""
        table = Table(title="\n📊 Agent Solutions Ranked by Quality", show_header=True)
        table.add_column("Rank", style="cyan", width=6)
        table.add_column("Agent", style="green", width=20)
        table.add_column("Score", style="yellow", width=10)
        table.add_column("Time", style="blue", width=10)
        table.add_column("Files", style="magenta", width=8)
        table.add_column("Approach", style="white", width=50)

        for eval_result in evaluation_results:
            medal = "🥇" if eval_result.rank == 1 else "🥈" if eval_result.rank == 2 else "🥉" if eval_result.rank == 3 else "  "

            # Try to parse operations to count files
            operations = self.parser.parse_response(eval_result.response.content)
            file_count = len(operations) if operations else 0

            # Extract approach
            approach = eval_result.response.explanation or eval_result.response.content[:100] + "..."

            table.add_row(
                f"{medal} #{eval_result.rank}",
                eval_result.response.agent_name,
                f"{eval_result.average_score:.1f}/100",
                f"{eval_result.response.execution_time_ms}ms" if eval_result.response.execution_time_ms else "N/A",
                f"{file_count} files" if file_count > 0 else "No files",
                approach
            )

        self.console.print(table)

    def _display_operations_summary(self, operations: List[FileOperation]):
        """Display summary of file operations."""
        summary = self.parser.get_summary(operations)
        self.console.print(summary)

    def _display_diff_preview(self, diffs: List[FileDiff]):
        """Display preview of changes."""
        if not diffs:
            return

        # Overall summary
        summary = self.diff_generator.format_diff_summary(diffs)
        self.console.print(summary)

        # Detailed diffs for each file
        for diff in diffs[:3]:  # Show max 3 files in preview
            detailed = self.diff_generator.format_detailed_diff(diff)
            self.console.print(Panel(detailed, border_style="cyan"))

            if len(diffs) > 3:
                self.console.print(f"\n[dim]... and {len(diffs) - 3} more file(s)[/dim]")
                break


async def select_and_apply(
    evaluation_results: List[EvaluationResult],
    all_responses: List[AgentResponse],
    working_directory: str = ".",
    dry_run: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Select a solution and apply changes.

    Args:
        evaluation_results: Ranked evaluation results
        all_responses: All agent responses
        working_directory: Directory for changes
        dry_run: If True, don't actually apply changes

    Returns:
        Result dictionary with applied changes, or None if cancelled
    """
    selector = InteractiveSelector(working_directory)

    # Let user select
    selected = await selector.select_solution(evaluation_results, all_responses)

    if not selected or not selected.get("diffs"):
        return selected

    # Apply changes
    if not dry_run:
        results = selector.diff_generator.apply_changes(selected["diffs"])

        # Show results
        if results["success"]:
            console = Console()
            console.print(f"\n✅ Successfully applied {len(results['success'])} file(s)")
            for file in results["success"]:
                console.print(f"   • {file}")

        if results["failed"]:
            console = Console()
            console.print(f"\n❌ Failed to apply {len(results['failed'])} file(s)")
            for item in results["failed"]:
                console.print(f"   • {item['file']}: {item['error']}")

        selected["apply_results"] = results

    return selected
