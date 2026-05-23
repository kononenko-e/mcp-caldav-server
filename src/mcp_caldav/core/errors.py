class McpCaldavError(Exception):
    """Base error for the project."""


class ConfigError(McpCaldavError):
    """Configuration is invalid."""


class AccountNotFoundError(McpCaldavError):
    """Requested account_id does not exist."""


class CalendarNotFoundError(McpCaldavError):
    """Requested calendar_id does not exist."""


class ProviderConnectionError(McpCaldavError):
    """Provider connection failed."""


class EventNotFoundError(McpCaldavError):
    """Requested event_uid does not exist."""


class ValidationError(McpCaldavError):
    """User input validation error."""
