from __future__ import annotations

import os

from mcp_caldav.config.models import AccessConfig, AccessProfileConfig, AccountConfig, ServerConfig
from mcp_caldav.core.errors import ConfigError


def resolve_passwords(config: ServerConfig) -> ServerConfig:
    accounts: dict[str, AccountConfig] = {}
    for account_id, account in config.accounts.items():
        if account.password_env:
            secret = os.getenv(account.password_env)
            if not secret:
                raise ConfigError(
                    f"configuration error for account '{account_id}': "
                    f"environment variable '{account.password_env}' is empty or missing"
                )
            accounts[account_id] = account.model_copy(
                update={"password": secret, "password_env": None}
            )
        else:
            accounts[account_id] = account

    access = _resolve_access_tokens(config)
    _validate_access_references(accounts, access)

    return config.model_copy(update={"accounts": accounts, "access": access})


def _resolve_access_tokens(config: ServerConfig) -> AccessConfig | None:
    if config.access is None:
        return None

    profiles: dict[str, AccessProfileConfig] = {}
    for profile_id, profile in config.access.tokens.items():
        if profile.token_env:
            token = os.getenv(profile.token_env)
            if not token:
                raise ConfigError(
                    f"configuration error for access profile '{profile_id}': "
                    f"environment variable '{profile.token_env}' is empty or missing"
                )
            profiles[profile_id] = profile.model_copy(update={"token": token, "token_env": None})
        else:
            profiles[profile_id] = profile

    return config.access.model_copy(update={"tokens": profiles})


def _validate_access_references(
    accounts: dict[str, AccountConfig],
    access: AccessConfig | None,
) -> None:
    if access is None:
        return

    known_accounts = set(accounts)
    for profile_id, profile in access.tokens.items():
        for account_id in profile.allowed_accounts or []:
            if account_id not in known_accounts:
                raise ConfigError(
                    f"configuration error for access profile '{profile_id}': "
                    f"unknown account_id '{account_id}'"
                )

        for account_id, calendar_ids in (profile.allowed_calendars or {}).items():
            if account_id not in known_accounts:
                raise ConfigError(
                    f"configuration error for access profile '{profile_id}': "
                    f"unknown account_id '{account_id}' in allowed_calendars"
                )
            configured_calendars = accounts[account_id].calendars
            if configured_calendars is None:
                continue
            known_calendar_ids = {calendar.calendar_id for calendar in configured_calendars}
            for calendar_id in calendar_ids:
                if calendar_id not in known_calendar_ids:
                    raise ConfigError(
                        f"configuration error for access profile '{profile_id}': "
                        f"unknown calendar_id '{calendar_id}' for account '{account_id}'"
                    )
