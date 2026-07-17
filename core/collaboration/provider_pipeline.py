from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, List, Tuple

import time

from core.cognitive.contracts import ContextQuery, ContextResponse, ProviderStatus
from core.cognitive.providers import Architect, Guardian, Historian, Librarian, Observer, Strategist


class ProviderPipeline:
    def __init__(self, providers: Dict[str, object] | None = None) -> None:
        self.providers = providers or self._default_providers()

    def _default_providers(self) -> Dict[str, object]:
        return {
            "librarian": Librarian(),
            "historian": Historian(),
            "architect": Architect(),
            "observer": Observer(),
            "guardian": Guardian(),
            "strategist": Strategist(),
        }

    def resolve(self, query: ContextQuery) -> List[str]:
        services = list(query.required_services or [])
        if not services:
            service_order = ["librarian", "historian", "architect", "observer", "guardian"]
            if any(term in query.task.lower() for term in ["business", "roi", "market", "strategy", "revenue"]):
                service_order = ["strategist", "historian", "librarian"]
            elif any(term in query.task.lower() for term in ["bug", "error", "failure", "crash", "incident"]):
                service_order = ["observer", "historian", "architect", "guardian"]
            elif any(term in query.task.lower() for term in ["code", "implement", "build", "feature", "refactor", "change"]):
                service_order = ["librarian", "architect", "guardian"]
            return service_order
        return services

    def execute(self, query: ContextQuery, provider_names: List[str], execution_mode: str = "sequential", timeout_seconds: int = 10) -> List[Tuple[str, ContextResponse]]:
        if execution_mode == "parallel" and len(provider_names) > 1:
            return self._run_parallel(provider_names, query, timeout_seconds)

        results: List[Tuple[str, ContextResponse]] = []
        for provider_name in provider_names:
            provider = self.providers.get(provider_name.lower())
            if provider is None:
                continue
            try:
                response = provider.query(query)
                results.append((provider_name, response))
            except Exception:
                results.append((provider_name, self._build_fallback_response(provider_name, query)))
        return results

    def _run_parallel(self, provider_names: List[str], query: ContextQuery, timeout_seconds: int) -> List[Tuple[str, ContextResponse]]:
        results: List[Tuple[str, ContextResponse]] = []
        with ThreadPoolExecutor(max_workers=min(4, len(provider_names))) as executor:
            futures: Dict[str, object] = {}
            for provider_name in provider_names:
                provider = self.providers.get(provider_name.lower())
                if provider is None:
                    continue
                futures[provider_name] = executor.submit(self._call_provider, provider, query, timeout_seconds)
            for provider_name in provider_names:
                future = futures.get(provider_name)
                if future is None:
                    continue
                try:
                    results.append((provider_name, future.result()))
                except Exception:
                    results.append((provider_name, self._build_fallback_response(provider_name, query)))
        return results

    def _call_provider(self, provider: object, query: ContextQuery, timeout_seconds: int) -> ContextResponse:
        start = time.time()
        response = provider.query(query)
        elapsed = time.time() - start
        if elapsed > timeout_seconds:
            raise TimeoutError(f"Provider {getattr(provider, 'name', 'unknown')} exceeded timeout")
        return response

    def _build_fallback_response(self, provider_name: str, query: ContextQuery) -> ContextResponse:
        return ContextResponse(
            summary=f"Provider {provider_name} failed to respond for task '{query.task}'.",
            evidence=[],
            recommendations=[],
            confidence=0.0,
            sources=[provider_name],
            metadata={"failed": True},
        )

    def get_status(self) -> Dict[str, ProviderStatus]:
        status: Dict[str, ProviderStatus] = {}
        for name, provider in self.providers.items():
            status[name] = provider.status()
        return status
