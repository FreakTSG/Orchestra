"""Backup and rollback system for file changes."""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import json


class BackupManager:
    """Manage backups and rollbacks of file changes."""

    def __init__(self, working_directory: str = ".", backup_dir: Optional[str] = None):
        """
        Initialize backup manager.

        Args:
            working_directory: Directory to backup
            backup_dir: Directory to store backups (default: .multi-agent-coder-backups)
        """
        self.working_dir = Path(working_directory).resolve()

        if backup_dir is None:
            backup_dir = self.working_dir / ".multi-agent-coder-backups"

        self.backup_dir = Path(backup_dir).resolve()
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, file_paths: List[str]) -> str:
        """
        Create a backup of specified files.

        Args:
            file_paths: List of file paths to backup

        Returns:
            Path to the backup directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)

        manifest = {
            "timestamp": timestamp,
            "backup_path": str(backup_path),
            "files": []
        }

        for file_path in file_paths:
            full_path = self.working_dir / file_path

            if not full_path.exists():
                continue

            try:
                # Create subdirectory structure in backup
                backup_file_path = backup_path / file_path
                backup_file_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                shutil.copy2(full_path, backup_file_path)

                manifest["files"].append({
                    "original_path": file_path,
                    "backup_path": str(backup_file_path.relative_to(backup_path)),
                    "size": full_path.stat().st_size
                })

            except Exception as e:
                print(f"Warning: Failed to backup {file_path}: {e}")

        # Save manifest
        manifest_path = backup_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))

        return str(backup_path)

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups."""
        backups = []

        for item in self.backup_dir.iterdir():
            if not item.is_dir():
                continue

            manifest_path = item / "manifest.json"
            if not manifest_path.exists():
                continue

            try:
                manifest = json.loads(manifest_path.read_text())
                backups.append({
                    "name": item.name,
                    "timestamp": manifest.get("timestamp"),
                    "file_count": len(manifest.get("files", [])),
                    "path": str(item)
                })
            except Exception:
                pass

        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x["timestamp"], reverse=True)
        return backups

    def restore_backup(self, backup_name: str, file_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Restore files from a backup.

        Args:
            backup_name: Name of the backup to restore
            file_paths: Specific files to restore (None = all)

        Returns:
            Summary of restore operation
        """
        backup_path = self.backup_dir / backup_name

        if not backup_path.exists():
            raise ValueError(f"Backup '{backup_name}' not found")

        manifest_path = backup_path / "manifest.json"
        if not manifest_path.exists():
            raise ValueError(f"Backup manifest not found")

        manifest = json.loads(manifest_path.read_text())

        results = {
            "restored": [],
            "failed": []
        }

        for file_info in manifest.get("files", []):
            original_path = file_info["original_path"]

            # Skip if file_paths specified and this file not in list
            if file_paths and original_path not in file_paths:
                continue

            backup_file_path = backup_path / file_info["backup_path"]
            target_file_path = self.working_dir / original_path

            try:
                # Ensure parent directory exists
                target_file_path.parent.mkdir(parents=True, exist_ok=True)

                # Restore file
                shutil.copy2(backup_file_path, target_file_path)
                results["restored"].append(original_path)

            except Exception as e:
                results["failed"].append({
                    "file": original_path,
                    "error": str(e)
                })

        return results

    def cleanup_old_backups(self, keep_count: int = 10):
        """
        Remove old backups, keeping only the most recent N.

        Args:
            keep_count: Number of backups to keep
        """
        backups = self.list_backups()

        for backup in backups[keep_count:]:
            backup_path = Path(backup["path"])
            try:
                shutil.rmtree(backup_path)
            except Exception:
                pass

    def get_latest_backup(self) -> Optional[str]:
        """Get the name of the most recent backup."""
        backups = self.list_backups()
        return backups[0]["name"] if backups else None

    def format_backup_list(self) -> str:
        """Format backups list for display."""
        backups = self.list_backups()

        if not backups:
            return "No backups found"

        lines = ["\n💾 Available Backups"]
        lines.append("=" * 60)

        for i, backup in enumerate(backups[:10], 1):
            lines.append(f"\n{i}. {backup['name']}")
            lines.append(f"   Time: {backup['timestamp']}")
            lines.append(f"   Files: {backup['file_count']}")

        if len(backups) > 10:
            lines.append(f"\n... and {len(backups) - 10} more backups")

        return "\n".join(lines)
