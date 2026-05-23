from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_caldav.core.registry import AccountRegistry
from mcp_caldav.core.session import SessionManager
from mcp_caldav.schemas.tools import (
    CreateEventInput,
    CreateEventResponse,
    DeleteEventInput,
    DeleteEventResponse,
    GetTodayEventsInput,
    GetWeekEventsInput,
    ListEventsInput,
    ListEventsResponse,
    UpdateEventInput,
    UpdateEventResponse,
)
from mcp_caldav.utils.time import today_window, week_window


def register_event_tools(
    server: FastMCP,
    registry: AccountRegistry,
    sessions: SessionManager,
) -> None:
    @server.tool(
        name="caldav_list_events",
        description="List events for a calendar in an explicit time range.",
    )
    def list_events(account_id: str, calendar_id: str, start: str, end: str) -> dict[str, object]:
        payload = ListEventsInput(
            account_id=account_id,
            calendar_id=calendar_id,
            start=start,
            end=end,
        )
        registry.get_account(payload.account_id)
        provider = sessions.get_provider(payload.account_id)
        events = provider.list_events(payload.calendar_id, payload.start, payload.end)
        response = ListEventsResponse(
            account_id=payload.account_id,
            calendar_id=payload.calendar_id,
            events=events,
        )
        return response.model_dump(mode="json")

    @server.tool(
        name="caldav_get_today_events",
        description="List today's events for a calendar using the server local timezone.",
    )
    def get_today_events(account_id: str, calendar_id: str) -> dict[str, object]:
        payload = GetTodayEventsInput(account_id=account_id, calendar_id=calendar_id)
        start, end = today_window()
        registry.get_account(payload.account_id)
        provider = sessions.get_provider(payload.account_id)
        events = provider.list_events(payload.calendar_id, start, end)
        response = ListEventsResponse(
            account_id=payload.account_id,
            calendar_id=payload.calendar_id,
            events=events,
        )
        return response.model_dump(mode="json")

    @server.tool(
        name="caldav_get_week_events",
        description="List events for the next seven days using the server local timezone.",
    )
    def get_week_events(account_id: str, calendar_id: str) -> dict[str, object]:
        payload = GetWeekEventsInput(account_id=account_id, calendar_id=calendar_id)
        start, end = week_window()
        registry.get_account(payload.account_id)
        provider = sessions.get_provider(payload.account_id)
        events = provider.list_events(payload.calendar_id, start, end)
        response = ListEventsResponse(
            account_id=payload.account_id,
            calendar_id=payload.calendar_id,
            events=events,
        )
        return response.model_dump(mode="json")

    @server.tool(
        name="caldav_create_event",
        description="Create an event in a specific account_id and calendar_id.",
    )
    def create_event(**kwargs: object) -> dict[str, object]:
        payload = CreateEventInput.model_validate(kwargs)
        registry.get_account(payload.account_id)
        provider = sessions.get_provider(payload.account_id)
        event = provider.create_event(payload)
        response = CreateEventResponse(
            account_id=payload.account_id,
            calendar_id=payload.calendar_id,
            event=event,
        )
        return response.model_dump(mode="json")

    @server.tool(
        name="caldav_update_event",
        description="Update an existing event identified by account_id, calendar_id and event_uid.",
    )
    def update_event(**kwargs: object) -> dict[str, object]:
        payload = UpdateEventInput.model_validate(kwargs)
        registry.get_account(payload.account_id)
        provider = sessions.get_provider(payload.account_id)
        event = provider.update_event(payload)
        response = UpdateEventResponse(
            account_id=payload.account_id,
            calendar_id=payload.calendar_id,
            event_uid=payload.event_uid,
            event=event,
        )
        return response.model_dump(mode="json")

    @server.tool(
        name="caldav_delete_event",
        description="Delete an existing event identified by account_id, calendar_id and event_uid.",
    )
    def delete_event(account_id: str, calendar_id: str, event_uid: str) -> dict[str, object]:
        payload = DeleteEventInput(
            account_id=account_id,
            calendar_id=calendar_id,
            event_uid=event_uid,
        )
        registry.get_account(payload.account_id)
        provider = sessions.get_provider(payload.account_id)
        provider.delete_event(payload.calendar_id, payload.event_uid)
        response = DeleteEventResponse(
            account_id=payload.account_id,
            calendar_id=payload.calendar_id,
            event_uid=payload.event_uid,
            deleted=True,
        )
        return response.model_dump(mode="json")
