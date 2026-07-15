from __future__ import annotations

from typing import List

from .contracts import ContextQuery


def route_query(query: ContextQuery) -> List[str]:
    lowered = query.task.lower()
    if any(term in lowered for term in ["bug", "error", "failure", "crash", "incident"]):
        return ["observer", "historian", "architect", "guardian"]
    if any(term in lowered for term in ["business", "roi", "market", "strategy", "revenue"]):
        return ["strategist", "historian", "librarian"]
    if any(term in lowered for term in ["code", "implement", "build", "feature", "refactor", "change"]):
        return ["librarian", "architect", "guardian"]
    if query.scope == "runtime":
        return ["observer", "guardian"]
    return ["librarian", "architect", "historian"]
