from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_caldav.core.registry import AccountRegistry
from mcp_caldav.core.session import SessionManager
from mcp_caldav.schemas.tools import (
    GetCalendarInput,
    GetCalendarResponse,
    ListCalendarsInput,
    ListCalendarsResponse,
)


def register_calendar_tools(
    server: FastMCP,
    registry: AccountRegistry,
    sessions: SessionManager,
) -> None:
    @server.tool(
        name="caldav_list_calendars",
        description="List calendars for a specific account_id.",
    )
    def list_calendars(account_id: str) -> dict[str, object]:
        payload = ListCalendarsInput(account_id=account_id)
        registry.get_account(payload.account_id)
        provider = sessions.get_provider(payload.account_id)
        calendars = provider.list_calendars()
        response = ListCalendarsResponse(account_id=payload.account_id, calendars=calendars)
        return response.model_dump(mode="json")

    @server.tool(
        name="caldav_get_calendar",
        description="Get metadata for a single calendar identified by account_id and calendar_id.",
    )
    def get_calendar(account_id: str, calendar_id: str) -> dict[str, object]:
        payload = GetCalendarInput(account_id=account_id, calendar_id=calendar_id)
        registry.get_account(payload.account_id)
        provider = sessions.get_provider(payload.account_id)
        calendar = provider.get_calendar(payload.calendar_id)
        response = GetCalendarResponse(account_id=payload.account_id, calendar=calendar)
        return response.model_dump(mode="json")
