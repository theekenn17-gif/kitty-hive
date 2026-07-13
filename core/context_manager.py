from __future__ import annotations

import ast
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


DEFAULT_OUTPUT_PATH = Path("memory/context/repository_index.json")
EXCLUDED_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "kitty_env",
    "memory-env",
    "__pycache__",
    ".pytest_cache",
    "logs",
    "backups",
    "database",
    "embeddings",
    "cache",
}
EXCLUDED_FILE_NAMES = {".env", ".env.local", ".env.production", ".env.example"}
EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".sqlite3",
    ".db",
    ".log",
    ".jpg",
    ".png",
    ".gif",
    ".mp4",
    ".zip",
    ".tar",
    ".gz",
    ".whl",
}


def _normalize_repo_root(repo_root: Optional[Path] = None) -> Path:
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]
    return Path(repo_root).resolve()


def _is_excluded(path: Path, repo_root: Path) -> bool:
    try:
        rel_path = path.relative_to(repo_root)
    except ValueError:
        return True

    parts = rel_path.parts
    if any(part in EXCLUDED_DIR_NAMES for part in parts):
        return True

    if any(part.startswith(".") and part != "." for part in parts):
        if rel_path.name in EXCLUDED_FILE_NAMES:
            return True

    if rel_path.name in EXCLUDED_FILE_NAMES:
        return True

    if rel_path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True

    if rel_path.as_posix().startswith("memory/context/"):
        return True

    return False


