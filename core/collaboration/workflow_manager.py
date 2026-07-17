from __future__ import annotations

from typing import List, Tuple

from core.cognitive.contracts import ContextQuery, ContextResponse
from .task_context import TaskContext


class WorkflowManager:
    def determine_mode(self, task_context: TaskContext) -> str:
        if task_context.query.scope == "runtime" or task_context.execution_mode == "parallel":
            return "parallel"
        if len(task_context.provider_names) > 1:
            return "parallel"
        return "sequential"

    def determine_provider_order(self, task_context: TaskContext, pipeline) -> List[str]:
        if task_context.provider_names:
            return list(task_context.provider_names)
        return pipeline.resolve(task_context.query)

    def estimate_time(self, provider_count: int, timeout_seconds: int) -> float:
        return round(max(0.1, provider_count * timeout_seconds / 2.0), 2)

    def estimate_cost(self, provider_count: int, token_budget: int) -> int:
        if token_budget <= 0:
            return provider_count * 250
        return min(token_budget, provider_count * 250)
