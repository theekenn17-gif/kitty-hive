from __future__ import annotations

from typing import Iterable, List

from core.cognitive.contracts import ContextResponse


class ConfidenceEngine:
    def aggregate(self, responses: Iterable[ContextResponse]) -> float:
        response_list = list(responses)
        if not response_list:
            return 0.0
        return round(sum(item.confidence for item in response_list) / max(1, len(response_list)), 3)

    def adjust_for_budget(self, confidence: float, token_budget: int, used_tokens: int) -> float:
        if token_budget <= 0:
            return confidence
        saturation = min(1.0, used_tokens / max(1, token_budget))
        return round(max(0.0, confidence - saturation * 0.05), 3)

    def estimate_tokens(self, provider_count: int, budget: int) -> int:
        if budget <= 0:
            return provider_count * 250
        return min(budget, provider_count * 250)
