from __future__ import annotations

from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP
from pydantic import AnyHttpUrl, TypeAdapter
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from mcp_caldav.core.access import AccessController
from mcp_caldav.core.auth import StaticTokenVerifier
from mcp_caldav.core.registry import AccountRegistry
from mcp_caldav.core.session import SessionManager
from mcp_caldav.tools.accounts import register_account_tools
from mcp_caldav.tools.calendars import register_calendar_tools
from mcp_caldav.tools.events import register_event_tools
from mcp_caldav.tools.search import register_search_tools


def build_server(
    registry: AccountRegistry,
    sessions: SessionManager,
    access: AccessController,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    mount_path: str = "/",
    streamable_http_path: str = "/mcp",
    stateless_http: bool = False,
    public_base_url: str | None = None,
) -> FastMCP:
    token_verifier = None
    auth_settings = None
    if access.has_http_auth():
        base_url = public_base_url or f"http://{host}:{port}"
        validated_base_url = TypeAdapter(AnyHttpUrl).validate_python(base_url)
        token_verifier = StaticTokenVerifier(registry.config.access)  # type: ignore[arg-type]
        auth_settings = AuthSettings(
            issuer_url=validated_base_url,
            resource_server_url=validated_base_url,
            required_scopes=[],
        )

    server = FastMCP(
        "mcp-caldav-server",
        host=host,
        port=port,
        mount_path=mount_path,
        streamable_http_path=streamable_http_path,
        stateless_http=stateless_http,
        auth=auth_settings,
        token_verifier=token_verifier,
    )
    register_account_tools(server, registry, access)
    register_calendar_tools(server, registry, sessions, access)
    register_event_tools(server, registry, sessions, access)
    register_search_tools(server, registry, sessions, access)

    @server.custom_route("/health", methods=["GET"])  # type: ignore[untyped-decorator]
    async def health(_: Request) -> Response:
        return JSONResponse({"status": "ok", "server": "mcp-caldav-server"})

    return server
