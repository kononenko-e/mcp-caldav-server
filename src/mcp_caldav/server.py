from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_caldav.core.registry import AccountRegistry
from mcp_caldav.core.session import SessionManager
from mcp_caldav.tools.accounts import register_account_tools
from mcp_caldav.tools.calendars import register_calendar_tools
from mcp_caldav.tools.events import register_event_tools
from mcp_caldav.tools.search import register_search_tools


def build_server(registry: AccountRegistry, sessions: SessionManager) -> FastMCP:
    server = FastMCP("mcp-caldav-server")
    register_account_tools(server, registry)
    register_calendar_tools(server, registry, sessions)
    register_event_tools(server, registry, sessions)
    register_search_tools(server, registry, sessions)
    return server
