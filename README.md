# MCP CalDAV Server

MCP server for multi-account CalDAV access with explicit `account_id` and `calendar_id`.

## Features

- One server, many accounts in one YAML config.
- Lazy CalDAV connection per account.
- Cached provider sessions with explicit reconnect support.
- Stable calendar selection by `calendar_id`.
- Predictable JSON responses for LLM agents.
- Optional shared HTTP mode for multiple concurrent agents.
- Optional bearer-token access profiles to isolate visible accounts/calendars per agent.
- Runtime-safe CalDAV backend selection for environments where `niquests` and HTTP/3 are problematic.
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

### Calendar matching rules

When `calendars` is configured, each entry is matched against remote CalDAV calendars in this order:
1. By `url` (exact match after stripping trailing slash) — takes priority.
2. By `name` (exact string match).

If neither matches, the calendar entry is silently skipped.
Duplicate remote names across different servers may produce unexpected matches — use `url` for reliable identification.

Optional shared HTTP section:

```yaml
http:
  host: 127.0.0.1
  port: 8787
  streamable_http_path: /mcp
  stateless_http: false
  public_base_url: http://127.0.0.1:8787
```

Optional per-agent visibility rules for shared HTTP mode:

```yaml
access:
  tokens:
    hermes_main:
      client_id: hermes-main
      token_env: HERMES_MAIN_MCP_TOKEN
      allowed_accounts: [work]

    claude_personal:
      client_id: claude-personal
      token_env: CLAUDE_PERSONAL_MCP_TOKEN
      allowed_calendars:
        personal: [home]
```

Access semantics:

- If `access.tokens` is omitted, HTTP mode is open and every client sees all configured accounts.
- If `access.tokens` is present, HTTP requests must use `Authorization: Bearer <token>`.
- Each token is mapped to one `client_id`.
- `allowed_accounts` grants full access to those accounts.
- `allowed_calendars` grants access only to specific calendars in those accounts.
- If both `allowed_accounts` and `allowed_calendars` are omitted for a token, that token has full access.

Optional provider compatibility section:

```yaml
provider:
  http_backend: requests
  disable_http3: true
```

Provider compatibility rules:

- Default is `http_backend: requests`.
- This avoids the `niquests` runtime path by default.
- `http_backend: niquests` is still available if you explicitly need it.
- When `niquests` is used, `disable_http3: true` is applied by default to avoid HTTP/3 kernel issues.

## Run

```bash
uv run mcp-caldav-server --config config/caldav.yaml
```

Transport options:

```bash
uv run mcp-caldav-server --config config/caldav.yaml --transport stdio
uv run mcp-caldav-server --config config/caldav.yaml --transport sse
uv run mcp-caldav-server --config config/caldav.yaml --transport streamable-http
uv run mcp-caldav-server --config config/caldav.yaml --transport streamable-http --host 127.0.0.1 --port 8787
```

Shared HTTP checks:

```bash
curl http://127.0.0.1:8787/health
curl -H "Authorization: Bearer $HERMES_MAIN_MCP_TOKEN" http://127.0.0.1:8787/mcp
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

Shared HTTP example:

```json
{
  "mcpServers": {
    "caldav-shared": {
      "transport": "streamable-http",
      "url": "http://127.0.0.1:8787/mcp",
      "headers": {
        "Authorization": "Bearer ${HERMES_MAIN_MCP_TOKEN}"
      }
    }
  }
}
```

## Agent setup

`Codex`, `Claude`, `Hermes` and similar clients are easiest to support in two modes:

1. `stdio` mode:
   one agent process starts its own MCP server process.
2. `streamable-http` mode:
   many agents share one long-lived MCP server instance on the same machine.

Use `stdio` when:

- the client does not support MCP-over-HTTP;
- the client does not support custom bearer headers;
- you want strict process isolation.

Use shared HTTP when:

- several agent instances should reuse one MCP server;
- you want one connection pool and one config file;
- you want token-based visibility per agent.

For `Hermes`, this is the important part:

- if Hermes can connect to MCP via `streamable-http` and send `Authorization` headers, one shared server is enough;
- if Hermes only supports `command`-style MCP, run it in `stdio` mode instead.

For environments where Hermes reports `HTTP/3`, `urllib3-future`, `qh3`, or `niquests` issues, keep this:

```yaml
provider:
  http_backend: requests
  disable_http3: true
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
