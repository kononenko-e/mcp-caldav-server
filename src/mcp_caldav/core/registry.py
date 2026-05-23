from __future__ import annotations

from mcp_caldav.config.models import AccountConfig, ServerConfig
from mcp_caldav.core.errors import AccountNotFoundError
from mcp_caldav.schemas.common import AccountSummary


class AccountRegistry:
    def __init__(self, config: ServerConfig) -> None:
        self._config = config

    @property
    def config(self) -> ServerConfig:
        return self._config

    def list_accounts(self) -> list[AccountSummary]:
        accounts: list[AccountSummary] = []
        for account_id, account in self._config.accounts.items():
            accounts.append(
                AccountSummary(
                    account_id=account_id,
                    url=account.url,
                    username=account.username,
                    default_calendar_id=account.default_calendar_id,
                    configured_calendar_count=len(account.calendars or []),
                    auto_discover_calendars=account.auto_discover_calendars,
                )
            )
        return accounts

    def get_account(self, account_id: str) -> AccountConfig:
        try:
            return self._config.accounts[account_id]
        except KeyError as exc:
            raise AccountNotFoundError(f"account_id '{account_id}' was not found") from exc
