from __future__ import annotations

import ast
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.context_manager import build_repository_index
from core.self_healing.models import RepositoryHealth, SelfHealingIssue, SelfHealingReport


class SelfHealingScanner:
    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root or "/root/KITTY_HIVE").resolve()
        self.docs_dir = self.repo_root / "docs" / "self_healing"
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.history_store_path = self.repo_root / "memory" / "database" / "self_healing_history.json"
        self.history_store_path.parent.mkdir(parents=True, exist_ok=True)
        self.chroma_collection_name = "self_healing_history"

    def scan_repository(self) -> SelfHealingReport:
        self._ensure_repository_index()
        issues = []
        issues.extend(self._scan_imports())
        issues.extend(self._scan_security())
        issues.extend(self._scan_duplicates())
        issues.extend(self._scan_structure())
        issues.extend(self._scan_perf_and_quality())
        health = self._score_health(issues)
        return SelfHealingReport(
            repo_root=self.repo_root,
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            health=health,
            issues=issues,
        )

    def generate_report(self, report: SelfHealingReport) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        path = self.docs_dir / f"SELF_HEAL_REPORT_{timestamp}.md"
        path.write_text(report.to_markdown(), encoding="utf-8")
        return path

    def monitor_repository(self, report: SelfHealingReport, previous_report: Optional[SelfHealingReport] = None) -> Dict[str, Any]:
        subsystem_scores = self._collect_subsystem_scores(report.health)
        history = self._build_history(report, previous_report)
        regressions = self._detect_regressions(report, previous_report)
        chroma_status = self._store_monitoring_snapshot(report, subsystem_scores, history, regressions)
        return {
            "subsystem_scores": subsystem_scores,
            "history": history,
            "regressions": regressions,
            "chroma_status": chroma_status,
        }

    def _ensure_repository_index(self) -> None:
        build_repository_index(repo_root=self.repo_root, output_path=self.repo_root / "memory" / "context" / "repository_index.json")

    def _scan_imports(self) -> List[SelfHealingIssue]:
        issues: List[SelfHealingIssue] = []
        for py_file in sorted(self.repo_root.rglob("*.py")):
            if not py_file.is_file() or self._is_excluded(py_file):
                continue
            try:
                source = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(source, filename=str(py_file))
            except Exception:
                continue
            missing_modules = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if not self._module_exists(alias.name):
                            missing_modules.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module and not self._module_exists(node.module):
                        missing_modules.append(node.module)
            if missing_modules:
                issues.append(
                    SelfHealingIssue(
                        category="import",
                        title="Broken or unresolved imports detected",
                        description="The repository contains imports that do not resolve to available Python modules.",
                        severity="medium",
                        confidence=0.76,
                        affected_files=[py_file.relative_to(self.repo_root).as_posix()],
                        suggested_repair="Review import paths and ensure the referenced module exists within the repository or installed environment.",
                        estimated_impact="medium",
                        estimated_difficulty="medium",
                    )
                )
        return issues

    def _scan_security(self) -> List[SelfHealingIssue]:
        issues: List[SelfHealingIssue] = []
        for py_file in sorted(self.repo_root.rglob("*.py")):
            if not py_file.is_file() or self._is_excluded(py_file):
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
                        description="The code uses subprocess calls with shell=True, which increases injection risk.",
                        severity="high",
                        confidence=0.88,
                        affected_files=[py_file.relative_to(self.repo_root).as_posix()],
                        suggested_repair="Replace shell=True subprocess calls with argument-based execution or explicit command arrays.",
                        estimated_impact="high",
                        estimated_difficulty="medium",
                    )
                )
            if "eval(" in source or "exec(" in source:
                issues.append(
                    SelfHealingIssue(
                        category="security",
                        title="Dynamic execution detected",
                        description="The code uses eval/exec, which can introduce code injection risks.",
                        severity="high",
                        confidence=0.82,
                        affected_files=[py_file.relative_to(self.repo_root).as_posix()],
                        suggested_repair="Avoid eval/exec for user-controlled input and prefer explicit logic paths.",
                        estimated_impact="high",
                        estimated_difficulty="hard",
                    )
                )
        return issues

    def _scan_duplicates(self) -> List[SelfHealingIssue]:
        issues: List[SelfHealingIssue] = []
        function_name_map = {}
        for py_file in sorted(self.repo_root.rglob("*.py")):
            if not py_file.is_file() or self._is_excluded(py_file):
                continue
            try:
                source = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(source, filename=str(py_file))
            except Exception:
                continue
            function_names = [node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
            for name in function_names:
                function_name_map.setdefault(name, []).append(py_file)

        for function_name, paths in function_name_map.items():
            if len(paths) > 1:
                issues.append(
                    SelfHealingIssue(
                        category="duplicate",
                        title="Possible duplicate code detected",
                        description=f"Multiple files define the same top-level function name '{function_name}'.",
                        severity="low",
                        confidence=0.68,
                        affected_files=[p.relative_to(self.repo_root).as_posix() for p in paths],
                        suggested_repair="Factor shared content into a reusable helper or module to reduce duplication.",
                        estimated_impact="medium",
                        estimated_difficulty="medium",
                    )
                )
        return issues

    def _scan_structure(self) -> List[SelfHealingIssue]:
        issues: List[SelfHealingIssue] = []
        for path in sorted(self.repo_root.rglob("*")):
            if not path.exists():
                continue
            if path.is_dir() and not any(path.iterdir()):
                issues.append(
                    SelfHealingIssue(
                        category="structure",
                        title="Empty directory detected",
                        description="The repository contains an empty directory that may be an orphaned artifact.",
                        severity="low",
                        confidence=0.7,
                        affected_files=[path.relative_to(self.repo_root).as_posix()],
                        suggested_repair="Remove the empty directory or document its purpose.",
                        estimated_impact="low",
                        estimated_difficulty="easy",
                    )
                )
        return issues

    def _scan_perf_and_quality(self) -> List[SelfHealingIssue]:
        issues: List[SelfHealingIssue] = []
        for py_file in sorted(self.repo_root.rglob("*.py")):
            if not py_file.is_file() or self._is_excluded(py_file):
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
                        description="The file is unusually large and may be difficult to maintain.",
                        severity="medium",
                        confidence=0.74,
                        affected_files=[py_file.relative_to(self.repo_root).as_posix()],
                        suggested_repair="Split the file into smaller modules or responsibilities.",
                        estimated_impact="medium",
                        estimated_difficulty="medium",
                    )
                )
            if "TODO" in source or "FIXME" in source:
                issues.append(
                    SelfHealingIssue(
                        category="maintainability",
                        title="TODO/FIXME marker detected",
                        description="The repository contains unresolved TODO or FIXME comments.",
                        severity="low",
                        confidence=0.72,
                        affected_files=[py_file.relative_to(self.repo_root).as_posix()],
                        suggested_repair="Resolve or document the pending work to reduce maintenance uncertainty.",
                        estimated_impact="low",
                        estimated_difficulty="easy",
                    )
                )
        return issues

    def _score_health(self, issues: List[SelfHealingIssue]) -> RepositoryHealth:
        penalty = 0
        for issue in issues:
            severity_penalty = {"low": 4, "medium": 8, "high": 12}.get(issue.severity, 6)
            penalty += severity_penalty
        score = max(0, min(100, 100 - penalty))
        return RepositoryHealth(
            overall_score=score,
            architecture=max(0, min(100, score - 3)),
            security=max(0, min(100, score - 8)),
            performance=max(0, min(100, score - 6)),
            maintainability=max(0, min(100, score - 4)),
            dependencies=max(0, min(100, score - 5)),
            documentation=max(0, min(100, score - 2)),
            testing=max(0, min(100, score - 1)),
            memory_health=max(0, min(100, score - 2)),
        )

    def _collect_subsystem_scores(self, health: RepositoryHealth) -> Dict[str, int]:
        return {
            "overall": health.overall_score,
            "architecture": health.architecture,
            "security": health.security,
            "performance": health.performance,
            "maintainability": health.maintainability,
            "dependencies": health.dependencies,
            "documentation": health.documentation,
            "testing": health.testing,
            "memory_health": health.memory_health,
        }

    def _build_history(self, report: SelfHealingReport, previous_report: Optional[SelfHealingReport]) -> Dict[str, Any]:
        previous_score = None
        previous_generated_at = None
        if previous_report is not None:
            previous_score = previous_report.health.overall_score
            previous_generated_at = previous_report.generated_at
        else:
            previous_snapshot = self._load_previous_snapshot()
            if previous_snapshot is not None:
                previous_score = previous_snapshot.get("history", {}).get("current_score")
                previous_generated_at = previous_snapshot.get("history", {}).get("current_generated_at")

        current_score = report.health.overall_score
        delta = current_score - previous_score if previous_score is not None else 0
        return {
            "previous_score": previous_score,
            "current_score": current_score,
            "score_delta": delta,
            "previous_generated_at": previous_generated_at,
            "current_generated_at": report.generated_at,
        }

    def _detect_regressions(self, report: SelfHealingReport, previous_report: Optional[SelfHealingReport]) -> List[Dict[str, Any]]:
        if previous_report is None:
            previous_snapshot = self._load_previous_snapshot()
            if previous_snapshot is None:
                return []
            previous_health = previous_snapshot.get("health")
            if not previous_health:
                return []
            previous_report = SelfHealingReport(
                repo_root=Path(previous_snapshot.get("repo_root", self.repo_root)),
                generated_at=previous_snapshot.get("generated_at", "unknown"),
                health=RepositoryHealth(**previous_health),
                issues=[],
            )

        regressions: List[Dict[str, Any]] = []
        previous_health = previous_report.health
        current_health = report.health
        subsystem_names = [
            "overall",
            "architecture",
            "security",
            "performance",
            "maintainability",
            "dependencies",
            "documentation",
            "testing",
            "memory_health",
        ]
        for subsystem in subsystem_names:
            previous_value = getattr(previous_health, subsystem) if subsystem != "overall" else previous_health.overall_score
            current_value = getattr(current_health, subsystem) if subsystem != "overall" else current_health.overall_score
            delta = current_value - previous_value
            if delta < -3:
                regressions.append(
                    {
                        "subsystem": subsystem,
                        "previous_value": previous_value,
                        "current_value": current_value,
                        "delta": delta,
                        "message": f"{subsystem} regressed by {delta} points.",
                    }
                )
        if not regressions and (current_health.overall_score - previous_health.overall_score) < 0:
            regressions.append(
                {
                    "subsystem": "overall",
                    "previous_value": previous_health.overall_score,
                    "current_value": current_health.overall_score,
                    "delta": current_health.overall_score - previous_health.overall_score,
                    "message": "Overall health score declined.",
                }
            )
        return regressions

    def _store_monitoring_snapshot(
        self,
        report: SelfHealingReport,
        subsystem_scores: Dict[str, int],
        history: Dict[str, Any],
        regressions: List[Dict[str, Any]],
    ) -> str:
        payload = {
            "repo_root": str(report.repo_root),
            "generated_at": report.generated_at,
            "health": {
                "overall_score": report.health.overall_score,
                "architecture": report.health.architecture,
                "security": report.health.security,
                "performance": report.health.performance,
                "maintainability": report.health.maintainability,
                "dependencies": report.health.dependencies,
                "documentation": report.health.documentation,
                "testing": report.health.testing,
                "memory_health": report.health.memory_health,
            },
            "subsystem_scores": subsystem_scores,
            "history": history,
            "regressions": regressions,
        }
        try:
            import chromadb

            client = chromadb.PersistentClient(path=str(self.repo_root / "memory" / "database"))
            collection = client.get_or_create_collection(name=self.chroma_collection_name)
            collection.add(
                ids=[f"{report.repo_root.name}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"],
                documents=[json.dumps(payload, sort_keys=True)],
                metadatas=[{"source": str(report.repo_root), "generated_at": report.generated_at}],
            )
            return "stored_in_chromadb"
        except Exception:
            self.history_store_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
            return "stored_locally"

    def _load_previous_snapshot(self) -> Optional[Dict[str, Any]]:
        if self.history_store_path.exists():
            try:
                return json.loads(self.history_store_path.read_text(encoding="utf-8"))
            except Exception:
                return None
        return None

    def _module_exists(self, module_name: str) -> bool:
        if not module_name:
            return True
        root_name = module_name.split(".")[0]
        if root_name in {"os", "sys", "json", "ast", "re", "pathlib", "subprocess", "tempfile", "datetime", "typing"}:
            return True
        if (self.repo_root / root_name).exists() or (self.repo_root / f"{root_name}.py").exists():
            return True
        return False

    def _is_excluded(self, path: Path) -> bool:
        try:
            rel = path.relative_to(self.repo_root)
        except ValueError:
            return True
        parts = rel.parts
        excluded = {".git", "__pycache__", ".pytest_cache", "kitty_env", "chroma", "memory", "logs", "backups", "docs"}
        if any(part in excluded for part in parts):
            return True
        return False
