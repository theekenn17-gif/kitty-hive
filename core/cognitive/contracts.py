from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class Evidence:
    service: str
    domain: str
    summary: str
    confidence: float = 0.0
    freshness: str = "unknown"
    impact: str = "medium"
    risk: str = "low"
    provenance: Optional[str] = None


@dataclass(slots=True)
class Recommendation:
    service: str
    summary: str
    priority: str = "medium"
    confidence: float = 0.0
    impact: str = "medium"
    risk: str = "low"
    provenance: Optional[str] = None


@dataclass(slots=True)
class ProviderStatus:
    provider: str
    available: bool = True
    version: str = "0.1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ContextQuery:
    task: str
    agent: str = "queen"
    scope: str = "general"
    token_budget: int = 4000
    required_services: Optional[List[str]] = None
    include_provenance: bool = True
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ContextResponse:
    summary: str
    evidence: List[Evidence] = field(default_factory=list)
    recommendations: List[Recommendation] = field(default_factory=list)
    confidence: float = 0.0
    freshness: str = "unknown"
    impact: str = "medium"
    risk: str = "low"
    sources: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseProvider(ABC):
    name: str = "provider"

    @abstractmethod
    def query(self, query: ContextQuery) -> ContextResponse:
        raise NotImplementedError

    @abstractmethod
    def status(self) -> ProviderStatus:
        raise NotImplementedError

    @abstractmethod
    def explain(self, subject: str) -> str:
        raise NotImplementedError
