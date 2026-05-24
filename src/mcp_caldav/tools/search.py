from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_caldav.core.access import AccessController
from mcp_caldav.core.registry import AccountRegistry
from mcp_caldav.core.session import SessionManager
from mcp_caldav.schemas.tools import SearchEventsInput, SearchEventsResponse


def register_search_tools(
    server: FastMCP,
    registry: AccountRegistry,
    sessions: SessionManager,
    access: AccessController,
) -> None:
    @server.tool(
        name="caldav_search_events",
        description=(
            "Search event text fields inside one explicit calendar. "
            "Optional start/end narrow the time window; without them a +-1-year window around today is used."
        ),
    )
    def search_events(
        account_id: str,
        calendar_id: str,
        query: str,
        start: str | None = None,
        end: str | None = None,
    ) -> dict[str, object]:
        payload = SearchEventsInput(
            account_id=account_id,
            calendar_id=calendar_id,
            query=query,
            start=start,
            end=end,
        )
        registry.get_account(payload.account_id)
        access.ensure_calendar_access(payload.account_id, payload.calendar_id)
        provider = sessions.get_provider(payload.account_id)
        events = provider.search_events(
            calendar_id=payload.calendar_id,
            query=payload.query,
            start=payload.start,
            end=payload.end,
        )
        response = SearchEventsResponse(
            account_id=payload.account_id,
            calendar_id=payload.calendar_id,
            query=payload.query,
            events=events,
        )
        return response.model_dump(mode="json")