def _read_git_metadata(file_path: Path, repo_root: Path) -> Dict[str, Optional[str]]:
    try:
        timestamp = subprocess.check_output(
            ["git", "log", "-1", "--format=%ct", "--", str(file_path.relative_to(repo_root))],
            cwd=str(repo_root),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        subject = subprocess.check_output(
            ["git", "log", "-1", "--format=%s", "--", str(file_path.relative_to(repo_root))],
            cwd=str(repo_root),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return {"last_changed_unix": timestamp or None, "last_commit_subject": subject or None}
    except Exception:
        return {"last_changed_unix": None, "last_commit_subject": None}


def _infer_responsibilities(path: Path) -> List[str]:
    parts = path.parts
    responsibilities = []
    if any(part in {"agents", "agent"} for part in parts):
        responsibilities.append("agent")
    if any(part in {"core", "monitor", "performance", "memory", "tools"} for part in parts):
        responsibilities.append(parts[parts.index(next(p for p in parts if p in {"core", "monitor", "performance", "memory", "tools"}))])
    if path.name == "queen.py":
        responsibilities.append("orchestration")
    if path.name == "hive_dispatcher.py":
        responsibilities.append("dispatch")
    if path.name == "file_manager.py":
        responsibilities.append("file-tool")
    if path.name == "hive_status.py":
        responsibilities.append("telemetry")
    if path.name == "mcp_manager.py":
        responsibilities.append("mcp")
    return responsibilities


def _is_test_related_task(task: str) -> bool:
    lowered = task.lower()
    return any(term in lowered for term in {"test", "tests", "testing", "regression", "coverage", "pytest", "unittest"})


def _is_test_file(path: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")
    if "tests" in parts:
        return True
    if normalized.startswith("test_") or normalized.endswith("_test.py") or normalized.endswith(".test.py") or normalized.endswith("test.py"):
        return True
    return False


def _collect_python_details(path: Path, repo_root: Path) -> Dict[str, object]:
    source = path.read_text(encoding="utf-8", errors="ignore")
    tree = ast.parse(source, filename=str(path))

    functions: List[Dict[str, object]] = []
    classes: List[Dict[str, object]] = []
    imports: List[str] = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append({
                "name": node.name,
                "line_start": node.lineno,
                "line_end": node.end_lineno or node.lineno,
            })
        elif isinstance(node, ast.ClassDef):
            classes.append({
                "name": node.name,
                "line_start": node.lineno,
                "line_end": node.end_lineno or node.lineno,
            })

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    entry_points = [item["name"] for item in functions if item["name"] in {
        "ask_kitty",
        "worker_execute",
        "scout_execute",
        "analyst_execute",
        "soldier_execute",
        "get_hive_status",
        "execute_file_command",
    }]

    return {
        "kind": "package" if path.name == "__init__.py" else "module",
        "line_count": len(source.splitlines()),
        "functions": functions,
        "classes": classes,
        "imports": sorted(set(imports)),
        "entry_points": entry_points,
        "has_main_guard": any(isinstance(node, ast.If) and isinstance(node.test, ast.Compare) for node in tree.body),
    }


def build_repository_index(repo_root: Optional[Path] = None, output_path: Optional[Path] = None) -> Dict[str, object]:
    repo_root = _normalize_repo_root(repo_root)
    if output_path is None:
        output_path = repo_root / DEFAULT_OUTPUT_PATH
    else:
        output_path = Path(output_path).resolve()

    python_files = [p for p in repo_root.rglob("*.py") if not _is_excluded(p, repo_root)]
    python_files = sorted(p for p in python_files if p.is_file())

    records: List[Dict[str, object]] = []
    for path in python_files:
        rel_path = path.relative_to(repo_root).as_posix()
        details = _collect_python_details(path, repo_root)
        metadata = _read_git_metadata(path, repo_root)
        record = {
            "path": rel_path,
            "kind": details["kind"],
            "line_count": details["line_count"],
            "responsibilities": _infer_responsibilities(path),
            "imports": details["imports"],
            "entry_points": details["entry_points"],
            "functions": details["functions"],
            "classes": details["classes"],
            "has_main_guard": details["has_main_guard"],
            "last_changed_unix": metadata["last_changed_unix"],
            "last_commit_subject": metadata["last_commit_subject"],
        }
        records.append(record)

    index = {
        "version": 1,
        "generated_at": None,
        "repository": repo_root.name,
        "files": records,
        "facts": {
            "runtime_entrypoints": [record["path"] for record in records if record["path"] in {"queen.py", "mcp_server.py"}],
            "agent_modules": [record["path"] for record in records if "/agents/" in record["path"]],
            "core_modules": [record["path"] for record in records if record["path"].startswith("core/")],
            "tool_modules": [record["path"] for record in records if record["path"].startswith("tools/")],
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return index


def load_repository_index(index_path: Optional[Path] = None, repo_root: Optional[Path] = None) -> Dict[str, object]:
    repo_root = _normalize_repo_root(repo_root)
    if index_path is None:
        index_path = repo_root / DEFAULT_OUTPUT_PATH
    else:
        index_path = Path(index_path).resolve()

    if not index_path.exists():
        return build_repository_index(repo_root=repo_root, output_path=index_path)

    return json.loads(index_path.read_text(encoding="utf-8"))


class RepositoryContextManager:
    """Repository context manager for Phase 0 repository exploration."""

    def __init__(self, repo_root: Optional[Path] = None, index_path: Optional[Path] = None) -> None:
        self.repo_root = _normalize_repo_root(repo_root)
        self.index_path = Path(index_path).resolve() if index_path is not None else self.repo_root / DEFAULT_OUTPUT_PATH
        self.index: Dict[str, object] = {}

    def __enter__(self) -> "RepositoryContextManager":
        self.index = load_repository_index(index_path=self.index_path, repo_root=self.repo_root)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        return False

    def refresh(self) -> Dict[str, object]:
        self.index = build_repository_index(repo_root=self.repo_root, output_path=self.index_path)
        return self.index

    def select(self, task: str, agent: str = "queen", max_items: int = 5, include_adjacent: bool = False) -> Dict[str, object]:
        return select_context(
            task,
            agent=agent,
            repo_root=self.repo_root,
            index_path=self.index_path,
            max_items=max_items,
            include_adjacent=include_adjacent,
        )


def select_context(task: str, agent: str = "queen", repo_root: Optional[Path] = None, index_path: Optional[Path] = None, max_items: int = 5, include_adjacent: bool = False) -> Dict[str, object]:
    repo_root = _normalize_repo_root(repo_root)
    index = load_repository_index(index_path=index_path, repo_root=repo_root)
    records = index.get("files", [])
    include_tests = _is_test_related_task(task)
    if not include_tests:
        records = [record for record in records if not _is_test_file(record.get("path", ""))]

    task_terms = [term for term in re.split(r"[^a-z0-9]+", task.lower()) if term]
    stop_words = {"the", "a", "an", "and", "for", "with", "how", "what", "why", "to", "from", "of", "in", "on", "is", "are", "can", "should"}
    task_terms = [term for term in task_terms if term not in stop_words]

    ranked: List[Tuple[float, Dict[str, object]]] = []
    for record in records:
        text_blob = " ".join([
            record.get("path", ""),
            " ".join(record.get("responsibilities", [])),
            " ".join(record.get("imports", [])),
            " ".join([item["name"] for item in record.get("functions", [])]),
            " ".join([item["name"] for item in record.get("classes", [])]),
        ]).lower()
        score = 0.0
        for term in task_terms:
            if term in text_blob:
                score += 2.0
        for term in task_terms:
            if term in record.get("path", ""):
                score += 1.5
        if agent in record.get("path", ""):
            score += 1.0
        if agent == "worker" and ("tool" in text_blob or "file" in text_blob):
            score += 1.0
        if agent == "scout" and ("research" in text_blob or "monitor" in text_blob):
            score += 1.0
        ranked.append((score, record))

    ranked.sort(key=lambda item: item[0], reverse=True)
    selected_records = []
    for _, record in ranked[:max_items]:
        if not record.get("path"):
            continue
        line_count = int(record.get("line_count", 0))
        symbol_ranges = []
        for symbol in record.get("functions", []) + record.get("classes", []):
            symbol_ranges.append({
                "start": int(symbol["line_start"]),
                "end": int(symbol["line_end"]),
            })
        line_ranges = symbol_ranges[:1] or [{"start": 1, "end": min(120, line_count) if line_count else 1}]
        content_budget = min(700, max(180, line_count * 6))
        selected_records.append({
            "path": record["path"],
            "reason": "matched task keywords and subsystem relevance",
            "line_ranges": line_ranges,
            "content_budget": content_budget,
            "kind": record.get("kind"),
            "entry_points": record.get("entry_points", []),
            "responsibilities": record.get("responsibilities", []),
        })

    adjacent_files: List[Dict[str, object]] = []
    if include_adjacent:
        selected_paths = {item["path"] for item in selected_records}
        for record in records:
            if record.get("path") in selected_paths:
                continue
            path_text = record.get("path", "")
            if any(path in path_text for path in ["core/", "tools/", "monitor/", "agents/"]):
                if any(selected_path in path_text for selected_path in selected_paths):
                    continue
            if any(selected_path.split("/")[-1].replace(".py", "") in path_text for selected_path in selected_paths):
                adjacent_files.append({
                    "path": record["path"],
                    "reason": "adjacent subsystem context",
                    "line_ranges": [{"start": 1, "end": min(80, int(record.get("line_count", 0)))}],
                    "content_budget": 240,
                })

    return {
        "task": task,
        "agent": agent,
        "selected_files": selected_records,
        "adjacent_files": adjacent_files,
        "facts": index.get("facts", {}),
        "guidance": [],
    }


if __name__ == "__main__":
    build_repository_index()
