from __future__ import annotations

import logging

from pathlib import Path

import yaml  # type: ignore[import-untyped]
from dotenv import load_dotenv
from pydantic import ValidationError

from mcp_caldav.config.models import ServerConfig
from mcp_caldav.config.validate import resolve_passwords
from mcp_caldav.core.errors import ConfigError

logger = logging.getLogger(__name__)


def load_config(path: Path) -> ServerConfig:
    load_dotenv()
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"configuration file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML in configuration file: {path}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("configuration file must contain a top-level mapping")

    try:
        config = ServerConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(f"configuration validation failed: {exc}") from exc

    logger.info("Loaded config from '%s' with %d account(s)", path, len(config.accounts))
    return resolve_passwords(config)
