import json
import tempfile
from pathlib import Path

from core.context_manager import RepositoryContextManager, build_repository_index, select_context


def _write_sample_repo(root: Path) -> None:
    (root / "core").mkdir(parents=True, exist_ok=True)
    (root / "tools").mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(parents=True, exist_ok=True)
    (root / "memory").mkdir(parents=True, exist_ok=True)
    (root / ".env").write_text("SECRET=1\n", encoding="utf-8")
    (root / "core" / "telemetry.py").write_text(
        "def get_status():\n    return {'ok': True}\n",
        encoding="utf-8",
    )
    (root / "tools" / "file_manager.py").write_text(
        "def write_file(path):\n    return path\n",
        encoding="utf-8",
    )
    (root / "logs" / "debug.log").write_text("ignore me\n", encoding="utf-8")
    (root / "memory" / "context").mkdir(parents=True, exist_ok=True)


def test_build_repository_index_excludes_sensitive_and_generated_paths():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        _write_sample_repo(root)
        index = build_repository_index(repo_root=root, output_path=root / "memory" / "context" / "repository_index.json")
        paths = [item["path"] for item in index["files"]]
        assert "core/telemetry.py" in paths
        assert "tools/file_manager.py" in paths
        assert ".env" not in paths
        assert "logs/debug.log" not in paths
        assert "memory/context/repository_index.json" not in paths


def test_select_context_returns_line_ranges_within_file_bounds():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        _write_sample_repo(root)
        context = select_context("telemetry status", agent="worker", repo_root=root, max_items=3)
        selected = context["selected_files"][0]
        assert selected["path"] == "core/telemetry.py"
        for line_range in selected["line_ranges"]:
            assert line_range["start"] >= 1
            assert line_range["end"] >= line_range["start"]
            assert line_range["end"] <= 20
            assert selected["content_budget"] > 0


def test_select_context_can_handle_two_known_tasks():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        _write_sample_repo(root)
        telemetry_context = select_context("telemetry status", agent="worker", repo_root=root, max_items=3)
        file_context = select_context("file manager write", agent="worker", repo_root=root, max_items=3)
        assert telemetry_context["selected_files"][0]["path"] == "core/telemetry.py"
        assert file_context["selected_files"][0]["path"] == "tools/file_manager.py"


def test_file_manager_write_prefers_tool_file_over_test_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        _write_sample_repo(root)
        tests_dir = root / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        (tests_dir / "test_file_manager.py").write_text(
            "def test_file_manager():\n    assert True\n",
            encoding="utf-8",
        )
        context = select_context("file manager write", agent="worker", repo_root=root, max_items=5)
        selected_paths = [item["path"] for item in context["selected_files"]]
        assert selected_paths[0] == "tools/file_manager.py"
        assert all("tests/" not in path for path in selected_paths)


def test_repository_context_manager_phase0_support():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        _write_sample_repo(root)
        index_output = root / "memory" / "context" / "repository_index.json"
        with RepositoryContextManager(repo_root=root, index_path=index_output) as manager:
            assert manager.index["repository"] == root.name
            selected = manager.select("telemetry status", agent="worker", max_items=3)
            assert selected["selected_files"][0]["path"] == "core/telemetry.py"
        refreshed = manager.refresh()
        assert refreshed["repository"] == root.name
