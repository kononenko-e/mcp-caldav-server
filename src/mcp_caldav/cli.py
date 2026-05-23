from __future__ import annotations

from pathlib import Path
from typing import Literal, cast

import click

from mcp_caldav.config.load import load_config
from mcp_caldav.core.access import AccessController
from mcp_caldav.core.registry import AccountRegistry
from mcp_caldav.core.session import SessionManager
from mcp_caldav.providers.caldav import CaldavProviderFactory
from mcp_caldav.server import build_server


@click.command()
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, exists=True, path_type=Path),
    required=True,
    help="Path to YAML configuration file.",
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "streamable-http"], case_sensitive=False),
    default="stdio",
    show_default=True,
    help="MCP transport.",
)
@click.option("--host", type=str, default=None, help="HTTP host override.")
@click.option("--port", type=int, default=None, help="HTTP port override.")
@click.option("--mount-path", type=str, default=None, help="HTTP mount path override.")
@click.option(
    "--streamable-http-path",
    type=str,
    default=None,
    help="HTTP MCP endpoint path override.",
)
@click.option(
    "--public-base-url",
    type=str,
    default=None,
    help="Public base URL used for HTTP auth metadata.",
)
@click.option(
    "--stateless-http/--stateful-http",
    default=None,
    help="Override streamable HTTP session mode.",
)
def main(
    config_path: Path,
    transport: str,
    host: str | None,
    port: int | None,
    mount_path: str | None,
    streamable_http_path: str | None,
    public_base_url: str | None,
    stateless_http: bool | None,
) -> None:
    """Run the MCP CalDAV server."""
    config = load_config(config_path)
    registry = AccountRegistry(config)
    sessions = SessionManager(
        registry=registry,
        factory=CaldavProviderFactory(config.provider),
    )
    access = AccessController(config.access)
    http_config = config.http
    server = build_server(
        registry=registry,
        sessions=sessions,
        access=access,
        host=host or http_config.host,
        port=port or http_config.port,
        mount_path=mount_path or http_config.mount_path,
        streamable_http_path=streamable_http_path or http_config.streamable_http_path,
        stateless_http=http_config.stateless_http if stateless_http is None else stateless_http,
        public_base_url=public_base_url or http_config.public_base_url,
    )
    selected_transport = cast(
        Literal["stdio", "sse", "streamable-http"],
        transport.lower(),
    )
    server.run(transport=selected_transport)


if __name__ == "__main__":
    main()
