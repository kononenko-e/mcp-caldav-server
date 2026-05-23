from __future__ import annotations

from unittest.mock import patch

from mcp.server.auth.provider import AccessToken

from mcp_caldav.config.models import AccessConfig, AccessProfileConfig
from mcp_caldav.core.access import AccessController
from mcp_caldav.core.errors import AccountNotFoundError, CalendarNotFoundError
from mcp_caldav.schemas.common import AccountSummary, CalendarSummary


def test_access_controller_filters_accounts_and_calendars() -> None:
    controller = AccessController(
        AccessConfig(
            tokens={
                "hermes": AccessProfileConfig(
                    client_id="hermes",
                    token="secret",
                    allowed_calendars={"work": ["main"]},
                )
            }
        )
    )
    token = AccessToken(token="secret", client_id="hermes", scopes=["caldav"])

    with patch("mcp_caldav.core.access.get_access_token", return_value=token):
        accounts = controller.filter_accounts(
            [
                AccountSummary(
                    account_id="work",
                    url="https://caldav.example.com/",
                    username="alice@example.com",
                    configured_calendar_count=2,
                    auto_discover_calendars=True,
                ),
                AccountSummary(
                    account_id="personal",
                    url="https://caldav.icloud.com/",
                    username="alice@icloud.com",
                    configured_calendar_count=1,
                    auto_discover_calendars=True,
                ),
            ]
        )
        calendars = controller.filter_calendars(
            "work",
            [
                CalendarSummary(
                    account_id="work",
                    calendar_id="main",
                    calendar_uid="main",
                    name="Main",
                    url="https://caldav.example.com/work/main/",
                    index=0,
                ),
                CalendarSummary(
                    account_id="work",
                    calendar_id="meetings",
                    calendar_uid="meetings",
                    name="Meetings",
                    url="https://caldav.example.com/work/meetings/",
                    index=1,
                ),
            ],
        )

    assert [account.account_id for account in accounts] == ["work"]
    assert [calendar.calendar_id for calendar in calendars] == ["main"]


def test_access_controller_blocks_hidden_account_and_calendar() -> None:
    controller = AccessController(
        AccessConfig(
            tokens={
                "claude": AccessProfileConfig(
                    client_id="claude",
                    token="secret",
                    allowed_calendars={"work": ["main"]},
                )
            }
        )
    )
    token = AccessToken(token="secret", client_id="claude", scopes=["caldav"])

    with patch("mcp_caldav.core.access.get_access_token", return_value=token):
        try:
            controller.ensure_account_access("personal")
        except AccountNotFoundError:
            pass
        else:  # pragma: no cover
            raise AssertionError("expected AccountNotFoundError")

        try:
            controller.ensure_calendar_access("personal", "home")
        except AccountNotFoundError:
            pass
        else:  # pragma: no cover
            raise AssertionError("expected AccountNotFoundError")

        try:
            controller.ensure_calendar_access("work", "home")
        except CalendarNotFoundError:
            pass
        else:  # pragma: no cover
            raise AssertionError("expected CalendarNotFoundError")
