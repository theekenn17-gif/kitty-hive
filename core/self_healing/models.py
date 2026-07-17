from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class SelfHealingIssue:
    category: str
    title: str
    description: str
    severity: str
    confidence: float
    affected_files: List[str] = field(default_factory=list)
    suggested_repair: str = ""
    estimated_impact: str = "medium"
    estimated_difficulty: str = "medium"
    line_hint: Optional[int] = None


@dataclass
class RepositoryHealth:
    overall_score: int
    architecture: int
    security: int
    performance: int
    maintainability: int
    dependencies: int
    documentation: int
    testing: int
    memory_health: int


@dataclass
class SelfHealingReport:
    repo_root: Path
    generated_at: str
    health: RepositoryHealth
    issues: List[SelfHealingIssue]

    def to_markdown(self) -> str:
        lines = [
            "# SELF HEAL REPORT",
            "",
            f"- Repository: {self.repo_root}",
            f"- Generated: {self.generated_at}",
            f"- Overall Score: {self.health.overall_score}/100",
            "",
            "## Health Summary",
            "",
            f"- Architecture: {self.health.architecture}/100",
            f"- Security: {self.health.security}/100",
            f"- Performance: {self.health.performance}/100",
            f"- Maintainability: {self.health.maintainability}/100",
            f"- Dependencies: {self.health.dependencies}/100",
            f"- Documentation: {self.health.documentation}/100",
            f"- Testing: {self.health.testing}/100",
            f"- Memory Health: {self.health.memory_health}/100",
            "",
            "## Findings",
            "",
        ]
        if not self.issues:
            lines.append("No issues detected.")
        else:
            for idx, issue in enumerate(self.issues, 1):
                lines.extend([
                    f"{idx}. **{issue.title}**",
                    f"   - Category: {issue.category}",
                    f"   - Severity: {issue.severity}",
                    f"   - Confidence: {issue.confidence:.2f}",
                    f"   - Files: {', '.join(issue.affected_files) if issue.affected_files else 'n/a'}",
                    f"   - Suggested Repair: {issue.suggested_repair or 'n/a'}",
                    f"   - Impact: {issue.estimated_impact}",
                    f"   - Difficulty: {issue.estimated_difficulty}",
                    "",
                ])
        return "\n".join(lines)
