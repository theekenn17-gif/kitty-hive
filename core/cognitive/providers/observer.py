from __future__ import annotations

from monitor.hive_status import get_hive_status

from ..contracts import BaseProvider, ContextQuery, ContextResponse, Evidence, ProviderStatus


class Observer(BaseProvider):
    name = "observer"

    def query(self, query: ContextQuery) -> ContextResponse:
        try:
            metrics = get_hive_status()
            summary = (
                f"Runtime status: queen={metrics.get('queen')} memory={metrics.get('memory')} ollama={metrics.get('ollama')}"
            )
            return ContextResponse(
                summary=f"Observer report for '{query.task}': {summary}",
                evidence=[
                    Evidence(
                        service=self.name,
                        domain="runtime",
                        summary=summary,
                        confidence=0.7,
                        freshness="live",
                        impact="medium",
                        risk="medium",
                        provenance="monitor/hive_status.py",
                    )
                ],
                recommendations=[],
                confidence=0.7,
                freshness="live",
                impact="medium",
                risk="medium",
                sources=[self.name],
                metadata={"runtime_metrics": metrics, "provider": self.name},
            )
        except Exception as exc:
            return ContextResponse(
                summary=f"Observer unavailable for '{query.task}': {exc}",
                evidence=[],
                recommendations=[],
                confidence=0.2,
                freshness="stale",
                impact="medium",
                risk="medium",
                sources=[self.name],
                metadata={"error": str(exc)},
            )

    def status(self) -> ProviderStatus:
        return ProviderStatus(provider=self.name, available=True, metadata={"capability": "runtime-intelligence"})

    def explain(self, subject: str) -> str:
        return f"Observer watches runtime health signals for {subject} and surfaces operational state."
