from __future__ import annotations

from mcp.server.auth.middleware.auth_context import get_access_token

from mcp_caldav.config.models import AccessConfig, AccessProfileConfig
from mcp_caldav.core.errors import AccountNotFoundError, CalendarNotFoundError
from mcp_caldav.schemas.common import AccountSummary, CalendarSummary


class AccessController:
    def __init__(self, access: AccessConfig | None) -> None:
        self._profiles_by_client_id: dict[str, AccessProfileConfig] = {}
        if access is None:
            return
        for profile in access.tokens.values():
            self._profiles_by_client_id[profile.client_id] = profile

    def has_http_auth(self) -> bool:
        return bool(self._profiles_by_client_id)

    def filter_accounts(self, accounts: list[AccountSummary]) -> list[AccountSummary]:
        profile = self._current_profile()
        if profile is None:
            return accounts
        return [
            account
            for account in accounts
            if self._is_account_allowed(profile, account.account_id)
        ]

    def filter_calendars(
        self,
        account_id: str,
        calendars: list[CalendarSummary],
    ) -> list[CalendarSummary]:
        profile = self._current_profile()
        if profile is None:
            return calendars
        self.ensure_account_access(account_id)
        return [
            calendar
            for calendar in calendars
            if self._is_calendar_allowed(profile, account_id, calendar.calendar_id)
        ]

    def ensure_account_access(self, account_id: str) -> None:
        profile = self._current_profile()
        if profile is None:
            return
        if not self._is_account_allowed(profile, account_id):
            raise AccountNotFoundError(
                f"account_id '{account_id}' is not visible for client '{profile.client_id}'"
            )

    def ensure_calendar_access(self, account_id: str, calendar_id: str) -> None:
        profile = self._current_profile()
        if profile is None:
            return
        self.ensure_account_access(account_id)
        if not self._is_calendar_allowed(profile, account_id, calendar_id):
            raise CalendarNotFoundError(
                f"calendar_id '{calendar_id}' is not visible in account '{account_id}' "
                f"for client '{profile.client_id}'"
            )

    def _current_profile(self) -> AccessProfileConfig | None:
        access_token = get_access_token()
        if access_token is None:
            return None
        return self._profiles_by_client_id.get(access_token.client_id)

    def _is_account_allowed(self, profile: AccessProfileConfig, account_id: str) -> bool:
        if profile.allowed_accounts is None and profile.allowed_calendars is None:
            return True
        if profile.allowed_accounts and account_id in profile.allowed_accounts:
            return True
        if profile.allowed_calendars and account_id in profile.allowed_calendars:
            return True
        return False

    def _is_calendar_allowed(
        self,
        profile: AccessProfileConfig,
        account_id: str,
        calendar_id: str,
    ) -> bool:
        if profile.allowed_calendars and account_id in profile.allowed_calendars:
            return calendar_id in profile.allowed_calendars[account_id]
        if profile.allowed_accounts and account_id in profile.allowed_accounts:
            return True
        if profile.allowed_accounts is None and profile.allowed_calendars is None:
            return True
        return False
