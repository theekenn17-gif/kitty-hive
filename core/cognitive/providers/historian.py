from __future__ import annotations

from pathlib import Path

from ..contracts import BaseProvider, ContextQuery, ContextResponse, Evidence, ProviderStatus


class Historian(BaseProvider):
    name = "historian"

    def query(self, query: ContextQuery) -> ContextResponse:
        lessons = []
        try:
            import chromadb

            client = chromadb.PersistentClient(path=str(Path("/root/KITTY_HIVE/memory/database")))
            collection = client.get_or_create_collection(name="kitty_long_term_memory")
            results = collection.query(query_texts=[query.task], n_results=3)
            documents = results.get("documents", [])
            if documents and isinstance(documents, list) and documents[0]:
                lessons = [str(item) for item in documents[0] if str(item).strip()]
        except Exception:
            lessons = []

        summary = "Historical memory is available for prior fixes and lessons when the memory store is reachable."
        if lessons:
            summary = f"Historical memory suggests: {' | '.join(lessons[:2])}"

        return ContextResponse(
            summary=f"Historian guidance for '{query.task}': {summary}",
            evidence=[
                Evidence(
                    service=self.name,
                    domain="memory",
                    summary=summary,
                    confidence=0.55,
                    freshness="fresh",
                    impact="medium",
                    risk="low",
                    provenance="memory/database",
                )
            ],
            recommendations=[],
            confidence=0.55,
            freshness="fresh",
            impact="medium",
            risk="low",
            sources=[self.name],
            metadata={"lessons": lessons, "provider": self.name},
        )

    def status(self) -> ProviderStatus:
        return ProviderStatus(provider=self.name, available=True, metadata={"capability": "experience-intelligence"})

    def explain(self, subject: str) -> str:
        return f"Historian surfaces previous fixes and lessons learned for {subject}."
