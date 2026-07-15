from __future__ import annotations

from typing import Iterable

from .contracts import ContextResponse, Evidence, Recommendation


class Composer:
    def merge(self, responses: Iterable[ContextResponse]) -> ContextResponse:
        response_list = list(responses)
        if not response_list:
            return ContextResponse(summary="No intelligence responses were produced.")

        merged_evidence: list[Evidence] = []
        seen_evidence: set[tuple[str, str, str]] = set()
        for response in response_list:
            for evidence in response.evidence:
                key = (evidence.service, evidence.domain, evidence.summary)
                if key in seen_evidence:
                    continue
                seen_evidence.add(key)
                merged_evidence.append(evidence)

        merged_recommendations: list[Recommendation] = []
        seen_recommendations: set[tuple[str, str]] = set()
        for response in response_list:
            for recommendation in response.recommendations:
                key = (recommendation.service, recommendation.summary)
                if key in seen_recommendations:
                    continue
                seen_recommendations.add(key)
                merged_recommendations.append(recommendation)

        confidence = round(sum(item.confidence for item in response_list) / max(1, len(response_list)), 3)
        freshness = self._select_freshness(response_list)
        impact = self._select_severity(response_list, field="impact")
        risk = self._select_severity(response_list, field="risk")

        summary_parts = [response.summary for response in response_list if response.summary]
        summary = " | ".join(summary_parts) if summary_parts else "Merged intelligence context."

        return ContextResponse(
            summary=summary,
            evidence=merged_evidence,
            recommendations=merged_recommendations,
            confidence=confidence,
            freshness=freshness,
            impact=impact,
            risk=risk,
            sources=sorted({source for response in response_list for source in response.sources}),
            metadata={
                "merged_from": len(response_list),
                "evidence_count": len(merged_evidence),
                "recommendation_count": len(merged_recommendations),
            },
        )

    def _select_freshness(self, responses: list[ContextResponse]) -> str:
        freshness_values = {response.freshness for response in responses}
        if "live" in freshness_values:
            return "live"
        if "fresh" in freshness_values:
            return "fresh"
        if "stale" in freshness_values:
            return "stale"
        return "unknown"

    def _select_severity(self, responses: list[ContextResponse], field: str) -> str:
        severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1, "unknown": 0}
        highest = "unknown"
        highest_score = -1
        for response in responses:
            value = getattr(response, field, "unknown")
            score = severity_rank.get(value, 0)
            if score > highest_score:
                highest_score = score
                highest = value
        return highest
