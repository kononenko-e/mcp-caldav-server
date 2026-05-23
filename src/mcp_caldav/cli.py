from __future__ import annotations

from pathlib import Path
from typing import Literal, cast

import click

from mcp_caldav.config.load import load_config
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
def main(config_path: Path, transport: str) -> None:
    """Run the MCP CalDAV server."""
    config = load_config(config_path)
    registry = AccountRegistry(config)
    sessions = SessionManager(registry=registry, factory=CaldavProviderFactory())
    server = build_server(registry=registry, sessions=sessions)
    selected_transport = cast(
        Literal["stdio", "sse", "streamable-http"],
        transport.lower(),
    )
    server.run(transport=selected_transport)


if __name__ == "__main__":
    main()
