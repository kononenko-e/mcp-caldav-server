from __future__ import annotations

import pytest

from mcp_caldav.config.models import AccountConfig, CalendarConfig, ServerConfig
from mcp_caldav.core.errors import AccountNotFoundError
from mcp_caldav.core.registry import AccountRegistry


@pytest.fixture
def registry() -> AccountRegistry:
    config = ServerConfig(
        accounts={
            "work": AccountConfig(
                url="https://caldav.example.com/",
                username="alice@example.com",
                password="secret",
                calendars=[CalendarConfig(calendar_id="main", name="Main")],
            )
        }
    )
    return AccountRegistry(config)


def test_registry_lists_accounts(registry: AccountRegistry) -> None:
    accounts = registry.list_accounts()

    assert len(accounts) == 1
    assert accounts[0].account_id == "work"


def test_registry_raises_for_unknown_account(registry: AccountRegistry) -> None:
    with pytest.raises(AccountNotFoundError, match="missing"):
        registry.get_account("missing")
