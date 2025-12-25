"""Utility modules for Multi-Agent Coder."""

from .context_builder import CodebaseContext, get_codebase_context
from .code_parser import CodeParser, FileOperation, OperationType, parse_agent_response
from .diff_generator import DiffGenerator, FileDiff
from .interactive_selector import InteractiveSelector, select_and_apply
from .backup_manager import BackupManager

__all__ = [
    "CodebaseContext",
    "get_codebase_context",
    "CodeParser",
    "FileOperation",
    "OperationType",
    "parse_agent_response",
    "DiffGenerator",
    "FileDiff",
    "InteractiveSelector",
    "select_and_apply",
    "BackupManager",
]
