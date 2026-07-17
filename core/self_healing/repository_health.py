from __future__ import annotations

from pathlib import Path

from core.self_healing.models import RepositoryHealth


class RepositoryHealthTracker:
    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root or "/root/KITTY_HIVE").resolve()

    def summarize(self, overall_score: int) -> RepositoryHealth:
        return RepositoryHealth(
            overall_score=overall_score,
            architecture=max(0, min(100, overall_score - 3)),
            security=max(0, min(100, overall_score - 8)),
            performance=max(0, min(100, overall_score - 6)),
            maintainability=max(0, min(100, overall_score - 4)),
            dependencies=max(0, min(100, overall_score - 5)),
            documentation=max(0, min(100, overall_score - 2)),
            testing=max(0, min(100, overall_score - 1)),
            memory_health=max(0, min(100, overall_score - 2)),
        )
