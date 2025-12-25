"""Interactive REPL for Multi-Agent Coder."""

import asyncio
import os
import sys
from typing import Optional, Dict, Any
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

# Import from the parent directory structure
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_agent_coder.cli_orchestrator import MultiAgentCLICoder
from utils.context_builder import get_codebase_context
from utils.interactive_selector import select_and_apply
from utils.backup_manager import BackupManager
from utils.code_parser import CodeParser


class OrchestraREPL:
    """Interactive REPL for Multi-Agent Coder."""

    def __init__(self):
        """Initialize the REPL."""
        self.console = Console()
        self.working_dir = os.getcwd()
        self.orchestrator = None
        self.context = None
        self.history = []
        self.running = False

        # Startup banner
        self.show_banner()

    async def start(self):
        """Start the REPL loop."""
        self.running = True

        # Initialize orchestrator
        self.console.print("\n[bold cyan] Initializing Orchestra...[/bold cyan]")
        self.orchestrator = MultiAgentCLICoder(auto_detect=True)

        # Gather context
        self.gather_context()

        # Show ready message
        self.console.print(f"\n Ready! Working in: [cyan]{self.working_dir}[/cyan]")
        self.console.print("Type [bold yellow]help[/bold yellow] for commands or [bold yellow]exit[/bold yellow] to quit\n")

        # Main loop
        while self.running:
            try:
                # Get user input
                prompt = self.get_prompt()

                if not prompt:
                    continue

                # Execute command
                await self.execute(prompt)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"\n[red]Error: {str(e)}[/red]")

    def get_prompt(self) -> str:
        """Get user input."""
        return Prompt.ask(
            "\n[bold cyan]orchestra[/bold cyan]",
            default="",
            show_default=False
        )

    async def execute(self, input_text: str):
        """Execute a user command."""
        input_text = input_text.strip()
        self.history.append(input_text)

        # Handle commands
        if input_text.lower() in ['exit', 'quit', 'q']:
            await self.cmd_exit()

        elif input_text.lower() == 'help':
            self.cmd_help()

        elif input_text.lower() in ['clear', 'cls']:
            self.cmd_clear()

        elif input_text.lower() == 'agents':
            self.cmd_agents()

        elif input_text.lower() == 'pwd':
            self.cmd_pwd()

        elif input_text.lower().startswith('cd '):
            self.cmd_cd(input_text[3:])

        elif input_text.lower() == 'history':
            self.cmd_history()

        elif input_text.lower() == 'context':
            self.cmd_context()

        elif input_text.lower().startswith('set '):
            await self.cmd_set(input_text[4:])

        elif input_text.lower() == 'backup':
            await self.cmd_backup()

        elif input_text.lower().startswith('restore '):
            await self.cmd_restore(input_text[8:])

        else:
            # Treat as a coding query
            await self.cmd_query(input_text)

    def show_banner(self):
        """Show startup banner."""
        banner = """
========================================================================

     ORCHESTRA - Multi-Agent Coding Environment

     Your AI coding team at your fingertips

========================================================================
        """
        self.console.print(f"[bold cyan]{banner}[/bold cyan]")

    def gather_context(self):
        """Gather codebase context."""
        self.console.print("[dim] Gathering codebase context...[/dim]")

        codebase = get_codebase_context(self.working_dir, max_files=10)
        if codebase:
            self.context = {"codebase": codebase.get_context()}
            self.console.print(f"[dim]   Project: {codebase.project_type}[/dim]")
            self.console.print(f"[dim]   Files: {len(codebase.important_files)} scanned[/dim]")
        else:
            self.console.print("[yellow]  Could not gather context[/yellow]")

    # Commands
    def cmd_help(self):
        """Show help message."""
        help_text = """
[bold cyan]Orchestra Commands[/bold cyan]

[bold yellow]Coding Queries:[/bold yellow]
  <query>                 Ask agents to implement/fix/refactor code
  <query> !review         Get code review without file changes
  <query> !explain        Just explain, don't make changes

[bold yellow]Working Directory:[/bold yellow]
  pwd                     Show current working directory
  cd <path>               Change working directory
  context                 Show current codebase context

[bold yellow]Agents:[/bold yellow]
  agents                  List available AI CLI agents
  set agents <list>       Specify which agents to use
                           Example: set agents claude,gemini

[bold yellow]Options:[/bold yellow]
  set limit <n>           Set context file limit (default: 10)
  set nocontext           Disable codebase context
  set context             Enable codebase context

[bold yellow]Backups:[/bold yellow]
  backup                  Create manual backup
  restore <backup>        Restore a backup
  backups                 List all backups

[bold yellow]Utility:[/bold yellow]
  clear / cls             Clear screen
  history                 Show command history
  help                    Show this help message
  exit / quit / q         Exit Orchestra

[bold yellow]Examples:[/bold yellow]
  Add error handling
  Fix the bug in auth.py
  Refactor the database layer
  Implement binary search !explain
  cd ./backend && Optimize queries
"""
        self.console.print(help_text)

    def cmd_clear(self):
        """Clear screen."""
        import subprocess
        subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)

    def cmd_agents(self):
        """List available agents."""
        agents = self.orchestrator.get_available_agents()

        table = Table(title="🤖 Available AI Agents")
        table.add_column("Agent", style="green")
        table.add_column("Status", style="yellow")

        for agent in agents:
            table.add_row(agent, " Active")

        self.console.print(table)

    def cmd_pwd(self):
        """Show working directory."""
        self.console.print(f"\n {self.working_dir}")

    def cmd_cd(self, path: str):
        """Change working directory."""
        new_dir = os.path.abspath(path)

        if not os.path.isdir(new_dir):
            self.console.print(f"[red] Directory not found: {path}[/red]")
            return

        self.working_dir = new_dir
        self.console.print(f"[dim]Changed to: {self.working_dir}[/dim]")
        self.gather_context()  # Regather context

    def cmd_context(self):
        """Show current context."""
        if self.context:
            self.console.print(Panel(self.context['codebase'][:1000], title=" Codebase Context (truncated)"))
            self.console.print(f"\n[dim]Total context: {len(self.context['codebase'])} chars[/dim]")
        else:
            self.console.print("[yellow]No context gathered[/yellow]")

    def cmd_history(self):
        """Show command history."""
        if not self.history:
            self.console.print("\nNo commands yet")
            return

        self.console.print("\n[bold]Command History:[/bold]")
        for i, cmd in enumerate(self.history[-20:], 1):
            self.console.print(f"  {i}. {cmd}")

    async def cmd_query(self, prompt: str):
        """Execute a coding query."""
        # Check for flags
        review_only = "!review" in prompt
        explain_only = "!explain" in prompt

        # Clean prompt
        clean_prompt = prompt.replace("!review", "").replace("!explain", "").strip()

        if not clean_prompt:
            self.console.print("[yellow]  Please provide a query[/yellow]")
            return

        # Show what we're doing
        mode = "REVIEW" if review_only else "EXPLAIN" if explain_only else "IMPLEMENT"
        self.console.print(f"\n[bold cyan] Mode: {mode}[/bold cyan]")
        self.console.print(f"[bold cyan] Query:[/bold cyan] {clean_prompt}")

        # Build full prompt with context
        if self.context:
            full_prompt = f"{self.context['codebase']}\n\nTask: {clean_prompt}"
        else:
            full_prompt = clean_prompt

        # Run query
        self.console.print(f"\n[bold yellow] Dispatching to {len(self.orchestrator.get_available_agents())} agent(s)...[/bold yellow]")

        result = await self.orchestrator.query(full_prompt, skip_enhancement=True)

        # Show results
        self.display_results(result, review_only or explain_only)

        # If not review/explain mode, ask if user wants to apply
        if not review_only and not explain_only:
            await self.offer_solution_selection(result)

    def display_results(self, result, preview_only: bool = False):
        """Display query results."""
        # Show ranked solutions
        table = Table(title="\n Ranked Solutions")
        table.add_column("Rank", style="cyan", width=6)
        table.add_column("Agent", style="green", width=20)
        table.add_column("Score", style="yellow", width=10)
        table.add_column("Files", style="magenta", width=8)

        parser = CodeParser()

        for eval_result in result.evaluation_results:
            medal = "🥇" if eval_result.rank == 1 else "🥈" if eval_result.rank == 2 else "🥉"

            # Count files
            operations = parser.parse_response(eval_result.response.content)
            file_count = len(operations) if operations else 0

            table.add_row(
                f"{medal} #{eval_result.rank}",
                eval_result.response.agent_name,
                f"{eval_result.average_score:.1f}/100",
                f"{file_count} file(s)" if file_count > 0 else "N/A"
            )

        self.console.print(table)

        # Show best solution
        best = result.evaluation_results[0]
        self.console.print(f"\n[bold green] Best: {best.response.agent_name}[/bold green]")

        if best.response.explanation:
            self.console.print(Panel(best.response.explanation[:500], border_style="green"))

        if best.response.code and preview_only:
            self.console.print("\n[bold cyan] Code:[/bold cyan]")
            self.console.print(Panel(best.response.code[:500], border_style="cyan"))

    async def offer_solution_selection(self, result):
        """Offer to select and apply a solution."""
        from questionary import confirm

        choice = await confirm(
            "Would you like to preview and apply one of these solutions?",
            default=True
        ).ask_async()

        if not choice:
            self.console.print("[yellow]Skipped.[/yellow]")
            return

        # Create backup
        backup_mgr = BackupManager(self.working_dir)
        parser = CodeParser()

        # Collect all operations
        all_operations = []
        for response in result.all_responses:
            ops = parser.parse_response(response.content)
            all_operations.extend(ops)

        # Get unique files
        file_paths = list(set(op.file_path for op in all_operations if op.file_path))

        if file_paths:
            self.console.print(f"\n[bold yellow] Creating backup of {len(file_paths)} file(s)...[/bold yellow]")
            backup_path = backup_mgr.create_backup(file_paths)
            self.console.print(f"[green] Backup: {backup_path}[/green]")

        # Interactive selection
        selected = await select_and_apply(
            result.evaluation_results,
            result.all_responses,
            self.working_dir,
            dry_run=False
        )

        if selected:
            self.console.print(f"\n Applied solution from [cyan]{selected['agent_name']}[/cyan]!")
        else:
            self.console.print("[yellow]No changes applied.[/yellow]")

    async def cmd_set(self, options: str):
        """Set configuration options."""
        parts = options.split(maxsplit=1)

        if not parts or not parts[0]:
            self.console.print("[yellow]Usage: set <option> <value>[/yellow]")
            self.console.print("  set agents claude,gemini")
            self.console.print("  set limit 20")
            self.console.print("  set nocontext")
            self.console.print("  set context")
            return

        option = parts[0].lower()
        value = parts[1] if len(parts) > 1 else None

        if option == "agents":
            self.console.print(f"[dim]Agents set to: {value}[/dim]")
            # Would need to recreate orchestrator with specific agents
            # For now, just informational

        elif option == "limit":
            try:
                limit = int(value)
                self.console.print(f"[dim]Context file limit set to: {limit}[/dim]")
                self.gather_context()
            except ValueError:
                self.console.print("[red]Invalid limit (must be a number)[/red]")

        elif option == "nocontext":
            self.context = None
            self.console.print("[yellow]Context disabled[/yellow]")

        elif option == "context":
            self.gather_context()

        else:
            self.console.print(f"[red]Unknown option: {option}[/red]")

    async def cmd_backup(self):
        """Create a manual backup."""
        backup_mgr = BackupManager(self.working_dir)

        # Backup all Python files
        import glob
        py_files = list(glob.glob("**/*.py", recursive=True))[:50]

        if not py_files:
            self.console.print("[yellow]No Python files found to backup[/yellow]")
            return

        backup_path = backup_mgr.create_backup(py_files)
        self.console.print(f"[green] Backup created: {backup_path}[/green]")

    async def cmd_restore(self, backup_name: str):
        """Restore a backup."""
        backup_mgr = BackupManager(self.working_dir)

        backups = backup_mgr.list_backups()
        backup_names = [b['name'] for b in backups]

        if backup_name not in backup_names:
            self.console.print(f"[red] Backup '{backup_name}' not found[/red]")
            self.console.print("\nAvailable backups:")
            for b in backups:
                self.console.print(f"  • {b['name']}")
            return

        # Restore
        results = backup_mgr.restore_backup(backup_name)

        if results['restored']:
            self.console.print(f"\n[green] Restored {len(results['restored'])} file(s):[/green]")
            for f in results['restored']:
                self.console.print(f"  • {f}")

        if results['failed']:
            self.console.print(f"\n[red] Failed to restore {len(results['failed'])} file(s):[/red]")
            for item in results['failed']:
                self.console.print(f"  • {item['file']}: {item['error']}")

    async def cmd_exit(self):
        """Exit the REPL."""
        self.console.print("\n[bold yellow] Thank you for using Orchestra! See you next time! [/bold yellow]")
        self.running = False
