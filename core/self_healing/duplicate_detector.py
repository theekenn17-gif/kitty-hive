from __future__ import annotations

import re
from pathlib import Path
from typing import List

from core.self_healing.models import SelfHealingIssue


class DuplicateDetector:
    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root or "/root/KITTY_HIVE").resolve()

    def detect(self) -> List[SelfHealingIssue]:
        issues: List[SelfHealingIssue] = []
        grouped = {}
        for py_file in sorted(self.repo_root.rglob("*.py")):
            if not py_file.is_file():
                continue
            text = py_file.read_text(encoding="utf-8", errors="ignore")
            normalized = re.sub(r"\s+", "", text)
            grouped.setdefault(normalized, []).append(py_file)
        for paths in grouped.values():
            if len(paths) > 1:
                issues.append(
                    SelfHealingIssue(
                        category="duplicate",
                        title="Possible duplicate code detected",
                        description="Two or more files share identical or near-identical content.",
                        severity="low",
                        confidence=0.66,
                        affected_files=[p.relative_to(self.repo_root).as_posix() for p in paths],
                        suggested_repair="Consolidate repeated logic into a common helper.",
                        estimated_impact="medium",
                        estimated_difficulty="medium",
                    )
                )
        return issues
