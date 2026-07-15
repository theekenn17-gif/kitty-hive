from __future__ import annotations

from .chief_of_staff import ChiefOfStaff
from .contracts import ContextQuery, ContextResponse


class CognitiveOrchestrator:
    def __init__(self, chief_of_staff: ChiefOfStaff | None = None) -> None:
        self.chief_of_staff = chief_of_staff or ChiefOfStaff()

    def process(self, query: ContextQuery) -> ContextResponse:
        return self.chief_of_staff.handle(query)
