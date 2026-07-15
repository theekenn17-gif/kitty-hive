from __future__ import annotations

from typing import List

from .contracts import ContextQuery
from .policies import route_query


class Router:
    def route(self, query: ContextQuery) -> List[str]:
        return route_query(query)
