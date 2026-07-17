from __future__ import annotations

from pathlib import Path
from typing import List

from core.self_healing.models import SelfHealingIssue


class SecurityChecker:
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
            if "shell=True" in source:
                issues.append(
                    SelfHealingIssue(
                        category="security",
                        title="Shell execution with shell=True detected",
                        description="Subprocess execution uses shell=True, which increases injection risk.",
                        severity="high",
                        confidence=0.9,
                        affected_files=[py_file.relative_to(self.repo_root).as_posix()],
                        suggested_repair="Replace shell=True with a safer argument list approach.",
                        estimated_impact="high",
                        estimated_difficulty="medium",
                    )
                )
            if "eval(" in source or "exec(" in source:
                issues.append(
                    SelfHealingIssue(
                        category="security",
                        title="Dynamic execution detected",
                        description="The code uses eval/exec, which introduces code injection risk.",
                        severity="high",
                        confidence=0.85,
                        affected_files=[py_file.relative_to(self.repo_root).as_posix()],
                        suggested_repair="Avoid eval/exec for untrusted input and prefer explicit logic.",
                        estimated_impact="high",
                        estimated_difficulty="hard",
                    )
                )
        return issues
