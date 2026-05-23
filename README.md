# MCP CalDAV Server

MCP server for multi-account CalDAV access with explicit `account_id` and `calendar_id`.

## Features

- One server, many accounts in one YAML config.
- Lazy CalDAV connection per account.
- Cached provider sessions with explicit reconnect support.
- Stable calendar selection by `calendar_id`.
- Predictable JSON responses for LLM agents.
- Clear separation between config, core, provider and MCP tool layers.

## Requirements

- Python 3.11+
- `uv`

## Install

```bash
uv sync
```

## Configuration

Create a YAML file, for example `config/caldav.yaml`:

```yaml
accounts:
  work:
    url: https://caldav.example.com/
    username: alice@example.com
    password_env: WORK_CALDAV_PASSWORD
    calendars:
      - calendar_id: main
        name: Work
      - calendar_id: meetings
        name: Meetings

  personal:
    url: https://caldav.icloud.com/
    username: alice@icloud.com
    password_env: PERSONAL_CALDAV_PASSWORD
    default_calendar_id: home
```

Configuration rules:

- `account_id` is the map key under `accounts`.
- Password can be provided either as `password` or `password_env`.
- `password_env` must point to a non-empty environment variable.
- If `calendars` is omitted, calendars are auto-discovered lazily.
- `default_calendar_id` is optional and affects only response metadata.

## Run

```bash
uv run mcp-caldav-server --config config/caldav.yaml
```

Transport options:

```bash
uv run mcp-caldav-server --config config/caldav.yaml --transport stdio
uv run mcp-caldav-server --config config/caldav.yaml --transport sse
uv run mcp-caldav-server --config config/caldav.yaml --transport streamable-http
```

## Tools

- `caldav_list_accounts`
- `caldav_list_calendars`
- `caldav_get_calendar`
- `caldav_list_events`
- `caldav_get_today_events`
- `caldav_get_week_events`
- `caldav_create_event`
- `caldav_update_event`
- `caldav_delete_event`
- `caldav_search_events`

All event tools require explicit `account_id` and `calendar_id`.

## MCP client example

Example server config fragment:

```json
{
  "mcpServers": {
    "caldav": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-calendar (CalDAV)",
        "run",
        "mcp-caldav-server",
        "--config",
        "/absolute/path/to/config/caldav.yaml"
      ]
    }
  }
}
```

## Development

Run checks:

```bash
uv run ruff check .
uv run mypy
uv run pytest
```

## Architecture

```text
src/mcp_caldav/
  cli.py
  server.py
  config/
  core/
  providers/
  schemas/
  tools/
  utils/
```

Main flow:

1. CLI loads and validates YAML config.
2. Registry exposes account metadata without network calls.
3. Session manager creates provider instances lazily per `account_id`.
4. Tool handlers resolve account and calendar explicitly.
5. Provider performs CalDAV operations and returns normalized models.
