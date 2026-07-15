from __future__ import annotations

from pathlib import Path

from ..contracts import BaseProvider, ContextQuery, ContextResponse, Evidence, ProviderStatus


class Strategist(BaseProvider):
    name = "strategist"

    def query(self, query: ContextQuery) -> ContextResponse:
        roadmap = ""
        for candidate in [Path("/root/KITTY_HIVE/strategic_breakdown.md"), Path("/root/KITTY_HIVE/knowledge/hive_plan.txt")]:
            if candidate.exists():
                roadmap = candidate.read_text(encoding="utf-8", errors="ignore")[:1200]
                break

        next_task = "Continue modular integration of the cognitive layer and preserve current runtime behavior."
        if "Phase 1" in roadmap or "Phase 2" in roadmap:
            next_task = "Advance the next modular subsystem while keeping the current agent loop stable."

        return ContextResponse(
            summary=f"Strategist guidance for '{query.task}': {next_task}",
            evidence=[
                Evidence(
                    service=self.name,
                    domain="strategy",
                    summary=next_task,
                    confidence=0.62,
                    freshness="fresh",
                    impact="medium",
                    risk="medium",
                    provenance="strategic_breakdown.md",
                )
            ],
            recommendations=[],
            confidence=0.62,
            freshness="fresh",
            impact="medium",
            risk="medium",
            sources=[self.name],
            metadata={
                "provider": self.name,
                "priority": "medium",
                "estimated_roi": "pending",
                "estimated_time": "pending",
                "mission_alignment": "high",
            },
        )

    def status(self) -> ProviderStatus:
        return ProviderStatus(provider=self.name, available=True, metadata={"capability": "strategic-planning"})

    def explain(self, subject: str) -> str:
        return f"Strategist frames the next best action for {subject} using roadmap priorities and current phase context."
