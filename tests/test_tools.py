from __future__ import annotations

from collections.abc import Callable

import pytest

from mcp_caldav.config.models import AccountConfig, CalendarConfig, ServerConfig
from mcp_caldav.core.errors import AccountNotFoundError, CalendarNotFoundError
from mcp_caldav.core.registry import AccountRegistry
from mcp_caldav.core.session import SessionManager
from mcp_caldav.providers.base import CalendarProvider
from mcp_caldav.schemas.common import CalendarSummary, EventRecord
from mcp_caldav.server import build_server


class FakeProvider(CalendarProvider):
    def list_calendars(self) -> list[CalendarSummary]:
        return [
            CalendarSummary(
                account_id="work",
                calendar_id="main",
                calendar_uid="work",
                name="Work",
                url="https://caldav.example.com/work/",
                is_default=True,
                index=0,
            )
        ]

    def get_calendar(self, calendar_id: str) -> CalendarSummary:
        if calendar_id != "main":
            raise CalendarNotFoundError("missing calendar")
        return self.list_calendars()[0]

    def list_events(self, calendar_id: str, start: str, end: str) -> list[EventRecord]:
        del start, end
        if calendar_id != "main":
            raise CalendarNotFoundError("missing calendar")
        return [
            EventRecord(
                account_id="work",
                calendar_id="main",
                calendar_name="Work",
                calendar_url="https://caldav.example.com/work/",
                event_uid="evt-1",
                summary="Standup",
                dtstart="2026-05-23T09:00:00+00:00",
                dtend="2026-05-23T09:30:00+00:00",
                location="Room A",
                description="Daily sync",
                categories=["team"],
                attendees=["alice@example.com"],
            )
        ]

    def create_event(self, payload):
        del payload
        return self.list_events("main", "", "")[0]

    def update_event(self, payload):
        del payload
        return self.list_events("main", "", "")[0]

    def delete_event(self, calendar_id: str, event_uid: str) -> None:
        if calendar_id != "main" or event_uid != "evt-1":
            raise CalendarNotFoundError("missing calendar")

    def search_events(
        self,
        calendar_id: str,
        query: str,
        start: str | None = None,
        end: str | None = None,
    ):
        del query, start, end
        return self.list_events(calendar_id, "", "")


@pytest.fixture
def server_tools() -> tuple[dict[str, Callable[..., dict[str, object]]], AccountRegistry]:
    registry = AccountRegistry(
        ServerConfig(
            accounts={
                "work": AccountConfig(
                    url="https://caldav.example.com/",
                    username="alice@example.com",
                    password="secret",
                    calendars=[CalendarConfig(calendar_id="main", name="Work")],
                )
            }
        )
    )
    sessions = SessionManager(registry=registry, factory=lambda account_id, account: FakeProvider())
    server = build_server(registry=registry, sessions=sessions)
    manager = server._tool_manager  # noqa: SLF001
    tools = {tool.name: tool.fn for tool in manager.list_tools()}
    return tools, registry


def test_list_accounts_tool(
    server_tools: tuple[dict[str, Callable[..., dict[str, object]]], AccountRegistry],
) -> None:
    tools, _ = server_tools
    result = tools["caldav_list_accounts"]()

    assert result["accounts"][0]["account_id"] == "work"


def test_list_calendars_tool(
    server_tools: tuple[dict[str, Callable[..., dict[str, object]]], AccountRegistry],
) -> None:
    tools, _ = server_tools
    result = tools["caldav_list_calendars"](account_id="work")

    assert result["calendars"][0]["calendar_id"] == "main"
    assert result["calendars"][0]["index"] == 0


def test_list_events_tool_shape(
    server_tools: tuple[dict[str, Callable[..., dict[str, object]]], AccountRegistry],
) -> None:
    tools, _ = server_tools
    result = tools["caldav_list_events"](
        account_id="work",
        calendar_id="main",
        start="2026-05-23T00:00:00+00:00",
        end="2026-05-24T00:00:00+00:00",
    )

    event = result["events"][0]
    assert event["account_id"] == "work"
    assert event["calendar_id"] == "main"
    assert event["event_uid"] == "evt-1"


def test_unknown_account_error(
    server_tools: tuple[dict[str, Callable[..., dict[str, object]]], AccountRegistry],
) -> None:
    tools, _ = server_tools

    with pytest.raises(AccountNotFoundError):
        tools["caldav_list_calendars"](account_id="missing")


def test_unknown_calendar_error(
    server_tools: tuple[dict[str, Callable[..., dict[str, object]]], AccountRegistry],
) -> None:
    tools, _ = server_tools

    with pytest.raises(CalendarNotFoundError):
        tools["caldav_get_calendar"](account_id="work", calendar_id="missing")
