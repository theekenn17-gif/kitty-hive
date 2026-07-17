import tempfile
from pathlib import Path

from core.self_healing import SelfHealingScanner


def test_self_healing_scanner_detects_import_and_security_issues():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "core").mkdir(parents=True, exist_ok=True)
        (root / "core" / "alpha.py").write_text(
            "import missing_package\n"
            "from core.alpha import helper\n\n"
            "def compute():\n"
            "    return 1\n",
            encoding="utf-8",
        )
        (root / "core" / "beta.py").write_text(
            "def compute():\n"
            "    return 1\n\n"
            "import subprocess\n"
            "subprocess.run('echo hi', shell=True)\n",
            encoding="utf-8",
        )

        scanner = SelfHealingScanner(repo_root=root)
        report = scanner.scan_repository()

        assert report.health.overall_score <= 100
        assert any(issue.category == "import" for issue in report.issues)
        assert any(issue.category == "security" for issue in report.issues)
        assert any(issue.category == "duplicate" for issue in report.issues)


def test_self_healing_report_generator_writes_markdown_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "core").mkdir(parents=True, exist_ok=True)
        (root / "core" / "alpha.py").write_text(
            "def helper():\n"
            "    return True\n",
            encoding="utf-8",
        )

        scanner = SelfHealingScanner(repo_root=root)
        report = scanner.scan_repository()
        output_path = scanner.generate_report(report)

        assert output_path.exists()
        assert output_path.suffix == ".md"
        assert "SELF HEAL REPORT" in output_path.read_text(encoding="utf-8").upper()


def test_continuous_monitoring_detects_regressions_and_tracks_history():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "core").mkdir(parents=True, exist_ok=True)
        (root / "core" / "safe.py").write_text(
            "def helper():\n"
            "    return True\n",
            encoding="utf-8",
        )

        scanner = SelfHealingScanner(repo_root=root)
        first_report = scanner.scan_repository()
        first_monitoring = scanner.monitor_repository(first_report)

        assert first_monitoring["subsystem_scores"]["dependencies"] <= 100
        assert first_monitoring["history"]["previous_score"] is None

        (root / "core" / "risky.py").write_text(
            "import subprocess\n"
            "subprocess.run('echo hi', shell=True)\n",
            encoding="utf-8",
        )

        second_report = scanner.scan_repository()
        second_monitoring = scanner.monitor_repository(second_report, previous_report=first_report)

        assert second_monitoring["history"]["previous_score"] == first_report.health.overall_score
        assert second_monitoring["history"]["current_score"] == second_report.health.overall_score
        assert second_monitoring["history"]["score_delta"] < 0
        assert second_monitoring["regressions"]
