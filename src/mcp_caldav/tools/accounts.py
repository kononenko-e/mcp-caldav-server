from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_caldav.core.registry import AccountRegistry
from mcp_caldav.schemas.tools import ListAccountsResponse


def register_account_tools(server: FastMCP, registry: AccountRegistry) -> None:
    @server.tool(
        name="caldav_list_accounts",
        description="List configured CalDAV accounts without establishing network connections.",
    )
    def list_accounts() -> dict[str, object]:
        response = ListAccountsResponse(accounts=registry.list_accounts())
        return response.model_dump(mode="json")
