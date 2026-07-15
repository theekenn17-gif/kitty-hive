from __future__ import annotations

from pathlib import Path

from ..contracts import BaseProvider, ContextQuery, ContextResponse, Evidence, ProviderStatus


class Architect(BaseProvider):
    name = "architect"

    def query(self, query: ContextQuery) -> ContextResponse:
        guidance = "Preserve modular boundaries and avoid changing runtime entry points unless the task explicitly requires it."
        evidence = [
            Evidence(
                service=self.name,
                domain="design",
                summary=guidance,
                confidence=0.6,
                freshness="fresh",
                impact="medium",
                risk="medium",
                provenance="docs/structure_guide.md",
            )
        ]
        return ContextResponse(
            summary=f"Architect guidance for '{query.task}': {guidance}",
            evidence=evidence,
            recommendations=[],
            confidence=0.6,
            freshness="fresh",
            impact="medium",
            risk="medium",
            sources=[self.name],
            metadata={"provider": self.name, "mode": "design-guidance"},
        )

    def status(self) -> ProviderStatus:
        return ProviderStatus(provider=self.name, available=True, metadata={"capability": "design-intelligence"})

    def explain(self, subject: str) -> str:
        return f"Architect guidance for {subject} focuses on preserving boundaries and minimizing blast radius."
