from __future__ import annotations

import os

from mcp_caldav.config.models import AccountConfig, ServerConfig
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
    return config.model_copy(update={"accounts": accounts})
