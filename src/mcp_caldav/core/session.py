from __future__ import annotations

from collections.abc import Callable

from mcp_caldav.config.models import AccountConfig
from mcp_caldav.core.registry import AccountRegistry
from mcp_caldav.providers.base import CalendarProvider

ProviderFactory = Callable[[str, AccountConfig], CalendarProvider]


class SessionManager:
    def __init__(self, registry: AccountRegistry, factory: ProviderFactory) -> None:
        self._registry = registry
        self._factory = factory
        self._providers: dict[str, CalendarProvider] = {}

    def get_provider(self, account_id: str) -> CalendarProvider:
        provider = self._providers.get(account_id)
        if provider is None:
            account = self._registry.get_account(account_id)
            provider = self._factory(account_id, account)
            self._providers[account_id] = provider
        return provider

    def reset_provider(self, account_id: str) -> CalendarProvider:
        account = self._registry.get_account(account_id)
        provider = self._factory(account_id, account)
        self._providers[account_id] = provider
        return provider
