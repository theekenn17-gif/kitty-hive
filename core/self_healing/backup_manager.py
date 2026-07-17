from __future__ import annotations

from pathlib import Path
from typing import Optional


class BackupManager:
    """Design-only backup interface for future repair workflows."""

    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root or "/root/KITTY_HIVE").resolve()

    def backup_before_repair(self, target_files: list[str]) -> Optional[Path]:
        return None

    def rollback_after_failed_repair(self, backup_path: Optional[Path]) -> bool:
        return False
