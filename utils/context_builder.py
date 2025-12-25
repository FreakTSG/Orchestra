"""Build codebase context for AI agents."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import fnmatch


class CodebaseContext:
    """Represents the context of a codebase."""

    def __init__(self, root_path: str, max_files: int = 50):
        """
        Initialize codebase context.

        Args:
            root_path: Root directory of the project
            max_files: Maximum number of files to include in context
        """
        self.root_path = Path(root_path).resolve()
        self.max_files = max_files
        self.file_tree = self._build_file_tree()
        self.project_type = self._detect_project_type()
        self.important_files = self._find_important_files()
        self.context_text = self._build_context()

    def _build_file_tree(self) -> Dict[str, Any]:
        """Build a tree structure of the codebase."""
        tree = {"name": self.root_path.name, "path": str(self.root_path), "children": []}

        try:
            for item in sorted(self.root_path.iterdir()):
                # Skip hidden files and common exclusions
                if item.name.startswith('.'):
                    continue
                if item.name in ['node_modules', '__pycache__', 'venv', '.git', 'dist', 'build']:
                    continue

                if item.is_dir():
                    subtree = self._scan_directory(item, max_depth=2)
                    if subtree:
                        tree["children"].append(subtree)
                elif item.is_file():
                    tree["children"].append({
                        "name": item.name,
                        "path": str(item),
                        "size": item.stat().st_size
                    })
        except PermissionError:
            pass

        return tree

    def _scan_directory(self, dir_path: Path, max_depth: int = 2, current_depth: int = 0) -> Optional[Dict]:
        """Recursively scan directory."""
        if current_depth >= max_depth:
            return None

        try:
            children = []
            for item in sorted(dir_path.iterdir()):
                if item.name.startswith('.') or item.name in ['node_modules', '__pycache__', 'venv']:
                    continue

                if item.is_dir():
                    subtree = self._scan_directory(item, max_depth, current_depth + 1)
                    if subtree:
                        children.append(subtree)
                elif item.is_file():
                    children.append({
                        "name": item.name,
                        "path": str(item),
                        "size": item.stat().st_size
                    })

            return {
                "name": dir_path.name,
                "path": str(dir_path),
                "children": children
            } if children else None

        except PermissionError:
            return None

    def _detect_project_type(self) -> str:
        """Detect the type of project."""
        indicators = {
            "Python": ["requirements.txt", "setup.py", "pyproject.toml", "*.py"],
            "JavaScript/Node": ["package.json", "node_modules", "*.js", "*.ts"],
            "Java": ["pom.xml", "build.gradle", "*.java"],
            "Go": ["go.mod", "*.go"],
            "Rust": ["Cargo.toml", "*.rs"],
            "Ruby": ["Gemfile", "*.rb"],
        }

        for lang, patterns in indicators.items():
            for pattern in patterns:
                if pattern.startswith('*'):
                    # Check for file extension
                    if any(f.suffix == pattern[1:] for f in self.root_path.glob(pattern)):
                        return lang
                else:
                    # Check for specific file
                    if (self.root_path / pattern).exists():
                        return lang

        return "Unknown"

    def _find_important_files(self) -> List[Dict[str, Any]]:
        """Find important files to include in context."""
        important_patterns = [
            "README*",
            "package.json",
            "requirements.txt",
            "setup.py",
            "pyproject.toml",
            "Cargo.toml",
            "go.mod",
            "*.config.js",
            "*.config.ts",
            ".env*",
            "Dockerfile",
            "docker-compose.yml",
        ]

        files = []
        for pattern in important_patterns:
            matches = list(self.root_path.glob(pattern))
            for match in matches:
                if match.is_file() and len(files) < self.max_files:
                    try:
                        content = match.read_text(encoding='utf-8', errors='ignore')
                        files.append({
                            "path": str(match.relative_to(self.root_path)),
                            "name": match.name,
                            "content": content[:5000]  # Limit content size
                        })
                    except Exception:
                        pass

        return files

    def _build_context(self) -> str:
        """Build the context text to send to agents."""
        parts = []

        # Project overview
        parts.append(f"## Project Context")
        parts.append(f"**Project Root**: {self.root_path}")
        parts.append(f"**Project Type**: {self.project_type}")
        parts.append("")

        # Directory structure
        parts.append(f"## Directory Structure")
        parts.append("```")
        parts.append(self._format_tree(self.file_tree))
        parts.append("```")
        parts.append("")

        # Important files
        if self.important_files:
            parts.append(f"## Important Configuration Files")
            for file_info in self.important_files[:10]:  # Limit to 10 files
                parts.append(f"\n### {file_info['path']}")
                parts.append(f"```")
                parts.append(file_info['content'][:1000])  # First 1000 chars
                if len(file_info['content']) > 1000:
                    parts.append(f"\n... ({len(file_info['content'])} total characters)")
                parts.append("```")
                parts.append("")

        return "\n".join(parts)

    def _format_tree(self, tree: Dict[str, Any], indent: int = 0) -> str:
        """Format file tree as text."""
        result = []
        prefix = "  " * indent

        if "children" not in tree:
            return f"{prefix}📄 {tree['name']}"

        result.append(f"{prefix}📁 {tree['name']}/")

        for child in tree.get("children", [])[:20]:  # Limit children
            if "children" in child:
                result.append(self._format_tree(child, indent + 1))
            else:
                result.append(f"{prefix}  📄 {child['name']}")

        return "\n".join(result)

    def get_context(self) -> str:
        """Get the full context text."""
        return self.context_text

    def find_files(self, pattern: str) -> List[str]:
        """Find files matching a pattern."""
        matches = []
        for file_path in self.root_path.rglob(pattern):
            if file_path.is_file():
                matches.append(str(file_path.relative_to(self.root_path)))
        return matches[:self.max_files]

    def read_file(self, file_path: str) -> Optional[str]:
        """Read a file from the codebase."""
        full_path = self.root_path / file_path
        try:
            return full_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return None

    def search_code(self, query: str) -> List[Dict[str, Any]]:
        """Search for code matching a pattern."""
        import re
        results = []

        try:
            for file_path in self.root_path.rglob("*"):
                if not file_path.is_file():
                    continue

                # Skip binary files
                if file_path.suffix in ['.pyc', '.so', '.dll', '.exe']:
                    continue

                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    matches = list(re.finditer(re.escape(query), content, re.IGNORECASE))

                    if matches:
                        results.append({
                            "path": str(file_path.relative_to(self.root_path)),
                            "matches": len(matches),
                            "preview": content[:500]
                        })

                        if len(results) >= 20:  # Limit results
                            break

                except Exception:
                    pass

        except Exception:
            pass

        return results


def get_codebase_context(path: Optional[str] = None, max_files: int = 50) -> Optional[CodebaseContext]:
    """
    Get codebase context for a directory.

    Args:
        path: Directory path (defaults to current working directory)
        max_files: Maximum number of files to include

    Returns:
        CodebaseContext object or None if invalid path
    """
    if path is None:
        path = os.getcwd()

    if not os.path.isdir(path):
        return None

    return CodebaseContext(path, max_files)
