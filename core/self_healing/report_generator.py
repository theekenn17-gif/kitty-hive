from __future__ import annotations

from pathlib import Path
from typing import List

from core.self_healing.models import SelfHealingReport


class ReportGenerator:
    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root or "/root/KITTY_HIVE").resolve()
        self.output_dir = self.repo_root / "docs" / "self_healing"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, report: SelfHealingReport) -> Path:
        from datetime import datetime

        timestamp = datetime.utcnow().strftime("%Y%m%d")
        output_path = self.output_dir / f"SELF_HEAL_REPORT_{timestamp}.md"
        output_path.write_text(report.to_markdown(), encoding="utf-8")
        return output_path
