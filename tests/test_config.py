from __future__ import annotations

from pathlib import Path

import pytest

from mcp_caldav.config.load import load_config
from mcp_caldav.core.errors import ConfigError


def test_load_config_with_two_accounts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "caldav.yaml"
    config_path.write_text(
        """
accounts:
  work:
    url: https://caldav.example.com/
    username: alice@example.com
    password_env: WORK_PASS
    calendars:
      - calendar_id: main
        name: Work
  personal:
    url: https://caldav.icloud.com/
    username: alice@icloud.com
    password: app-password
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("WORK_PASS", "secret")

    config = load_config(config_path)

    assert set(config.accounts) == {"work", "personal"}
    assert config.accounts["work"].password == "secret"
    assert config.accounts["work"].password_env is None


def test_load_config_raises_for_missing_password_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "caldav.yaml"
    config_path.write_text(
        """
accounts:
  work:
    url: https://caldav.example.com/
    username: alice@example.com
    password_env: WORK_PASS
""",
        encoding="utf-8",
    )
    monkeypatch.delenv("WORK_PASS", raising=False)

    with pytest.raises(ConfigError, match="WORK_PASS"):
        load_config(config_path)
