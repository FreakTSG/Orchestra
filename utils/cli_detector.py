"""CLI tool detector - finds available AI CLI tools on the system."""

import subprocess
import asyncio
from typing import List, Dict, Tuple
from dataclasses import dataclass

from config.cli_settings import cli_settings


@dataclass
class CLITool:
    """Represents a detected CLI tool."""
    name: str
    command: str
    available: bool
    version: str = ""
    location: str = ""

    def __str__(self):
        status = "✓" if self.available else "✗"
        return f"{status} {self.name} ({self.command})"


class CLIDetector:
    """Detects and validates available AI CLI tools."""

    def __init__(self):
        self.settings = cli_settings
        self.detected_tools: Dict[str, CLITool] = {}

    async def detect_all(self) -> Dict[str, CLITool]:
        """Detect all available CLI tools."""
        configs = self.settings.get_all_cli_configs()

        detection_tasks = []
        for agent_name, config in configs.items():
            task = self._detect_tool(agent_name, config["command"], config.get("name", agent_name))
            detection_tasks.append(task)

        results = await asyncio.gather(*detection_tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, CLITool):
                self.detected_tools[result.name.lower()] = result

        return self.detected_tools

    async def _detect_tool(self, agent_key: str, command: str, display_name: str) -> CLITool:
        """Detect a single CLI tool."""
        # Try to get version
        version = await self._get_version(command)
        location = await self._get_location(command)

        available = version is not None or location is not None

        return CLITool(
            name=display_name,
            command=command,
            available=available,
            version=version or "",
            location=location or ""
        )

    async def _get_version(self, command: str) -> str:
        """Get version of CLI tool."""
        version_flags = ["--version", "-v", "version", "--v"]

        for flag in version_flags:
            try:
                process = await asyncio.create_subprocess_exec(
                    command,
                    flag,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=5
                )

                if process.returncode == 0:
                    output = stdout.decode('utf-8', errors='ignore').strip()
                    if output:
                        return output
                else:
                    # Some tools output version to stderr
                    output = stderr.decode('utf-8', errors='ignore').strip()
                    if output:
                        return output

            except (FileNotFoundError, asyncio.TimeoutError):
                continue
            except Exception:
                continue

        return None

    async def _get_location(self, command: str) -> str:
        """Get file system location of CLI command."""
        try:
            # Try 'which' on Unix-like systems
            process = await asyncio.create_subprocess_exec(
                "which",
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=5
            )

            if process.returncode == 0:
                return stdout.decode('utf-8').strip()

        except FileNotFoundError:
            # 'which' not available, try 'where' on Windows
            try:
                process = await asyncio.create_subprocess_exec(
                    "where",
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=5
                )

                if process.returncode == 0:
                    return stdout.decode('utf-8').strip()

            except Exception:
                pass

        except Exception:
            pass

        return None

    def get_available_tools(self) -> List[CLITool]:
        """Get list of available CLI tools."""
        return [tool for tool in self.detected_tools.values() if tool.available]

    def get_unavailable_tools(self) -> List[CLITool]:
        """Get list of unavailable CLI tools."""
        return [tool for tool in self.detected_tools.values() if not tool.available]

    def print_detection_report(self):
        """Print a formatted detection report."""
        print("\n" + "=" * 60)
        print("🔍 CLI Tool Detection Report")
        print("=" * 60)

        available = self.get_available_tools()
        unavailable = self.get_unavailable_tools()

        if available:
            print(f"\n✅ Available Tools ({len(available)}):")
            for tool in available:
                version_str = f" - {tool.version}" if tool.version else ""
                print(f"  ✓ {tool.name}{version_str}")
                if tool.location:
                    print(f"    Location: {tool.location}")

        if unavailable:
            print(f"\n❌ Unavailable Tools ({len(unavailable)}):")
            for tool in unavailable:
                print(f"  ✗ {tool.name} (command: {tool.command})")

        print("\n" + "=" * 60)

        if not available:
            print("\n⚠️  No CLI tools detected!")
            print("\nTo install CLI tools, consider:")
            print("  - Claude: npm install -g @anthropic-ai/claude-code")
            print("  - Gemini: pip install google-generativeai (or gemini-cli)")
            print("  - OpenAI: npm install -g openai-cli")
            print("  - Or add custom CLI tools in .env")
            print("\nExample .env:")
            print("  CUSTOM_CLI_MYTOOL=/path/to/my-tool")
        else:
            print(f"\n✨ Ready to use {len(available)} CLI tool(s)!")


async def main():
    """Test CLI detection."""
    detector = CLIDetector()
    await detector.detect_all()
    detector.print_detection_report()


if __name__ == "__main__":
    asyncio.run(main())
