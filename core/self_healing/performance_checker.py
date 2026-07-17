from __future__ import annotations

from pathlib import Path
from typing import List

from core.self_healing.models import SelfHealingIssue


class PerformanceChecker:
    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root or "/root/KITTY_HIVE").resolve()

    def check(self) -> List[SelfHealingIssue]:
        issues: List[SelfHealingIssue] = []
        for py_file in sorted(self.repo_root.rglob("*.py")):
            if not py_file.is_file():
                continue
            try:
                source = py_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            line_count = len(source.splitlines())
            if line_count > 400:
                issues.append(
                    SelfHealingIssue(
                        category="performance",
                        title="Large file detected",
                        description="The file is large enough to be a performance and maintainability concern.",
                        severity="medium",
                        confidence=0.74,
                        affected_files=[py_file.relative_to(self.repo_root).as_posix()],
                        suggested_repair="Split the file into smaller modules or responsibilities.",
                        estimated_impact="medium",
                        estimated_difficulty="medium",
                    )
                )
        return issues
