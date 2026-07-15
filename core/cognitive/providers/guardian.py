from __future__ import annotations

from ..contracts import BaseProvider, ContextQuery, ContextResponse, Evidence, ProviderStatus


class Guardian(BaseProvider):
    name = "guardian"

    def query(self, query: ContextQuery) -> ContextResponse:
        action = query.task
        risk = self.risk_level(action)
        requires_backup = self.requires_backup(action)
        approval = self.approve(action)
        summary = f"Guardian review: risk={risk} backup_required={requires_backup} approval={approval}."
        return ContextResponse(
            summary=f"Guardian guidance for '{query.task}': {summary}",
            evidence=[
                Evidence(
                    service=self.name,
                    domain="security",
                    summary=summary,
                    confidence=0.8,
                    freshness="fresh",
                    impact="high" if risk == "high" else "medium",
                    risk=risk,
                    provenance="core/cognitive/providers/guardian.py",
                )
            ],
            recommendations=[],
            confidence=0.8,
            freshness="fresh",
            impact="high" if risk == "high" else "medium",
            risk=risk,
            sources=[self.name],
            metadata={"approval_state": "approved" if approval else "rejected", "requires_backup": requires_backup},
        )

    def status(self) -> ProviderStatus:
        return ProviderStatus(provider=self.name, available=True, metadata={"capability": "validation-and-guardrails"})

    def explain(self, subject: str) -> str:
        return f"Guardian evaluates safety risks for {subject} and recommends backup and rollback steps when needed."

    def approve(self, action: str) -> bool:
        return self.risk_level(action) != "high"

    def reject(self, action: str) -> bool:
        return not self.approve(action)

    def requires_backup(self, action: str) -> bool:
        lowered = action.lower()
        if any(term in lowered for term in ["delete", "remove", "overwrite", "replace", "modify", "move", "write", "format", "rm "]):
            return True
        return self.risk_level(action) == "high"

    def risk_level(self, action: str) -> str:
        lowered = action.lower()
        if any(term in lowered for term in ["delete", "remove", "overwrite", "format", "drop", "rm ", "chmod"]):
            return "high"
        if any(term in lowered for term in ["modify", "move", "write", "replace"]):
            return "medium"
        return "low"
