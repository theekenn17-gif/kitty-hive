from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from core.cognitive.contracts import Evidence, Recommendation


@dataclass(slots=True)
class DecisionBundle:
    executive_summary: str
    evidence: List[Evidence] = field(default_factory=list)
    recommendations: List[Recommendation] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    providers_consulted: List[str] = field(default_factory=list)
    estimated_token_cost: int = 0
    estimated_execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
