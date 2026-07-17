from __future__ import annotations

from typing import Iterable, List

from core.cognitive.contracts import ContextResponse, Evidence, Recommendation


class EvidenceMerger:
    def merge(self, responses: Iterable[ContextResponse]) -> tuple[List[Evidence], List[Recommendation], str, str, str]:
        response_list = list(responses)
        if not response_list:
            return [], [], "No intelligence responses were produced.", "unknown", "unknown"

        merged_evidence: List[Evidence] = []
        seen_evidence: set[tuple[str, str, str]] = set()
        for response in response_list:
            for evidence in response.evidence:
                key = (evidence.service, evidence.domain, evidence.summary)
                if key in seen_evidence:
                    continue
                seen_evidence.add(key)
                merged_evidence.append(evidence)

        merged_recommendations: List[Recommendation] = []
        seen_recommendations: set[tuple[str, str]] = set()
        for response in response_list:
            for recommendation in response.recommendations:
                key = (recommendation.service, recommendation.summary)
                if key in seen_recommendations:
                    continue
                seen_recommendations.add(key)
                merged_recommendations.append(recommendation)

        freshness = self._select_freshness(response_list)
        impact = self._select_severity(response_list, field="impact")
        risk = self._select_severity(response_list, field="risk")
        return merged_evidence, merged_recommendations, freshness, impact, risk

    def _select_freshness(self, responses: List[ContextResponse]) -> str:
        freshness_values = {response.freshness for response in responses}
        if "live" in freshness_values:
            return "live"
        if "fresh" in freshness_values:
            return "fresh"
        if "stale" in freshness_values:
            return "stale"
        return "unknown"

    def _select_severity(self, responses: List[ContextResponse], field: str) -> str:
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
