from __future__ import annotations

from typing import Dict, List, Optional

from .contracts import BaseProvider, ProviderStatus


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: Dict[str, BaseProvider] = {}

    def register(self, provider: BaseProvider) -> None:
        self._providers[provider.name.lower()] = provider

    def unregister(self, name: str) -> bool:
        key = name.lower()
        if key in self._providers:
            del self._providers[key]
            return True
        return False

    def get(self, name: str) -> Optional[BaseProvider]:
        return self._providers.get(name.lower())

    def list(self) -> List[BaseProvider]:
        return list(self._providers.values())

    def health(self) -> Dict[str, ProviderStatus]:
        return {
            provider.name.lower(): provider.status()
            for provider in self._providers.values()
        }

    def register_defaults(self, providers: List[BaseProvider]) -> None:
        for provider in providers:
            self.register(provider)
