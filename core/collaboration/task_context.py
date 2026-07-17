from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.cognitive.contracts import ContextQuery


@dataclass(slots=True)
class TaskContext:
    query: ContextQuery
    provider_names: List[str] = field(default_factory=list)
    execution_mode: str = "sequential"
    token_budget: int = 4000
    timeout_seconds: int = 10
    constraints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    required_services: Optional[List[str]] = None

    @classmethod
    def from_query(cls, query: ContextQuery) -> "TaskContext":
        return cls(
            query=query,
            provider_names=list(query.required_services or []),
            token_budget=query.token_budget,
            constraints=dict(query.constraints),
            required_services=list(query.required_services or []),
        )
