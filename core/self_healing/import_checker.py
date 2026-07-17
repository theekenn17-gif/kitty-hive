from __future__ import annotations

import ast
from pathlib import Path
from typing import List

from core.self_healing.models import SelfHealingIssue


class ImportChecker:
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
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if not self._is_available(alias.name):
                            issues.append(
                                SelfHealingIssue(
                                    category="import",
                                    title="Unresolved import found",
                                    description="The parser detected an import that does not resolve to an available module.",
                                    severity="medium",
                                    confidence=0.75,
                                    affected_files=[py_file.relative_to(self.repo_root).as_posix()],
                                    suggested_repair="Confirm the import path and ensure the module exists in the environment or repository.",
                                    estimated_impact="medium",
                                    estimated_difficulty="medium",
                                )
                            )
                            break
        return issues

    def _is_available(self, module_name: str) -> bool:
        if not module_name:
            return True
        root_name = module_name.split(".")[0]
        builtins = {"os", "sys", "json", "ast", "re", "pathlib", "subprocess", "tempfile", "datetime", "typing"}
        if root_name in builtins:
            return True
        return (self.repo_root / root_name).exists() or (self.repo_root / f"{root_name}.py").exists()
