"""Orchestra REPL - Main entry point."""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestra.repl import OrchestraREPL


def main():
    """Main entry point for orchestra command."""
    try:
        asyncio.run(_run_orchestra())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)


async def _run_orchestra():
    """Run the Orchestra REPL."""
    repl = OrchestraREPL()
    await repl.start()


if __name__ == "__main__":
    main()
