from __future__ import annotations

from typing import List

from core.self_healing.models import SelfHealingIssue


class RepairPlanner:
    def build_plan(self, issues: List[SelfHealingIssue]) -> List[SelfHealingIssue]:
        return issues
