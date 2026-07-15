from __future__ import annotations

from .composer import Composer
from .contracts import ContextQuery, ContextResponse
from .providers import Architect, Guardian, Historian, Librarian, Observer, Strategist
from .registry import ProviderRegistry
from .router import Router


class ChiefOfStaff:
    def __init__(self, registry: ProviderRegistry | None = None) -> None:
        self.registry = registry or ProviderRegistry()
        self.router = Router()
        self.composer = Composer()
        self._register_defaults()

    def _register_defaults(self) -> None:
        providers = [
            Librarian(),
            Historian(),
            Observer(),
            Strategist(),
            Guardian(),
            Architect(),
        ]
        self.registry.register_defaults(providers)

    def handle(self, query: ContextQuery) -> ContextResponse:
        providers = []
        for provider_name in self.router.route(query):
            provider = self.registry.get(provider_name)
            if provider is not None:
                providers.append(provider)

        responses = [provider.query(query) for provider in providers]
        return self.composer.merge(responses)

    def register_provider(self, provider: object) -> None:
        self.registry.register(provider)
