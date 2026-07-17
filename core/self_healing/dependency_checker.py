from __future__ import annotations

import ast
from pathlib import Path
from typing import List

from core.self_healing.models import SelfHealingIssue


class DependencyChecker:
    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root or "/root/KITTY_HIVE").resolve()

    def check(self) -> List[SelfHealingIssue]:
        issues: List[SelfHealingIssue] = []
        for py_file in sorted(self.repo_root.rglob("*.py")):
            if not py_file.is_file():
                continue
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"), filename=str(py_file))
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    issues.append(
                        SelfHealingIssue(
                            category="dependency",
                            title="Import dependency discovered",
                            description="The repository contains import-based dependencies that should be tracked.",
                            severity="low",
                            confidence=0.7,
                            affected_files=[py_file.relative_to(self.repo_root).as_posix()],
                            suggested_repair="Document or isolate the dependency to maintain clarity.",
                            estimated_impact="low",
                            estimated_difficulty="easy",
                        )
                    )
                    break
        return issues
